import pytest
from unittest.mock import MagicMock, patch
from controller.controller import Controller
from controller.dto import AnimalDTO

@pytest.fixture
def mock_layout():
    layout = MagicMock()
    layout.tree_animals = MagicMock()
    layout.search_attr = MagicMock()
    layout.search_entry = MagicMock()
    return layout

@pytest.fixture
def mock_manager():
    return MagicMock()

@pytest.fixture
def controller(mock_layout, mock_manager):
    with patch('controller.local_backend.LocalBackend'), \
         patch('controller.remote_backend.RemoteBackend'):
        mock_layout.use_mode = "local"
        ctrl = Controller(mock_layout, mock_manager)
        # テストでBackendの呼び出しを検証するため、Mockに差し替える
        ctrl.backend = MagicMock()
        return ctrl
    

class TestInitialization:
    def test_controller_initialization(self, mock_layout, mock_manager):
        """モードに応じて適切なBackendが選択されるか"""
        with patch('controller.local_backend.LocalBackend') as mock_local, \
             patch('controller.remote_backend.RemoteBackend') as mock_remote:
            
            mock_layout.use_mode = "local"
            Controller(mock_layout, mock_manager)
            mock_local.assert_called_once()
            
            mock_layout.use_mode = "remote"
            Controller(mock_layout, mock_manager)
            mock_remote.assert_called_once()


class TestNavigation:
    @pytest.mark.parametrize("method_name, layout_method", [
        ("add", "open_add_dialog"),
        ("add_random", "open_random_dialog"),
        ("act", "open_act_dialog"),
    ])
    def test_common_dialog_opening(self, controller, mock_layout, method_name, layout_method):
        """引数なしでダイアログを開く単純なナビゲーションをまとめて検証"""
        getattr(controller, method_name)()
        getattr(mock_layout, layout_method).assert_called_once()


class TestAdd:
    def test_execute_add_success(self, controller, mock_layout):
        # Arrange
        mock_layout.add_window = MagicMock()
        # Act
        controller.execute_add("cat", "Tama")
        # Assert
        controller.backend.execute_add.assert_called_once_with("cat", "Tama")
        # UIの更新系メソッドが呼ばれているか
        mock_layout.refresh_list.assert_called_once()
        mock_layout.add_window.destroy.assert_called_once()
        mock_layout.log.assert_called_with("cat Tama を追加しました")

    def test_execute_add_failure(self, controller, mock_layout):
        # Arrange
        mock_layout.add_window = MagicMock()
        controller.backend.execute_add.side_effect = Exception("通信エラー発生")
        # Act
        controller.execute_add("cat", "Tama")
        # Assert
        mock_layout.log.assert_called_with("通信エラー発生")
        mock_layout.refresh_list.assert_not_called()
        mock_layout.add_window.destroy.assert_not_called()

    def test_execute_add_random_success(self, controller, mock_layout):
        # Arrange
        mock_layout.random_window = MagicMock()
        controller.backend.execute_add_random.return_value = True
        # Act
        controller.execute_add_random(3)
        # Assert
        controller.backend.execute_add_random.assert_called_once_with(3)
        mock_layout.refresh_list.assert_called_once()
        mock_layout.log.assert_called_with("3 回のランダム追加に成功しました")


class TestRemove:
    def test_remove_no_selection(self, controller, mock_layout):
        """何も選択されていない場合に警告ログが出るか"""
        # Arrange
        mock_layout.tree_animals.selection.return_value = []
        # Act
        controller.remove()
        # Assert
        mock_layout.log.assert_called_once_with("対象を選択してください")
        controller.backend.execute_remove.assert_not_called()

    def test_remove_selected_items(self, controller, mock_layout):
        # Arrange
        tree_data = {
            "item_key_1": {"values": [10, "猫", "Pochi"]},
            "item_key_2": {"values": [20, "犬", "Tama"]}
        }
        mock_layout.tree_animals.selection.return_value = list(tree_data.keys())
        mock_layout.tree_animals.item.side_effect = lambda item_id: tree_data[item_id]
        # Act
        controller.backend.execute_remove.side_effect = [
            {"id": 10, "name": "Pochi"}, {"id": 20, "name": "Tama"}
        ]
        controller.remove()
        # Assert Backendが2回呼ばれたか
        assert controller.backend.execute_remove.call_count == 2
        mock_layout.log.assert_any_call("削除完了: ID:10 Pochi")
        mock_layout.log.assert_any_call("削除完了: ID:20 Tama")


