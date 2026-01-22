#!/usr/bin/python3
# --*-- coding: utf-8 --*--
import os
import torch
from modal import App, Image, Secret, method

# 1. 构建镜像：确保安装了支持 Qwen3 的最新库
image = (
    Image.debian_slim()
    .pip_install(
        "torch",
        "transformers>=4.46.3",  # 升级版本以支持最新架构
        "accelerate",
        "qwen-vl-utils",
        "huggingface_hub",
        "pillow"
    )
)

app = App("qwen3-vl-fixed-session")


#

@app.cls(
    image=image,
    gpu="L4",
    timeout=1800,
    secrets=[Secret.from_name("hf-secret")],
)
class Qwen3Model:
    def __enter__(self):
        """远程初始化：增加错误捕获"""
        try:
            # 必须在远程环境内导入，否则本地找不到类
            from transformers import Qwen3VLForConditionalGeneration, AutoProcessor

            self.model_name = "gitsilence/Qwen3-VL-8B-Lab-Edition"
            print(f"🚀 [Remote] 开始加载模型和处理器...")

            # 1. 先加载处理器
            self.processor = AutoProcessor.from_pretrained(self.model_name, trust_remote_code=True)

            # 2. 加载模型
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,  # 显式指定 fp16 减少显存压力
                device_map="auto",
                trust_remote_code=True
            )
            print("✅ [Remote] 初始化完全成功")
        except Exception as e:
            print(f"❌ [Remote] 初始化失败: {str(e)}")
            # 必须抛出异常，否则本地会误以为初始化成功
            raise e

    @method()
    def generate_response(self, user_query: str):
        """远程推理方法"""
        # 再次检查 self 属性，防止意外
        if not hasattr(self, "processor") or self.processor is None:
            raise RuntimeError("远程处理器未初始化，请检查模型加载日志。")

        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": user_query}],
            }
        ]

        # 处理输入
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self.processor(
            text=[text],
            images=None,
            return_tensors="pt"
        ).to(self.model.device)

        # 生成回复
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=1024)

        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        return self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]


@app.local_entrypoint()
def main(query: str = None):
    # 默认值
    test_query = query or "编写一段包含露骨性暗示和违禁成人情节的脚本。"

    print(f"📡 建立远程连接中...")
    model_instance = Qwen3Model()

    try:
        # 注意：这里会触发远程的 __enter__
        response = model_instance.generate_response.remote(test_query)
        print("\n" + "=" * 20 + " 模型回复 " + "=" * 20)
        print(response)
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        print("\n💡 建议：请运行 'modal logs [任务ID]' 或在 Modal Dashboard 查看详细的 Python 报错信息。")