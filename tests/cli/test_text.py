import pytest
from colorama import Fore, Style
import CLI.text as text

class TestTextColor:
    """文字色の装飾が正しく ANSI エスケープシーケンスを含んでいるか検証"""
    
    def test_red(self):
        assert text.red("error") == f"{Fore.RED}error{Style.RESET_ALL}"

    def test_green(self):
        assert text.green("success") == f"{Fore.GREEN}success{Style.RESET_ALL}"

    def test_blue(self):
        assert text.blue("info") == f"{Fore.BLUE}info{Style.RESET_ALL}"

    def test_yellow(self):
        assert text.yellow("warning") == f"{Fore.YELLOW}warning{Style.RESET_ALL}"

class TestDisplayWidth:
    @pytest.mark.parametrize("input_str, expected_width", [
        ("abc", 3),           # 半角のみ
        ("あいう", 6),         # 全角のみ
        ("Hello世界", 9),      # 半角(5) + 全角(2*2) = 9
        ("🐱", 2),            # 絵文字（Wide文字として扱われる）
        ("", 0),              # 空文字
        ("123 456", 7),       # 半角スペース
    ])
    def test_get_display_width(self, input_str, expected_width):
        assert text.get_display_width(input_str) == expected_width

class TestPadding:

    def test_pad_right_half(self):
        # "abc" (3) + " " * (10 - 3) = 10文字分
        result = text.pad_right("abc", 10)
        assert result == "abc       "
        assert len(result) == 10

    def test_pad_right_full(self):
        # "あいう" (6) + " " * (10 - 6) = 10幅分
        result = text.pad_right("あいう", 10)
        assert result == "あいう    "
        # Pythonのlen()は文字数(7)だが、表示幅は10
        assert text.get_display_width(result) == 10