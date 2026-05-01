import pytest
from colorama import Fore, Style
import cli.formatter as formatter

class TestTextColor:
    """文字色の装飾が正しく ANSI エスケープシーケンスを含んでいるか検証"""
    def test_red(self):
        assert formatter.red("error") == f"{Fore.RED}error{Style.RESET_ALL}"

    def test_green(self):
        assert formatter.green("success") == f"{Fore.GREEN}success{Style.RESET_ALL}"

    def test_blue(self):
        assert formatter.blue("info") == f"{Fore.BLUE}info{Style.RESET_ALL}"

    def test_yellow(self):
        assert formatter.yellow("warning") == f"{Fore.YELLOW}warning{Style.RESET_ALL}"

class TestDisplayWidth:
    @pytest.mark.parametrize("input_str, expected_width", [
        ("abc", 3),          
        ("あいう", 6),
        ("Hello世界", 9),
        ("🐱", 2),
        ("", 0),
        ("123 456", 7),
    ])
    def test_get_display_width(self, input_str, expected_width):
        assert formatter.get_display_width(input_str) == expected_width

class TestPadding:
    def test_pad_right_half(self):
        # "abc" (3) + " " * (10 - 3) = 10文字分
        result = formatter.pad_right("abc", 10)
        assert result == "abc       "
        assert len(result) == 10

    def test_pad_right_full(self):
        # "あいう" (6) + " " * (10 - 6) = 10幅分
        result = formatter.pad_right("あいう", 10)
        assert result == "あいう    "
        assert len(result) == 7
        assert formatter.get_display_width(result) == 10
