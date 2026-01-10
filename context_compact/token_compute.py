

class Token:
    """Token 估算工具类，支持中英文混合文本"""

    # 中文字符（CJK 统一表意文字）每个约 1-2 Token，保守取 1.5
    TOKENS_PER_CJK_CHAR = 1.5
    # 英文/数字/符号，约 4 字符 = 1 Token
    CHARS_PER_ASCII_TOKEN = 4

    @staticmethod
    def is_cjk(char: str) -> bool:
        """
        判断字符是否为中日韩表意文字
        范围：CJK Unified Ideographs + 扩展区 + 标点
        """
        code = ord(char)
        return (
                (0x4E00 <= code <= 0x9FFF) or  # CJK 基本区
                (0x3400 <= code <= 0x4DBF) or  # CJK 扩展 A
                (0x20000 <= code <= 0x2A6DF) or  # CJK 扩展 B
                (0xF900 <= code <= 0xFAFF) or  # CJK 兼容
                (0x3000 <= code <= 0x303F) or  # CJK 标点（。、「」等）
                (0xFF00 <= code <= 0xFFEF)  # 全角字符（！？等）
        )

    @classmethod
    def estimate(cls, text: str) -> int:
        """
        估算文本的 Token 数量

        Args:
            text: 输入文本

        Returns:
            估算的 Token 数量
        """
        if not text:
            return 0

        cjk_count = 0
        ascii_count = 0

        for char in text:
            if cls.is_cjk(char):
                cjk_count += 1
            else:
                ascii_count += 1

        cjk_tokens = cjk_count * cls.TOKENS_PER_CJK_CHAR
        ascii_tokens = ascii_count / cls.CHARS_PER_ASCII_TOKEN

        return max(0, round(cjk_tokens + ascii_tokens))


# 使用示例
if __name__ == "__main__":
    test_cases = [
        "Hello World",
        "你好世界",
        "Hello 你好",
        "这是一段很长的中文测试文本",
        "The quick brown fox jumps over the lazy dog",
        "人工智能 (AI) 正在改变世界",
    ]

    for text in test_cases:
        tokens = Token.estimate(text)
        print(f"'{text}' => {tokens} tokens")
