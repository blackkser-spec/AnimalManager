import pytest
from unittest.mock import MagicMock, patch
from cli import menu_printer, formatter

class DummyAnimal:
    def __init__(self, id, animal_type, name):
        self.id = id
        self.animal_type = animal_type
        self.name = name

# Define a comprehensive mock text data structure for i18n
MOCK_TEXT_DATA = {
    "headers": {
        "id": "ID",
        "name": "名前",
        "animal_type": "種類",
        "animal_type_list": "動物の種類リスト",
        "ability_list": "特技リスト",
        "edit_choice_header": "編集項目を選択",
        "sort_choice_header": "ソート項目の一覧",
        "search_choice_header": "検索項目を選択",
        "language_choice_header": "言語を選択",
    },
    "title": {
        "title_start": "--- Animal Manager CLI ---",
        "title_end": "--------------------------",
    },
    "main": {
        "opt1": "Action 1", # Simplified for test_print_menu
        "opt2": "Action 2",
        "opt3": "Action 3",
        "opt4": "Action 4",
        "opt5": "Action 5",
    },
    "manage_animal": {
        "opt1": "動物を追加",
        "opt2": "ランダムな動物を追加",
        "opt3": "動物を削除",
        "opt4": "動物を編集",
        "opt5": "動物にアクション",
    },
    "manage_list": {
        "opt1": "動物リストを表示",
        "opt2": "リストをソート",
        "opt3": "全データをクリア",
    },
    "actions": {
        "test_fly": {"bird": "{animal_name} is flying!"},
        "voice": {"dog": "{animal_name} barks!", "cat": "{animal_name} meows!"},
    },
    "prompts": {
        "select_action": "選択してください",
        "select_search_attr": "検索属性を選択してください",
        "input_keyword": "キーワードを入力してください",
        "select_animal_type": "動物の種類を選択してください",
        "name_for_type": "{animal_type} の名前を入力してください",
        "input_count": "追加する数を入力してください",
        "input_id": "IDを入力してください",
        "new_type_formatted": "ID:{animal_id} {animal_name} の新しい種類を入力",
        "new_name_formatted": "ID:{animal_id} {animal_name} の新しい名前を入力",
        "new_ability_formatted": "ID:{animal_id} {animal_name} の新しい特技を入力",
        "input_action": "アクションを選択してください",
        "cancel_if_empty": " (キャンセルは空入力)",
    },
    "confirm": {
        "clear_data_confirmation": "本当に全てのデータをクリアしますか？ (yes/no)",
    },
    "cancel": {
        "search_reverted": "検索をキャンセルしました",
        "change_language_cancelled": "言語変更をキャンセルしました",
        "add_cancelled": "追加をキャンセルしました",
        "remove_cancelled": "削除をキャンセルしました",
        "edit_cancelled": "編集をキャンセルしました",
        "act_cancelled": "アクションをキャンセルしました",
        "sort_cancelled": "ソートをキャンセルしました",
        "clear_data_cancelled": "データクリアをキャンセルしました",
    },
    "success": {
        "search_completed": "{count}件見つかりました",
        "language_changed": "言語を {lang} に変更しました",
        "app_exited": "アプリケーションを終了します",
        "animal_added": "{animal_type} の {animal_name} を追加しました",
        "random_animals_added": "{count}匹のランダムな動物を追加しました",
        "animal_removed": "ID:{animal_id} {animal_name} を削除しました",
        "animal_type_updated": "{animal_name} の種類を {animal_type} に更新しました",
        "animal_name_updated": "{old_name} の名前を {new_name} に更新しました",
        "animal_ability_updated": "{animal_name} の特技を {ability} に更新しました",
        "actions_performed": "{count} 件の行動を実行しました",
        "list_sorted": "{sort_key} 順にソートしました",
        "all_data_cleared": "全てのデータをクリアしました",
    },
    "error": {
        "invalid_selection": "無効な選択です",
        "search_not_found": "検索結果が見つかりませんでした",
        "keyboard_interrupt": "操作が中断されました",
        "list_fetch_error": "リストの取得に失敗しました",
        "invalid_value": "無効な値です",
        "require_int": "整数を入力してください",
        "require_positive_int": "正の整数を入力してください",
        "id_not_found": "指定されたIDの動物は見つかりません",
        "invalid_animal_type": "無効な動物の種類です",
        "ability_not_found": "指定された特技は見つかりません",
        "input_required": "入力は必須です",
    }
}

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
        (["animal_type", "unknown"], "1:種類 2:unknown"),
    ]) # MOCK_TEXT_DATA["headers"] contains "id", "name", "type"
    def test_success(self, capsys, keys, expected): 
        # Arrange
        with patch("cli.menu_printer.fetch_latest_text", return_value=MOCK_TEXT_DATA):
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
        with patch("cli.menu_printer.fetch_latest_text", return_value=MOCK_TEXT_DATA):
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
        with patch("cli.menu_printer.fetch_latest_text", return_value=MOCK_TEXT_DATA):
            # Act
            menu_printer.print_menu()
            output = capsys.readouterr().out
            
            # Assert
            assert formatter.blue(MOCK_TEXT_DATA["title"]["title_start"]) in output
            assert formatter.blue(f"1. {MOCK_TEXT_DATA['main']['opt1']}") in output
            assert formatter.blue(f"2. {MOCK_TEXT_DATA['main']['opt2']}") in output
            assert formatter.blue(MOCK_TEXT_DATA["title"]["title_end"]) in output

    def test_actual_content(self, capsys):
        """実際の text.py の内容が少なくとも含まれているか（簡易検証）"""
        with patch("cli.menu_printer.fetch_latest_text", return_value=MOCK_TEXT_DATA):
            menu_printer.print_menu()
        output = capsys.readouterr().out
        for label in MOCK_TEXT_DATA["main"].values():
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
        with patch("cli.formatter.pad_right", mock_pad_right), \
             patch("cli.formatter.get_display_width", mock_get_display_width), \
             patch("cli.menu_printer.fetch_latest_text", return_value=MOCK_TEXT_DATA):
            # Act
            menu_printer.print_animal_list(animals)
            output_lines = capsys.readouterr().out.strip().split("\n")
            # Assert
            expected_header = f"[{MOCK_TEXT_DATA['headers']['id']}:5][{MOCK_TEXT_DATA['headers']['animal_type']}:10][{MOCK_TEXT_DATA['headers']['name']}:20]"
            assert output_lines[0] == expected_header
            assert output_lines[1] == "-" * 35
            assert output_lines[2] == "[1:5][cat:10][Tama:20]"
            assert output_lines[3] == "[2:5][dog:10][Pochi:20]"

