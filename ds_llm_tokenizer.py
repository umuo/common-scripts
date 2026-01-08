from transformers import AutoTokenizer

# 自动读取目录中的 tokenizer.json, tokenizer_config.json
tokenizer = AutoTokenizer.from_pretrained('./deepseek-v3.2-tokenizer')
text = """
正如我们第一部分所说，LLM 是一个概率模型，通过数学计算来进行下一个字的预测。然而，计算机只认识数字（0和1），并不认识"今天"、"天气"或者"Today"这些单词。因此，想要让计算机能够理解人类的语言，需要通过特定的编码机制将自然语言翻译成模型能运算的数字序列。分词器（Tokenizer）是实现这一功能的核心组件，它能够将连续文本拆解为离散语义单元（即Token）并转换为唯一索引（Token ID）用于模型输入。

所有 LLM 的输入都依赖 Tokenizer 的预处理结果。如果分词策略不合理，如拆分后丢失语义或 Token 粒度过细，会直接影响模型对文本的理解能力。因此，一个设计优良的 Tokenizer 是提升 LLM 性能的基础前提。

2.2 Tokenizer分类
根据切分粒度的不同，Tokenizer可分为三大类：字符级Tokenizer（Character-level）、词级Tokenizer（Word-level）以及子词级 Tokenizer（Subword-level）。我们以句子 "Today is sunday." 为例，看看它们是如何工作的。
"""
# encode 方法会将文本转换为数学序列
input_ids = tokenizer.encode(text)
print(f"{'ID':<10} | {'Token (原始)':<15} | {'解码后的内容'}")
print("-" * 45)

for idx in input_ids:
    # 1. 获取原始 token（可能包含字节乱码）
    raw_token = tokenizer.convert_ids_to_tokens(idx)

    # 2. 将单个 ID 解码为文本（这样能正确显示汉字碎片）
    # skip_special_tokens=False 保证能看到 [BOS] 等特殊字符
    decoded_word = tokenizer.decode([idx])

    print(f"{idx:<10} | {raw_token:<15} | {decoded_word}")


print(f"总共Token数量：{len(input_ids)}")
