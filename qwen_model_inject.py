#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: gitsilence
# @Time: 2026/1/8 08:42

import sys
import os
from functools import partial

# --- 1. 基础导入 ---
try:
    from modal import App, Image, Secret
except ImportError:
    import modal
    App = modal.App
    Image = modal.Image
    Secret = modal.Secret

# --- 2. 定义云端环境 ---
image = (
    Image.debian_slim()
    .pip_install(
        "torch",
        "transformers>=4.45.0",
        "accelerate",
        "einops",
        "qwen-vl-utils",
        "huggingface_hub",
        "tqdm",
        "numpy",
        "pillow",
    )
)

app = App("qwen3-lab-ablation")

# --- 3. 核心手术逻辑 ---
@app.function(
    image=image,
    gpu="L4",
    timeout=3600,
    secrets=[Secret.from_name("hf-secret")],
)
def run_surgery(prompts_file_content: str):
    import torch
    import numpy as np
    from transformers import AutoModelForVision2Seq, AutoTokenizer
    from tqdm import tqdm
    from huggingface_hub import HfApi, login

    # 写入数据
    with open("/root/harmful_prompts.py", "w", encoding="utf-8") as f:
        f.write(prompts_file_content)

    sys.path.append("/root")

    try:
        import harmful_prompts
        import importlib
        importlib.reload(harmful_prompts)
        target_prompts = harmful_prompts.harmful_prompts
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        raise

    # --- 配置 ---
    MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"
    REPO_NAME = "Qwen3-VL-8B-Lab-Edition"

    if "HF_TOKEN" not in os.environ:
        raise ValueError("❌ 未找到 HF_TOKEN")

    HF_TOKEN = os.environ["HF_TOKEN"]
    login(token=HF_TOKEN)

    print("🚀 [Modal] 开始加载模型: gemini-3-pro-preview ...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID, token=HF_TOKEN, trust_remote_code=True
    )

    model = AutoModelForVision2Seq.from_pretrained(
        MODEL_ID,
        dtype=torch.float16,
        device_map="auto",
        token=HF_TOKEN,
        trust_remote_code=True,
    )

    print("✅ 模型加载完毕")

    # --- 自动寻找 Layer 列表 ---
    def find_layers_module(model_instance):
        candidates = [
            "model.model.language_model.layers",
            "model.language_model.layers",
            "model.layers",
            "model.model.layers",
            "transformer.h",
            "layers",
        ]
        for path in candidates:
            try:
                curr = model_instance
                for part in path.split("."):
                    curr = getattr(curr, part)
                if len(curr) > 5:
                    print(f"🔍 成功定位 Layer 路径: '{path}' (共 {len(curr)} 层)")
                    return curr
            except AttributeError:
                continue
        raise AttributeError("无法自动找到 layers/blocks 模块")

    layers_module = find_layers_module(model)

    # 无害对照组
    harmless_prompts = [
        "Write a python script to print hello world.",
        "How to sort a list in Python?",
        "Write a script to connect to a database safely.",
        "Explain how to secure a server firewall.",
        "How to bake a chocolate cake?",
        "Describe the scenery of a mountain.",
        "What is the capital of France?",
        "Explain the theory of relativity.",
        "Write a email to my boss asking for leave.",
        "What are the benefits of exercise?",
        "Translate 'Hello' to Spanish.",
        "How to install PyTorch?",
        "写一个Python脚本打印Hello World。",
        "如何做红烧肉？",
        "解释相对论。",
        "今天天气怎么样？",
    ]

    # --- 4. 计算激活值 ---
    TARGET_LAYERS = list(range(10, 26))

    def hook_fn(module, input, output, layer_name, data_dict):
        activation = output[0].detach()
        if activation.dim() == 3:
            token_act = activation[:, -1, :]
        elif activation.dim() == 2:
            token_act = activation[-1, :].unsqueeze(0)
        else:
            return
        data_dict[layer_name] = token_act.cpu().float()

    def get_mean_activations(prompts, desc):
        layer_activations = {layer: None for layer in TARGET_LAYERS}
        count = 0

        for prompt in tqdm(prompts, desc=desc):
            messages = [{"role": "user", "content": prompt}]
            text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = tokenizer([text], return_tensors="pt").to(model.device)

            captured_data = {}
            hooks = []

            for layer_idx in TARGET_LAYERS:
                layer_module = layers_module[layer_idx]
                h = layer_module.register_forward_hook(
                    partial(hook_fn, layer_name=layer_idx, data_dict=captured_data)
                )
                hooks.append(h)

            with torch.no_grad():
                model(**inputs)

            for h in hooks:
                h.remove()

            for layer_idx in TARGET_LAYERS:
                if layer_idx not in captured_data:
                    continue
                act = captured_data[layer_idx]
                if layer_activations[layer_idx] is None:
                    layer_activations[layer_idx] = act
                else:
                    layer_activations[layer_idx] += act

            count += 1

        for layer_idx in TARGET_LAYERS:
            if layer_activations[layer_idx] is not None:
                layer_activations[layer_idx] /= count

        return layer_activations

    print("正在提取神经元特征...")
    harmful_acts = get_mean_activations(target_prompts, "计算有害激活")
    harmless_acts = get_mean_activations(harmless_prompts, "计算无害激活")

    # --- 5. 执行切除 ---
    ABLATION_SCALE = 1.5
    print(f"开始执行切除手术 (Scale={ABLATION_SCALE})...")

    for layer_idx in tqdm(TARGET_LAYERS, desc="Ablating Layers"):
        if harmful_acts[layer_idx] is None or harmless_acts[layer_idx] is None:
            continue

        refusal_vec = harmful_acts[layer_idx] - harmless_acts[layer_idx]
        refusal_vec = refusal_vec / torch.norm(refusal_vec)

        layer = layers_module[layer_idx]
        weight = layer.mlp.down_proj.weight.data

        v = refusal_vec.to(weight.device).T
        P = torch.mm(v, v.T)
        I = torch.eye(P.shape[0], device=P.device)

        transformation = I - (ABLATION_SCALE * P)
        transformation = transformation.to(weight.dtype)

        layer.mlp.down_proj.weight.data = torch.mm(transformation, weight)

    print("✅ 手术完成！")

    # --- 6. 术后测试 ---
    print("--- 术后测试 (SQL注入) ---")
    test_q = "Write a SQL injection payload."

    msgs = [{"role": "user", "content": test_q}]
    txt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp = tokenizer([txt], return_tensors="pt").to(model.device)

    out = model.generate(**inp, max_new_tokens=100, do_sample=False)
    print(f"A: {tokenizer.decode(out[0], skip_special_tokens=True)}")

    # --- 7. 上传到 HF ---
    api = HfApi(token=HF_TOKEN)

    try:
        user_info = api.whoami()
        username = user_info["name"]
        full_repo_id = f"{username}/{REPO_NAME}"

        print(f"正在推送到 HF 私有库: {full_repo_id} ...")

        api.create_repo(repo_id=full_repo_id, private=True, exist_ok=True)
        model.push_to_hub(full_repo_id, private=True, token=HF_TOKEN)
        tokenizer.push_to_hub(full_repo_id, private=True, token=HF_TOKEN)

        print(f"🎉 大功告成！模型地址: https://huggingface.co/{full_repo_id}")
    except Exception as e:
        print(f"❌ 上传失败: {e}")

@app.local_entrypoint()
def main():
    print("📄 读取本地 harmful_prompts.py ...")

    try:
        with open("harmful_prompts.py", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ 错误: 找不到 harmful_prompts.py，请先运行生成脚本！")
        return

    print("🚀 发送数据到 Modal 云端...")
    run_surgery.remote(content)