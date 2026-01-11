import argparse
import asyncio
import json
import os
import platform
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# -----------------------------------------------------------------------------
# Windows 事件循环策略说明：
# - Windows 上 asyncio 默认是 ProactorEventLoop（Python 3.8+ 常见默认），
#   支持异步 subprocess 的 PIPE（stdio）通信。
# - 你之前尝试的 WindowsSelectorEventLoopPolicy 在 Windows 下对
#   create_subprocess_exec + PIPE 组合不支持，容易 NotImplementedError。
# - 所以这里明确指定 Proactor，确保能通过 stdio 和 jdtls 做 LSP 通信。
# -----------------------------------------------------------------------------
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# -------------------------
# JSON-RPC / LSP transport (stdio)
# -------------------------
# LSP 基于 JSON-RPC 2.0，并通过如下 framing 传输：
#   Content-Length: <N>\r\n
#   \r\n
#   <N 字节的 JSON body>
#
# 也就是说消息没有分隔符，完全依赖 Content-Length 来切分。
# 这也是下面 _encode_msg / _read_headers / _read_msg 的意义。


def _encode_msg(payload: Dict[str, Any]) -> bytes:
    """
    将 JSON-RPC 消息编码为 LSP 的 stdio 帧格式（带 Content-Length 头）。
    """
    # JSON body（必须是 UTF-8）
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    # LSP framing header
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


async def _read_headers(reader: asyncio.StreamReader) -> Dict[str, str]:
    """
    读取 LSP 消息 header 区域，直到遇到空行（\\r\\n\\r\\n）。
    返回小写 header dict，如 {"content-length": "123"}。
    """
    headers: Dict[str, str] = {}
    while True:
        line = await reader.readline()
        if not line:
            # jdtls 进程退出/管道关闭时会走到这里
            raise EOFError("LSP stream closed while reading headers")

        # header 是 ASCII，遇到异常字符做 replace
        line = line.decode("ascii", errors="replace").strip()

        # 空行代表 header 结束
        if line == "":
            break

        # 标准 header 格式：Key: Value
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    return headers


async def _read_msg(reader: asyncio.StreamReader) -> Dict[str, Any]:
    """
    读取一条完整的 LSP 消息（header + body），并解析 JSON body。
    """
    headers = await _read_headers(reader)
    if "content-length" not in headers:
        raise RuntimeError(f"Missing Content-Length header: {headers}")

    length = int(headers["content-length"])
    body = await reader.readexactly(length)

    # LSP body 是 UTF-8 JSON
    return json.loads(body.decode("utf-8", errors="replace"))


# -------------------------
# Request/Response 管理
# -------------------------
# LSP 的 request/response 是异步的：
# - 客户端发 request（带 id）
# - 服务端异步返回 response（同一个 id）
# - 中间可能穿插很多 notification（无 id）
#
# 所以我们需要一个 pending 字典：id -> Future，
# 当 response 回来时 set_result / set_exception 唤醒 send_request。


@dataclass
class PendingRequest:
    """
    保存一次 request 的 Future，用于在 response 到达时完成它。
    """
    fut: asyncio.Future


