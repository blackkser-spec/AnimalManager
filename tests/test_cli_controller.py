import pytest
import CLI.menu_printer
from unittest.mock import MagicMock, patch
from CLI.cli_controller import CliController

@pytest.fixture
def mock_manager():
    return MagicMock()

@pytest.fixture
def cli_controller(mock_manager):
    """CliControllerのインスタンスを作成し、入力をモック化できるようにします。"""
    controller = CliController(mock_manager)
    controller.menu_printer = MagicMock()
    controller._get_raw_input = MagicMock()
    
    return controller


class TestInputHelpers:
    """入力用内部メソッド（_prompt_...）のバリデーションとループの挙動を検証"""
    def test_choice_retry_then_success(self, cli_controller):
        # Arrange
        choices = {"1": "VALID"}
        cli_controller._get_raw_input.side_effect = ["99", "1"]
        # Act
        result = cli_controller._prompt_for_choice("test", choices)
        # Assert
        assert result == "VALID"
        cli_controller.menu_printer.print_error.assert_called_once_with("無効な選択です")
        assert cli_controller.menu_printer.print_error.call_count == 1

    def test_choice_cancel(self, cli_controller):
        # Arrange
        cli_controller._get_raw_input.return_value = ""
        # Act
        result = cli_controller._prompt_for_choice("test", {"1": "V"}, cancel_msg="CANCELLED")
        # Assert
        assert result is None
        cli_controller.menu_printer.print_cancel.assert_called_with("CANCELLED")

    def test_input_cancel(self, cli_controller):
        # Arrange
        cli_controller._get_raw_input.return_value = ""
        # Act
        result = cli_controller._prompt_for_input("test", cancel_msg="CANCELLED")
        # Assert
        assert result is None
        cli_controller.menu_printer.print_cancel.assert_called_with("CANCELLED")

    def test_input_with_validator_error(self, cli_controller):
        # Arrange
        def mock_validator(val):
            if val == "bad": raise ValueError("Error Msg")
            return val
        cli_controller._get_raw_input.side_effect = ["bad", "good"]
        # Act
        result = cli_controller._prompt_for_input("test", validator=mock_validator)
        # Assert
        assert result == "good"
        cli_controller.menu_printer.print_error.assert_called_with("Error Msg")

    def test_input_no_cancel_retry(self, cli_controller):
        """allow_cancel=False の場合に空入力を許容せずリトライするか"""
        # Arrange
        cli_controller._get_raw_input.side_effect = ["", "valid_input"]
        # Act
        result = cli_controller._prompt_for_input("test", allow_cancel=False)
        # Assert
        assert result == "valid_input"
        cli_controller.menu_printer.print_error.assert_called_with("入力は必須です")

    def test_select_animal_id_flow_success(self, cli_controller, mock_manager):
        # Arrange: 1回目失敗(文字)、2回目失敗(存在しないID)、3回目成功
        mock_manager.get_animal.side_effect = [None, MagicMock()]
        cli_controller._get_raw_input.side_effect = ["abc", "999", "1"]
        # Act
        result = cli_controller._select_animal_id_flow("test prompt")
        # Assert
        assert result is not None
        assert cli_controller.menu_printer.print_error.call_count == 2

    def test_select_animal_type_flow_success(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.get_available_animal_types.return_value = ["cat", "dog"]
        cli_controller._get_raw_input.return_value = "cat"
        # Act
        result = cli_controller._select_animal_type_flow("prompt")
        # Assert
        assert result == "cat"

    def test_validate_selection_from_list_direct(self, cli_controller):
        """_validate_selection_from_list の境界値を直接検証"""
        # Arrange
        valid_list = ["apple", "banana"]
        # 正常系: index
        assert cli_controller._validate_selection_from_list("1", valid_list) == "apple"
        # 正常系: 文字列
        assert cli_controller._validate_selection_from_list("banana", valid_list) == "banana"
        # 異常系
        with pytest.raises(ValueError, match="無効な値です"):
            cli_controller._validate_selection_from_list("3", valid_list)
        with pytest.raises(ValueError, match="無効な値です"):
            cli_controller._validate_selection_from_list("orange", valid_list)


class TestValidators:    
    def test_validate_positive_int(self, cli_controller):
        # 正しい入力
        assert cli_controller._validate_positive_int("10") == 10
        # 負の数
        with pytest.raises(ValueError, match="1以上の数値を入力してください"):
            cli_controller._validate_positive_int("0")
        # 文字列
        with pytest.raises(ValueError):
            cli_controller._validate_positive_int("abc")

    def test_validate_animal_id(self, cli_controller, mock_manager):
        # 存在するID
        mock_manager.get_animal.return_value = MagicMock()
        assert cli_controller._validate_animal_id("1") == 1
        # 存在しないID
        mock_manager.get_animal.return_value = None
        with pytest.raises(ValueError, match="そのIDの動物は存在しません"):
            cli_controller._validate_animal_id("99")

    def test_validate_animal_type(self, cli_controller, mock_manager):
        mock_manager.get_available_animal_types.return_value = ["cat", "dog"]
        # インデックス入力
        assert cli_controller._validate_animal_type("1") == "cat"
        # 文字列入力
        assert cli_controller._validate_animal_type("dog") == "dog"
        # 無効な入力
        with pytest.raises(ValueError):
            cli_controller._validate_animal_type("bird")

    def test_validate_action(self, cli_controller):
        # 数字変換
        assert cli_controller._validate_action("1") == "voice"
        # 大文字文字変換
        assert cli_controller._validate_action("FLY") == "fly"
        # 例外入力
        with pytest.raises(ValueError, match="無効な選択です"):
            cli_controller._validate_action("jump")


class TestMenuFlows:
    @pytest.mark.parametrize("flow_method, printer_name", [
        ("manage_animal_flow", "print_manage_animal"),
        ("manage_list_flow", "print_manage_list"),
        ("main_menu", "print_menu"),
    ])
    def test_menu_cancel_and_exit(self, cli_controller, flow_method, printer_name):
        """main_menuの場合のみ終了処理が呼ばれるか"""
        # Arrange
        if flow_method == "main_menu":
            cli_controller._get_raw_input.side_effect = ["", "4"]
            cli_controller.exit_manager = MagicMock(return_value="EXIT")
        else:
            cli_controller._get_raw_input.return_value = ""
        # Act
        getattr(cli_controller, flow_method)()
        # Assert
        printer_mock = getattr(cli_controller.menu_printer, printer_name)
        if flow_method == "main_menu":
            assert printer_mock.call_count == 2
        else:
            assert printer_mock.call_count == 1

        if flow_method == "main_menu":
            cli_controller.exit_manager.assert_called_once()

    def test_main_menu_keyboard_interrupt(self, cli_controller):
        """KeyboardInterrupt 発生時に exit_manager が呼ばれるか"""
        # Arrange
        cli_controller.menu_printer.print_menu.side_effect = KeyboardInterrupt
        cli_controller.exit_manager = MagicMock()
        # Act
        cli_controller.main_menu()
        # Assert
        cli_controller.exit_manager.assert_called_once()

    def test_execute_menu_loop_control_flow(self, cli_controller):
        """_execute_menu_loop が EXIT や TO_MAIN を受け取った時に正しくリターンするか"""
        # Arrange
        mock_print = MagicMock()
        # 1回目は通常アクション、2回目は EXIT を返すアクション
        action_normal = MagicMock(return_value="TO_BACK")
        action_exit = MagicMock(return_value="EXIT")
        cli_controller._prompt_for_choice = MagicMock(side_effect=[action_normal, action_exit])
        
        # Act
        result = cli_controller._execute_menu_loop(mock_print, {}, "prompt")
        # Assert
        assert result == "EXIT"

    @pytest.mark.parametrize(
        "flow_method, choice, expected_sub_method", [
            ("manage_animal_flow", "1", "add_animal_flow"),
            ("manage_animal_flow", "3", "remove_animal_flow"),
            ("manage_list_flow", "1", "show_animal_list_flow"),
            ("manage_list_flow", "2", "sort_list_flow"),
            ("main_menu", "4", "exit_manager"),
        ])
    def test_dispatch(self, cli_controller, flow_method, choice, expected_sub_method):
        """各フローにおいて、正しい番号で正しいサブメソッドが呼ばれるか"""
        # Arrange
        assert hasattr(cli_controller, expected_sub_method)
        
        mock_return_value = "EXIT" if expected_sub_method == "exit_manager" else "TO_MAIN"
        mock_action = MagicMock(return_value=mock_return_value)
        setattr(cli_controller, expected_sub_method, mock_action)

        inputs = [choice]
        if flow_method == "main_menu" and choice != "4":
            inputs.append("4")

        cli_controller._get_raw_input.side_effect = inputs
        # Act
        getattr(cli_controller, flow_method)()
        # Assert
        mock_action.assert_called_once()    


class TestSearchAnimalFlows:
    @pytest.mark.parametrize("choice, attr", [
        ("1", "ID"),
        ("2", "種類"),
        ("3", "名前"),
        ("4", "特技"),
    ])
    def test_success(self, cli_controller, mock_manager, choice, attr):
        # Arrange
        mock_results = [MagicMock()]
        mock_manager.get_all_animals.return_value = []
        mock_manager.search_animal.return_value = mock_results
        cli_controller._get_raw_input.side_effect = [choice, "keyword"]
        # Act
        cli_controller.search_animal_flow()
        # Assert
        mock_manager.search_animal.assert_called_once_with(attr, "keyword")
        cli_controller.menu_printer.print_animal_list.assert_called_with(mock_results)

    def test_no_results(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.get_all_animals.return_value = []
        mock_manager.search_animal.return_value = []
        cli_controller._get_raw_input.side_effect = ["3", "NonExistent"]
        # Act
        cli_controller.search_animal_flow()
        # Assert
        cli_controller.menu_printer.print_error.assert_called_with("検索結果が見つかりませんでした")



class TestExitManager:
    def test_success(self, cli_controller):
        # Arrange
        cli_controller.manager.save_to_file = MagicMock()
        # Act
        result = cli_controller.exit_manager()
        # Assert
        assert result == "EXIT"
        cli_controller.manager.save_to_file.assert_called_once()
        cli_controller.menu_printer.print_success.assert_called_with("AnimalManagerを終了します")
    
    def test_failure(self, cli_controller):
        # Arrange
        cli_controller.manager.save_to_file.side_effect = IOError("データの保存に失敗しました")
        cli_controller.menu_printer.print_error = MagicMock()
        # Act & Assert
        with pytest.raises(IOError):
            cli_controller.exit_manager()
        cli_controller.manager.save_to_file.assert_called_once()
        cli_controller.menu_printer.print_error.assert_called_with("データの保存に失敗しました")
        cli_controller.menu_printer.print_success.assert_not_called()


class TestAddAnimalFlow:
    def test_success(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.get_available_animal_types.return_value = ["cat"]
        cli_controller._get_raw_input.side_effect = ["cat", "Tama"]
        # Act
        cli_controller.add_animal_flow()
        # Assert
        mock_manager.add_animal.assert_called_once_with("cat", "Tama")

    def test_failure(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.get_available_animal_types.return_value = ["cat"]
        mock_manager.add_animal.side_effect = ValueError("名前は20文字以内で入力してください")
        cli_controller._get_raw_input.side_effect = ["cat", "a" * 21]
        # Act
        cli_controller.add_animal_flow()
        # Assert
        cli_controller.menu_printer.print_error.assert_called_with("名前は20文字以内で入力してください")
        cli_controller.menu_printer.print_success.assert_not_called()

class TestAddRandomFlow:
    def test_success(self, cli_controller, mock_manager):
        # Arrange
        cli_controller._get_raw_input.return_value = "3"
        # Act
        cli_controller.add_random_flow()
        # Assert
        mock_manager.add_random_animal.assert_called_once_with(3)

    def test_failure(self, cli_controller, mock_manager):
        cli_controller._get_raw_input.side_effect = ["abc", ""]
        # Act
        cli_controller.add_random_flow()
        # Assert
        cli_controller.menu_printer.print_error.assert_called()
        cli_controller.menu_printer.print_success.assert_not_called()
        mock_manager.add_random_animal.assert_not_called()


class TestRemoveAnimalFlow:
    def test_success(self, cli_controller, mock_manager):
        # Arrange
        mock_animal = MagicMock()
        mock_animal.name = "Tama"
        
        mock_manager.get_all_animals.return_value = [mock_animal]
        mock_manager.get_animal.return_value = mock_animal  # バリデーション(存在チェック)をパスさせる
        mock_manager.remove_animal.return_value = mock_animal
        cli_controller._get_raw_input.return_value = "1"
        # Act
        cli_controller.remove_animal_flow()
        # Assert
        mock_manager.remove_animal.assert_called_once_with(1)
        cli_controller.menu_printer.print_success.assert_called_with("Tama を削除しました")

    def test_failure(self, cli_controller, mock_manager):
        # Arrange
        mock_animal = MagicMock()
        mock_manager.get_all_animals.return_value = [mock_animal]
        mock_manager.get_animal.return_value = mock_animal
        mock_manager.remove_animal.side_effect = ValueError("IDは数値で入力してください")
        cli_controller._get_raw_input.return_value = "99"
        # Act
        cli_controller.remove_animal_flow()
        # Assert
        cli_controller.menu_printer.print_error.assert_called_with("IDは数値で入力してください")
        cli_controller.menu_printer.print_success.assert_not_called()


class TestEditAnimalFlow:
    @pytest.mark.parametrize("menu_index, attr_key, new_value, expected_msg_part",[
        ("1", "type", "cat", "種類を cat"),
        ("2", "name", "NewName", "名前を NewName"),
        ("3", "ability", "fly", "特技を fly")
    ])
    def test_success(self, cli_controller, mock_manager, menu_index, attr_key, new_value, expected_msg_part):
        # Arrange
        mock_animal = MagicMock()
        mock_manager.get_all_animals.return_value = [mock_animal]
        mock_manager.get_animal.return_value = mock_animal
        mock_manager.edit_animal.return_value = mock_animal
        mock_manager.get_available_animal_types.return_value = ["cat"]
        mock_manager.get_available_abilities.return_value = ["fly"]
        cli_controller._get_raw_input.side_effect = ["1", menu_index, new_value]
        # Act
        cli_controller.edit_animal_attr_flow()
        # Assert
        mock_manager.edit_animal.assert_called_once_with(1, attr_key, new_value)
        acutual_msg = cli_controller.menu_printer.print_success.call_args.args[0]
        assert expected_msg_part in acutual_msg

    def test_failure(self, cli_controller, mock_manager):
        # Arrange
        mock_animal = MagicMock()
        mock_manager.get_all_animals.return_value = [mock_animal]
        mock_manager.get_animal.return_value = mock_animal
        mock_manager.edit_animal.side_effect = ValueError("名前は20文字以内で入力してください")
        cli_controller._get_raw_input.side_effect = ["1", "2", "a" * 21]
        # Act
        cli_controller.edit_animal_attr_flow()
        # Assert
        cli_controller.menu_printer.print_error.assert_called()


class TestActAnimalFlow:
    def test_success(self, cli_controller, mock_manager):
        # Arrange
        mock_animal = MagicMock()
        mock_manager.act_animal.return_value = [mock_animal]
        cli_controller._get_raw_input.return_value = "1"
        # Act
        cli_controller.act_animal_flow()
        # Assert
        mock_manager.act_animal.assert_called_once_with("voice")

    def test_failure(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.act_animal.side_effect = ValueError("無効な選択です")
        cli_controller._get_raw_input.side_effect = ["99",""]
        # Act
        cli_controller.act_animal_flow()
        # Assert
        cli_controller.menu_printer.print_error.assert_called_with("無効な選択です")


class TestShowAnimalListFlow:
    def test_success(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.get_all_animals.return_value = [MagicMock()]
        # Act
        cli_controller.show_animal_list_flow()
        # Assert
        mock_manager.get_all_animals.assert_called_once()
        cli_controller.menu_printer.print_animal_list.assert_called_once()

    def test_failure(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.get_all_animals.side_effect = ValueError
        # Act
        cli_controller.show_animal_list_flow()
        # Assert
        mock_manager.get_all_animals.assert_called_once()
        cli_controller.menu_printer.print_error.assert_called_once()


class TestSortListFlow:
    @pytest.mark.parametrize("sort_index, expected_category", [
        ("1", "id"),
        ("2", "type_en"),
        ("3", "name")
    ])
    def test_success(self, cli_controller, mock_manager, sort_index, expected_category):
        # Arrange
        mock_list = [MagicMock()]
        sorted_mock_list = [MagicMock()]
        mock_manager.get_all_animals.return_value = mock_list
        mock_manager.sort_list.return_value = sorted_mock_list
        cli_controller._get_raw_input.return_value = sort_index
        # Act
        cli_controller.sort_list_flow()
        # Assert
        mock_manager.get_all_animals.assert_called_once()
        mock_manager.sort_list.assert_called_once_with(mock_list, expected_category)
        cli_controller.menu_printer.print_animal_list.assert_called_once_with(sorted_mock_list)

    def test_failure(self, cli_controller, mock_manager):
        # Arrange
        mock_manager.sort_list.side_effect = ValueError
        cli_controller._get_raw_input.side_effect = ["99",""]
        # Act
        cli_controller.sort_list_flow()
        # Assert
        cli_controller.menu_printer.print_error.assert_called_once()


class TestClearDataFlow:
    def test_success(self, cli_controller, mock_manager):
        # Arrange
        cli_controller._get_raw_input.return_value = "yes"
        # Act
        result = cli_controller.clear_data_flow()
        # Assert
        assert result == "TO_MAIN"
        mock_manager.clear_data.assert_called_once()


class TestFlowCancellations:
    """各フローにおけるキャンセル処理（未入力による中断）をまとめて検証"""
    @pytest.mark.parametrize("flow_method, inputs, expected_return", [
        # 基本的な 1 ステップ目でのキャンセル
        ("add_animal_flow", [""], "TO_BACK"),
        ("add_random_flow", [""], "TO_BACK"),
        ("remove_animal_flow", [""], "TO_BACK"),
        ("edit_animal_attr_flow", [""], "TO_BACK"),
        ("act_animal_flow", [""], "TO_BACK"),
        ("sort_list_flow", [""], "TO_BACK"),
        ("search_animal_flow", [""], "TO_MAIN"),
        ("clear_data_flow", ["no"], "TO_BACK"),
        # 2 ステップ目以降でのキャンセル（深い階層からの復帰）
        ("add_animal_flow", ["cat", ""], "TO_BACK"),
        ("edit_animal_attr_flow", ["1", ""], "TO_BACK"),
        ("edit_animal_attr_flow", ["1", "1", ""], "TO_BACK"),
        ("search_animal_flow", ["1", "", ""], "TO_MAIN"),
    ])
    def test_all_cancel_scenarios(self, cli_controller, mock_manager, flow_method, inputs, expected_return):
        # Arrange: どのフローが呼ばれてもバリデーションを通るように最小限のモックを設定
        mock_animal = MagicMock(id=1)
        mock_animal.name = "Tama"
        mock_manager.get_all_animals.return_value = [mock_animal]
        mock_manager.get_animal.return_value = mock_animal
        mock_manager.get_available_animal_types.return_value = ["cat"]
        mock_manager.get_available_abilities.return_value = ["fly"]
        
        cli_controller._get_raw_input.side_effect = inputs
        # Act
        method = getattr(cli_controller, flow_method)
        result = method()
        # Assert
        assert result == expected_return
        assert cli_controller.menu_printer.print_cancel.called
        mock_manager.clear_data.assert_not_called()