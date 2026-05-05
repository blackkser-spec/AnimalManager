import pytest
from unittest.mock import MagicMock, patch
from cli import menu_printer, formatter

class DummyAnimal:
    def __init__(self, id, animal_type, name):
        self.id = id
        self.animal_type = animal_type
        self.name = name

#個別のロジックが薄い/ほかのテストで網羅されている関数のテストはオミットされています

class TestPrintNumberedLine:
    @pytest.mark.parametrize("items, expected", [
        (["a", "b", "c"], ["1. a", "2. b", "3. c"]),
        ({"k1": "a", "k2": "b", "k3": "c"}, ["1. a", "2. b", "3. c"]),
    ])
    def test_success(self, capsys, items, expected):
        # Act
        menu_printer._print_numbered_line(items)
        captured = capsys.readouterr()
        output = captured.out.strip().split("\n")    
        # Assert
        assert output == expected
    
    def test_with_color(self, capsys):
        # Arrange
        items = ["a"]
        
        def mock_color(s):
            return f"[colored]{s}"
        
        menu_printer._print_numbered_line(items, color_func=mock_color)
        captured = capsys.readouterr()
        output = captured.out.strip()
        # Assert
        assert output == "[colored]1. a"
    

class TestPrintInlineChoices:
    @pytest.mark.parametrize("keys, expected", [
        (["id", "name"], "1:ID 2:名前"),
        (["type", "unknown"], "1:種類 2:unknown"),
    ])
    def test_success(self, capsys, keys, expected):
        # Arrange
        test_H = {"id": "ID", "name": "名前", "type": "種類"}
        with patch("cli.menu_printer.H", test_H):
            # Act
            menu_printer._print_inline_choices(keys)
            captured = capsys.readouterr()
            output = captured.out.strip()
            # Assert
            assert output == expected


class TestInlineOptions:
    def test_success(self, capsys):
        # Arrange
        header_key = "sort_choice_header"
        keys = ["id", "name"]
        test_H = {"sort_choice_header": "ソート項目の一覧", "id": "ID", "name": "名前"}

        with patch("cli.menu_printer.H", test_H):
            # Act
            menu_printer.print_inline_options(header_key, keys)
            captured = capsys.readouterr()
            output = captured.out.strip().split("\n")
            # Assert
            output = "\n".join(output)
            assert "ソート項目の一覧" in output
            assert "1:ID 2:名前" in output


class TestPrintMenu:
    def test_success(self, capsys):
        """メニューの構造（タイトル、項目、フッター）が正しく出力されるか"""
        # Arrange: Ma をテスト用の固定データに差し替える
        test_ma = {"opt1": "Action 1", "opt2": "Action 2"}

        with patch("cli.menu_printer.Ma", test_ma), \
             patch("cli.menu_printer.T", {"title_start": "START", "title_end": "END"}):   
            # Act
            menu_printer.print_menu()
            output = capsys.readouterr().out
            
            # Assert
            assert formatter.blue("START") in output
            assert formatter.blue("1. Action 1") in output
            assert formatter.blue("2. Action 2") in output
            assert formatter.blue("END") in output

    def test_actual_content(self, capsys):
        """実際の text.py の内容が少なくとも含まれているか（簡易検証）"""
        menu_printer.print_menu()
        output = capsys.readouterr().out
        for label in menu_printer.Ma.values():
            assert label in output


class TestPrintAnimalList:
    def test_success(self, capsys):
        # Arrange
        mock_pad_right = MagicMock(side_effect=lambda text, width: f"[{text}:{width}]")
        mock_get_display_width = MagicMock(return_value=35)

        animals = [
            DummyAnimal(1, "cat", "Tama"),
            DummyAnimal(2, "dog", "Pochi"),
        ]
        test_H = {"id": "ID", "type": "種類", "name": "名前"}

        with patch("cli.formatter.pad_right", mock_pad_right), \
             patch("cli.formatter.get_display_width", mock_get_display_width), \
             patch("cli.menu_printer.H", test_H):
            # Act
            menu_printer.print_animal_list(animals)
            output_lines = capsys.readouterr().out.strip().split("\n")
            # Assert
            assert output_lines[0] == "[ID:5][種類:10][名前:20]"
            assert output_lines[1] == "-" * 35
            assert output_lines[2] == "[1:5][cat:10][Tama:20]"
            assert output_lines[3] == "[2:5][dog:10][Pochi:20]"

class TestGetText:
    def test_success(self):
        """指定したセクションとキーから、フォーマット済みのテキストが取得できるか"""
        # Arrange: 辞書全体をモックデータに置き換える準備
        test_text = {
            "test_section": {"test_key": "Hello, {name}!"}
        }
        with patch("cli.menu_printer.TEXT", test_text):
            # Act
            result = menu_printer.get_text("test_section", "test_key", name="World")
            # Assert
            assert result == "Hello, World!"

    def test_missing_key(self):
        with pytest.raises(KeyError):
            menu_printer.get_text("main", "missing_key", name="World")

    def test_format_missing_arg(self):
        # Arrange
        TEXT = {"main": {"greet": "Hello {name}"}}
        with patch("cli.menu_printer.TEXT", TEXT):
            # Act
            result = menu_printer.get_text("main", "greet")
        # Assert
        assert result == "Hello {name}"

class TestActionResult:
    def test_success(self, capsys):
        # Arrange
        test_Ac = {"test_fly": {"bird": "{animal_name} is flying!"}}
        with patch("cli.menu_printer.Ac", test_Ac):
            # Act
            menu_printer.print_action_result("test_fly", "bird", animal_name="test_bird")
            output = capsys.readouterr().out
            # Assert
            assert output.strip() == "test_bird is flying!"

    def test_missing_action_key(self, capsys):
        # Arrange
        test_Ac = {}
        with patch("cli.menu_printer.Ac", test_Ac):
            # Act
            menu_printer.print_action_result("unknown_action", "unknown_type", animal_name="test_bird")
            output = capsys.readouterr().out
            # Assert
            assert output.strip() == "test_bird (unknown_type): unknown_action"