class LspClient:
    """
    一个极简 LSP Client：
    - 通过子进程 stdio 与 jdtls 通信
    - 支持 send_request / send_notification
    - 一个后台任务 _dispatch_loop 负责持续读取 server 消息并分发：
        * response：唤醒对应的 Future
        * notification：处理 diagnostics 等
    """

    def __init__(self, proc: asyncio.subprocess.Process):
        self.proc = proc

        # create_subprocess_exec(..., stdout=PIPE, stdin=PIPE) 返回的
        # stdout/stdin 是 StreamReader/StreamWriter
        self.reader = proc.stdout  # type: ignore
        self.writer = proc.stdin   # type: ignore

        # JSON-RPC request id 自增
        self._id = 0

        # id -> PendingRequest(future)
        self._pending: Dict[int, PendingRequest] = {}

        # 这里保存 diagnostics（server 推送通知 textDocument/publishDiagnostics）
        # key: 文档 uri
        # value: publishDiagnostics 的 params（含 diagnostics 列表）
        self._diagnostics: Dict[str, Any] = {}

        # 保存后台 dispatch task，便于退出时 cancel，避免 Windows 上退出噪音
        self._dispatch_task = None

    def _next_id(self) -> int:
        """生成下一个 JSON-RPC request id。"""
        self._id += 1
        return self._id

    async def send_notification(self, method: str, params: Any) -> None:
        """
        发送 LSP notification（无 id，无需等待返回）。
        常用于：initialized、didOpen、didChange、exit 等。
        """
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        self.writer.write(_encode_msg(msg))
        await self.writer.drain()

    async def start(self) -> None:
        """
        启动后台读循环：
        - 持续读取 jdtls 输出的消息
        - 分发 response/notification
        """
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def send_request(self, method: str, params: Any) -> Any:
        """
        发送 LSP request（有 id，必须等待 response）。
        返回 response.result（若 response.error 则抛异常）。
        """
        rid = self._next_id()
        msg = {"jsonrpc": "2.0", "id": rid, "method": method, "params": params}

        # 为这次 request 创建 Future，等待 _dispatch_loop 收到同 id 的 response
        fut = asyncio.get_event_loop().create_future()
        self._pending[rid] = PendingRequest(fut=fut)

        self.writer.write(_encode_msg(msg))
        await self.writer.drain()

        # 等待 response
        return await fut

    async def _dispatch_loop(self) -> None:
        """
        后台消息分发循环：
        - response：含 id & (result/error)
        - notification：含 method（一般无 id）
        """
        while True:
            msg = await _read_msg(self.reader)

            # -------------------------
            # 1) response（有 id）
            # -------------------------
            # response 结构：
            #   {"jsonrpc":"2.0","id":1,"result":...}
            # 或 {"jsonrpc":"2.0","id":1,"error":...}
            if "id" in msg and ("result" in msg or "error" in msg):
                rid = msg["id"]
                pending = self._pending.pop(rid, None)
                if pending:
                    if "error" in msg:
                        pending.fut.set_exception(RuntimeError(msg["error"]))
                    else:
                        pending.fut.set_result(msg["result"])
                continue

            # -------------------------
            # 2) notification（无 id）
            # -------------------------
            method = msg.get("method")

            # jdtls 会通过 publishDiagnostics 主动推送语法/语义诊断结果
            if method == "textDocument/publishDiagnostics":
                params = msg.get("params", {})
                uri = params.get("uri")
                if uri:
                    self._diagnostics[uri] = params

            # 你可以在这里扩展更多通知处理：
            # - window/logMessage      (打印 jdtls 日志)
            # - window/showMessage     (弹窗/提示)
            # - $/progress             (导入/构建进度)
            # - telemetry/event
            # 等等


# -------------------------
# helpers
# -------------------------

def path_to_file_uri(p: Path) -> str:
    """
    Path -> file:// URI
    LSP 通常使用 URI 传文件路径（而不是本地路径字符串）。
    Path.as_uri 会自动处理 Windows 盘符为 file:///E:/xxx 的形式。
    """
    return p.resolve().as_uri()


def guess_jdtls_config_dir(jdtls_home: Path) -> Path:
    """
    根据 OS 选择 jdtls 的 configuration 目录：
    - Windows: config_win
    - macOS:   config_mac
    - Linux:   config_linux
    """
    sysname = platform.system().lower()
    if "windows" in sysname:
        return jdtls_home / "config_win"
    if "darwin" in sysname or "mac" in sysname:
        return jdtls_home / "config_mac"
    return jdtls_home / "config_linux"


def find_launcher_jar(jdtls_home: Path) -> Path:
    """
    jdtls 是一个基于 Eclipse OSGi 的应用，它通过 equinox launcher 启动。
    launcher jar 通常位于：<jdtls_home>/plugins/org.eclipse.equinox.launcher_*.jar
    """
    plugins = jdtls_home / "plugins"
    jars = sorted(plugins.glob("org.eclipse.equinox.launcher_*.jar"))
    if not jars:
        raise FileNotFoundError(f"Cannot find org.eclipse.equinox.launcher_*.jar in: {plugins}")
    # 选择版本号最大的那个（排序后最后一个）
    return jars[-1]


def find_position(text: str, needle: str, prefer_after: bool = False) -> Tuple[int, int]:
    """
    在 text 中查找 needle 首次出现的位置，并转换成 LSP 所需的 position：
    - line: 0-based 行号
    - character: 0-based 列号（基于 UTF-16 可能更严谨，但这里先按 Python 字符索引演示）
      * 注：严格的 LSP/VSCode position 的 character 常用 UTF-16 code unit，
        对 ASCII/英文基本一致，对 emoji/部分非 BMP 字符会有偏差。
        Java 源码通常影响不大。
    prefer_after=True 表示返回 needle 之后的位置（比如触发 "System." 后面的 completion）。
    """
    idx = text.find(needle)
    if idx < 0:
        raise ValueError(f"Cannot find needle in file: {needle!r}")
    if prefer_after:
        idx += len(needle)

    # 计算 line
    line = text.count("\n", 0, idx)
    # 计算 character：最后一个换行到 idx 的偏移
    last_nl = text.rfind("\n", 0, idx)
    ch = idx if last_nl < 0 else idx - last_nl - 1
    return line, ch