class TestEdit:
    def test_edit_no_selection(self, controller, mock_layout):
        """編集対象が選択されていない場合"""
        mock_layout.tree_animals.selection.return_value = []
        controller.edit()
        mock_layout.log.assert_called_once_with("対象を選択してください")
        mock_layout.open_edit_dialog.assert_not_called()

    def test_edit_dialog_open(self, controller, mock_layout):
        """選択されている場合に編集ダイアログが開くか"""
        # Arrange
        mock_layout.tree_animals.selection.return_value = ["item1"]
        mock_layout.tree_animals.item.return_value = {"values": [1]}
        # Act
        controller.edit()
        # Assert
        mock_layout.open_edit_dialog.assert_called_once_with(1)

    def test_execute_edit_success(self, controller, mock_layout):
        # Arrange
        mock_layout.edit_window = MagicMock()
        mock_layout.edit_target_id = 1
        mock_layout.edit_target.get.return_value = "名前の変更"
        mock_layout.name_entry.get.return_value = "Tama"
        # Act
        controller.execute_edit()
        # Assert
        controller.backend.execute_edit.assert_called_once_with(1, "name", "Tama")
        mock_layout.log.assert_called_once_with("編集完了")
        mock_layout.refresh_list.assert_called_once()
        mock_layout.edit_window.destroy.assert_called_once()

    def test_execute_edit_invalid_choice(self, controller, mock_layout):
        """無効な編集項目が選択された場合のバリデーション"""
        # Arrange
        mock_layout.edit_target.get.return_value = "無効な項目"
        # Act
        controller.execute_edit()
        # Assert
        mock_layout.log.assert_called_once_with("編集項目を選択してください")
        controller.backend.execute_edit.assert_not_called()


class TestAction:
    def test_execute_act_success(self, controller, mock_layout):
        # Arrange
        mock_layout.act_window = MagicMock()
        controller.backend.is_valid_action.return_value = True
        controller.backend.execute_act.return_value = ["わんわん", "走った"]
        # Act
        controller.execute_act("voice")
        # Assert
        controller.backend.execute_act.assert_called_once_with("voice")
        mock_layout.log.assert_any_call("わんわん")
        mock_layout.log.assert_any_call("走った")
        mock_layout.act_window.destroy.assert_called_once()

    def test_execute_act_invalid(self, controller, mock_layout):
        """不正な行動が選択された場合のバリデーション"""
        # Arrange
        controller.backend.is_valid_action.return_value = False
        # Act
        controller.execute_act("unknown_action")
        # Assert
        mock_layout.log.assert_called_once_with("不正な行動です")
        controller.backend.execute_act.assert_not_called()


class TestSearchAndSort:
    def test_search_integration(self, controller, mock_layout):
        """検索UIの値を取得し、Backendの結果をリストに反映させるか"""
        # Arrange
        mock_layout.search_attr.get.return_value = "名前"
        mock_layout.search_entry.get.return_value = "Tama"
        mock_results = [
            AnimalDTO(id=1, name="Tama", type_en="cat", type_jp="猫", abilities=[]),
            AnimalDTO(id=2, name="Tama2", type_en="dog", type_jp="犬", abilities=["fly"])
        ]
        controller.backend.execute_search.return_value = mock_results
        # Act
        controller.search()
        # Assert
        controller.backend.execute_search.assert_called_once_with("名前", "Tama")
        mock_layout.refresh_list.assert_called_once_with(mock_results)

    def test_clear_search(self, controller, mock_layout):
        # Arrange
        mock_layout.search_entry.delete.return_value = None
        # Act
        controller.clear_search()
        # Assert
        mock_layout.search_entry.delete.assert_called_once()
        mock_layout.refresh_list.assert_called_once()

    @pytest.mark.parametrize(
        "sort_column, initial_last_sort_col, initial_sort_desc, expected_ids",[
            ("name", "id", False, [1, 2]),
            ("id", "name", False, [1, 2]),
            ("id", "id", False, [2, 1]),
            ("id", "id", True, [1, 2]),]
    )
    def test_sort_tree_behavior(
        self, controller, mock_layout, sort_column, initial_last_sort_col, initial_sort_desc, expected_ids
    ):
        """Controllerのsort_treeメソッドが、指定されたカラムで昇降順にソートされるか"""
        # Arrange
        mock_layout.search_attr.get.return_value = "すべて"
        mock_layout.search_entry.get.return_value = ""
        mock_results = [
            AnimalDTO(id=2, name="B", type_en="dog", type_jp="犬", abilities=[]),
            AnimalDTO(id=1, name="A", type_en="cat", type_jp="猫", abilities=[])
        ]
        controller.backend.execute_search.return_value = mock_results
        controller.last_sort_col = initial_last_sort_col
        controller.sort_desc = initial_sort_desc
        # Act
        controller.sort_tree(sort_column)
        # Assert
        mock_layout.refresh_list.assert_called_once()
        sorted_animals = mock_layout.refresh_list.call_args.args[0]
        
        actual_ids = [animal.id for animal in sorted_animals]
        assert actual_ids == expected_ids
        # 念のため、ソート後のControllerの状態も確認
        assert controller.last_sort_col == sort_column
        if initial_last_sort_col == sort_column:
            assert controller.sort_desc == (not initial_sort_desc)
        else:
            assert controller.sort_desc == False