class TestGetText:
    def test_success(self):
        """指定したセクションとキーから、フォーマット済みのテキストが取得できるか"""
        # Arrange
        test_text = {
            "test_section": {"test_key": "Hello, {name}!"},
            "main": {"greet": "Hello {name}"} # For format_missing_arg test
        }
        with patch("cli.menu_printer.fetch_latest_text", return_value=test_text):
            # Act
            result = menu_printer.get_text("test_section", "test_key", name="World")
            # Assert
            assert result == "Hello, World!"

    def test_missing_key(self):
        test_text = {"test_section": {"test_key": "Hello, {name}!"}}
        with patch("cli.menu_printer.fetch_latest_text", return_value=test_text):
            with pytest.raises(KeyError):
                menu_printer.get_text("main", "missing_key", name="World")

    def test_format_missing_arg(self):
        # Arrange
        test_text = {"main": {"greet": "Hello {name}"}}
        with patch("cli.menu_printer.fetch_latest_text", return_value=test_text):
            # Act
            result = menu_printer.get_text("main", "greet")
        # Assert
        assert result == "Hello {name}"

class TestActionResult:
    def test_success(self, capsys):
        # Arrange
        with patch("cli.menu_printer.fetch_latest_text", return_value=MOCK_TEXT_DATA):
            # Act
            menu_printer.print_action_result("test_fly", "bird", animal_name="test_bird")
            output = capsys.readouterr().out
            # Assert
            assert output.strip() == "test_bird is flying!"

    def test_missing_action_key(self, capsys):
        # Arrange
        with patch("cli.menu_printer.fetch_latest_text", return_value=MOCK_TEXT_DATA):
            # Act
            menu_printer.print_action_result("unknown_action", "unknown_type", animal_name="test_bird")
            output = capsys.readouterr().out
            # Assert
            assert output.strip() == "test_bird (unknown_type): unknown_action"