# -------------------------
# main demo
# -------------------------

async def main():
    # argparse 这里你暂时注释了一些参数，改成写死路径
    # 这样更适合你先跑通，再逐步参数化
    ap = argparse.ArgumentParser()
    ap.add_argument("--java", default="java", help="java executable, e.g. /path/to/java")
    args = ap.parse_args()

    # -------------------------------------------------------------------------
    # 这里是你当前写死的路径：
    # - jdtls_home: jdtls 解压目录
    # - project_root: 你的 Java 项目根目录（包含 pom.xml）
    # - ws_dir: jdtls 的 workspace 目录（注意：不是项目目录！）
    # - file_path: 本次演示要打开的 Java 文件
    # -------------------------------------------------------------------------
    jdtls_home = Path(r"E:\javaTools\LSP\jdt-language-server-1.54.0")
    project_root = Path(r"E:\JavaProject\HellWorld")
    ws_dir = Path(r"E:\javaTools\LSP\workspaces")
    file_path = project_root / "src/main/java/com/lacknb/Main.java"

    if not file_path.exists():
        raise FileNotFoundError(f"Java file not found: {file_path}")

    # jdtls 启动所需：launcher jar + config 目录
    launcher = find_launcher_jar(jdtls_home)
    config_dir = guess_jdtls_config_dir(jdtls_home)

    # -------------------------------------------------------------------------
    # 组装 jdtls 启动命令：
    # -D...：Eclipse/OSGi 的启动参数
    # -jar：指定 equinox launcher
    # -configuration：指定 config_win/config_linux/config_mac
    # -data：指定 jdtls workspace（索引/缓存/项目导入状态目录）
    # -------------------------------------------------------------------------
    cmd = [
        args.java,
        "-Declipse.application=org.eclipse.jdt.ls.core.id1",
        "-Dosgi.bundles.defaultStartLevel=4",
        "-Declipse.product=org.eclipse.jdt.ls.core.product",
        "-Dlog.level=ALL",
        "-noverify",
        "-Xmx1G",
        "-jar", str(launcher),
        "-configuration", str(config_dir),
        "-data", str(ws_dir),
    ]

    # -------------------------------------------------------------------------
    # 启动子进程：
    # stdin/stdout/stderr 都用 PIPE，这样 Python 可以通过 stdio 做 LSP 通信。
    # cwd 设置为 project_root 只是让 jdtls 的相对路径/日志更合理，
    # 真正告诉 jdtls "分析哪个项目" 是靠 initialize 的 rootUri/workspaceFolders。
    # -------------------------------------------------------------------------
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(project_root),
    )

    # 创建 LSP client 并启动后台读循环
    client = LspClient(proc)
    await client.start()

    # LSP 强制使用 URI 表示根目录/文件路径
    root_uri = path_to_file_uri(project_root)
    file_uri = path_to_file_uri(file_path)

    # -------------------------------------------------------------------------
    # 1) initialize
    # LSP 标准流程：
    #   client -> initialize(request)
    #   server -> initialize(response, capabilities)
    #   client -> initialized(notification)
    #
    # capabilities：声明客户端能支持哪些能力（这里用最常见的一些）
    # rootUri / workspaceFolders：告诉 server 要管理哪个项目（workspace）
    # -------------------------------------------------------------------------
    init_params = {
        "processId": os.getpid(),
        "rootUri": root_uri,
        "workspaceFolders": [{"uri": root_uri, "name": project_root.name}],
        "capabilities": {
            "textDocument": {
                "hover": {"contentFormat": ["markdown", "plaintext"]},
                "definition": {"dynamicRegistration": False},
                "completion": {"completionItem": {"snippetSupport": True}},
                "publishDiagnostics": {"relatedInformation": True},
            },
            "workspace": {"workspaceFolders": True},
        },
        "clientInfo": {"name": "python-jdtls-demo", "version": "0.1"},
    }

    init_result = await client.send_request("initialize", init_params)

    # 2) initialized（必须发）
    await client.send_notification("initialized", {})

    print("✅ initialize done, server capabilities keys:", list(init_result.get("capabilities", {}).keys()))

    # -------------------------------------------------------------------------
    # 3) didOpen
    # 告诉 server：我打开了某个文件，内容如下。
    # 注意：这里把整个文件内容发给 server（首次打开）
    # 后续编辑应使用 didChange 增量/全量更新。
    # -------------------------------------------------------------------------
    text = file_path.read_text(encoding="utf-8", errors="replace")
    await client.send_notification("textDocument/didOpen", {
        "textDocument": {
            "uri": file_uri,
            "languageId": "java",
            "version": 1,
            "text": text
        }
    })
    print(f"✅ didOpen sent: {file_path}")

    # 等待一小会儿让 jdtls 做初始导入/解析/诊断
    # 对于首次导入 Maven 项目，2 秒可能偏短，你后续可以改成轮询等待 diagnostics
    await asyncio.sleep(2.0)

    # -------------------------------------------------------------------------
    # 4) diagnostics
    # diagnostics 是 server 主动 push 的 notification：
    #   textDocument/publishDiagnostics
    # 我们在 _dispatch_loop 里已经收集到 client._diagnostics 中。
    # -------------------------------------------------------------------------
    diags = client._diagnostics.get(file_uri)
    if diags is None:
        print("ℹ️ no diagnostics received yet (may take longer on first import/index).")
    else:
        dlist = diags.get("diagnostics", [])
        print(f"📋 diagnostics count: {len(dlist)}")
        for d in dlist[:5]:
            rng = d.get("range", {})
            msg = d.get("message", "")
            sev = d.get("severity", "")
            print(f"  - severity={sev} range={rng} msg={msg[:120]}")

    # -------------------------------------------------------------------------
    # 5) hover demo
    # hover：给定一个 position，返回该符号的类型/文档。
    # 这里用 find_position 找到 "String" 或 "System" 作为演示点。
    # -------------------------------------------------------------------------
    try:
        line, ch = find_position(text, "String")
    except ValueError:
        line, ch = find_position(text, "System")

    hover = await client.send_request("textDocument/hover", {
        "textDocument": {"uri": file_uri},
        "position": {"line": line, "character": ch},
    })

    print("\n🪧 hover result:")
    if hover and "contents" in hover:
        print(json.dumps(hover["contents"], ensure_ascii=False, indent=2)[:1200])
    else:
        print(hover)

    # -------------------------------------------------------------------------
    # 6) definition demo
    # definition：跳转定义位置（返回 Location / Location[]）。
    # 注意：对 JDK 内置类（如 System/String）有时可能返回空，
    # 更稳定的演示方式是跳到你自己项目里的类/方法。
    # -------------------------------------------------------------------------
    try:
        dline, dch = find_position(text, "System")
        definition = await client.send_request("textDocument/definition", {
            "textDocument": {"uri": file_uri},
            "position": {"line": dline, "character": dch},
        })
        print("\n📍 definition result (first 1):")
        if isinstance(definition, list) and definition:
            print(json.dumps(definition[0], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(definition, ensure_ascii=False, indent=2)[:1200])
    except Exception as e:
        print("\n⚠️ definition failed:", e)

    # -------------------------------------------------------------------------
    # 7) completion demo
    # completion：补全建议列表。
    # 这里通过查找 "System." 并把 position 放在 '.' 后面触发补全。
    # -------------------------------------------------------------------------
    try:
        cline, cch = find_position(text, "System.", prefer_after=True)
        completion = await client.send_request("textDocument/completion", {
            "textDocument": {"uri": file_uri},
            "position": {"line": cline, "character": cch},
            "context": {"triggerKind": 1},  # 1=Invoked（手动触发），2=TriggerCharacter 等
        })
        print("\n✨ completion result (first 10 labels):")
        items = completion.get("items") if isinstance(completion, dict) else completion
        if isinstance(items, list):
            for it in items[:10]:
                print("  -", it.get("label"))
        else:
            print(json.dumps(completion, ensure_ascii=False, indent=2)[:1200])
    except Exception as e:
        print("\n⚠️ completion failed:", e)

    # -------------------------------------------------------------------------
    # 8) shutdown / exit（优雅关闭）
    # 正确关闭顺序建议：
    #   client -> shutdown(request)
    #   server -> shutdown(response)
    #   client -> exit(notification)
    #
    # 然后关闭 stdin，等待进程退出。
    # 最后 cancel 掉 dispatch loop，避免 event loop 退出时管道析构噪音（Windows 常见）。
    # -------------------------------------------------------------------------
    try:
        await client.send_request("shutdown", None)
    except Exception:
        pass

    try:
        await client.send_notification("exit", None)
    except Exception:
        pass

    # 关闭 stdin：告诉 server 客户端不再发送任何消息
    try:
        client.writer.close()
        await client.writer.wait_closed()
    except Exception:
        pass

    # 等待 jdtls 进程退出（给 10 秒）
    try:
        await asyncio.wait_for(proc.wait(), timeout=10.0)
    except Exception:
        # 超时则强制 terminate
        try:
            proc.terminate()
        except Exception:
            pass

    # 取消 dispatch loop：避免程序结束时仍在 await _read_msg() 读 pipe
    if client._dispatch_task:
        client._dispatch_task.cancel()
        try:
            await client._dispatch_task
        except asyncio.CancelledError:
            pass
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