class TestDataManagement:
    def test_load_success(self, controller, mock_layout):
        # Arrange
        mock_layout.log.return_value = None
        controller.backend.execute_load.return_value = True
        # Act
        controller.load()
        # Assert
        controller.backend.execute_load.assert_called_once()
        mock_layout.refresh_list.assert_called_once()

    def test_load_failure(self, controller, mock_layout):
        # Arrange
        mock_layout.log.return_value = None
        controller.backend.execute_load.side_effect = Exception
        # Act
        controller.load()
        # Assert
        controller.backend.execute_load.assert_called_once()
        mock_layout.log.assert_called_once()

    def test_save_success(self, controller, mock_layout):
        # Arrange
        mock_layout.log.return_value = None
        controller.backend.save.return_value = "データを保存しました"
        # Act
        controller.save()
        # Assert
        controller.backend.save.assert_called_once()
        mock_layout.log.assert_called_once_with("データを保存しました")
        mock_layout.refresh_list.assert_called_once()

    def test_save_failure(self, controller, mock_layout):
        # Arrange
        mock_layout.log.return_value = None
        controller.backend.save.side_effect = ValueError("保存データの形式が正しくありません")
        # Act
        controller.save()
        # Assert
        controller.backend.save.assert_called_once()
        mock_layout.log.assert_called_once_with("保存データの形式が正しくありません")
        mock_layout.refresh_list.assert_not_called()

    def test_data_clear(self, controller, mock_layout):
        # Arrange
        mock_layout.log.return_value = None
        # Act
        with patch('controller.controller.messagebox.askyesno', return_value=True):
            controller.data_clear()
        # Assert
        controller.backend.data_clear.assert_called_once()
        mock_layout.log.assert_called_once_with("データを消去しました")
        mock_layout.refresh_list.assert_called_once()
    
    def test_data_clear_abort(self, controller, mock_layout):
        # Arrange
        mock_layout.log.return_value = None
        # Act
        with patch('controller.controller.messagebox.askyesno', return_value=False):
            controller.data_clear()
        # Assert
        controller.backend.data_clear.assert_not_called()
        mock_layout.log.assert_called_once_with("データ消去をキャンセルしました")
        mock_layout.refresh_list.assert_not_called()

    def test_on_close_with_save(self, controller, mock_layout):
        # Arrange
        controller.backend.has_unsaved_changes.return_value = True
        # Act
        with patch('controller.controller.messagebox.askyesnocancel', return_value=True):
            controller.on_close()
        # Assert
        controller.backend.save.assert_called_once()
        mock_layout.root.destroy.assert_called_once()

    def test_on_close_discard_changes(self, controller, mock_layout):
        # Arrange
        controller.backend.has_unsaved_changes.return_value = True
        # Act
        with patch('controller.controller.messagebox.askyesnocancel', return_value=False):
            controller.on_close()
        # Assert
        controller.backend.save.assert_not_called()
        mock_layout.root.destroy.assert_called_once()

    def test_on_close_cancel_abort(self, controller, mock_layout):
        # Arange
        controller.backend.has_unsaved_changes.return_value = True
        # Act
        with patch('controller.controller.messagebox.askyesnocancel', return_value=None):
            controller.on_close()
        # Assert: 破棄メソッドが呼ばれないことを確認
        mock_layout.root.destroy.assert_not_called()

    def test_on_close_no_changes(self, controller, mock_layout):
        """変更なし -> そのまま閉じる"""
        # Arange
        controller.backend.has_unsaved_changes.return_value = False
        # Act
        controller.on_close()
        # Assert
        mock_layout.root.destroy.assert_called_once()