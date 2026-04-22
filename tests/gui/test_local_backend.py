import pytest
from unittest.mock import MagicMock
from controller.local_backend import LocalBackend
from controller.dto import AnimalDTO

@pytest.fixture
def mock_layout():
    return MagicMock()

@pytest.fixture
def mock_manager():
    return MagicMock()

@pytest.fixture
def local_backend(mock_layout, mock_manager):
    return LocalBackend(mock_layout, mock_manager)

class TestInitialization:
    def test_init_calls_load(self, mock_layout, mock_manager):
        # 初期化時に読み込みが呼ばれることを確認
        LocalBackend(mock_layout, mock_manager)
        mock_manager.load_from_file.assert_called_once()

    def test_init_failure(self, mock_layout, mock_manager):
        # 初期化時のIOエラーが伝播するか確認
        mock_manager.load_from_file.side_effect = IOError("ファイルがありません")
        with pytest.raises(IOError, match="ファイルがありません"):
            LocalBackend(mock_layout, mock_manager)


class TestExecuteAdd:
    def test_success(self, local_backend, mock_manager):
        # Arrange
        animal_type = "cat"
        name = "Tama"
        # Act
        local_backend.execute_add(animal_type, name)
        # Assert
        mock_manager.add_animal.assert_called_once_with(animal_type, name)

    def test_failure(self, local_backend, mock_manager):
        # Arrange
        animal_type = "cat"
        name = ""
        expected_error_msg = "名前を空白にはできません"
        # Act & Assert
        mock_manager.add_animal.side_effect = ValueError(expected_error_msg)
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_add(animal_type, name)
        
        mock_manager.add_animal.assert_called_once_with(animal_type, name)


class TestExecuteAddRandom:
    def test_success(self, local_backend, mock_manager):
        # Arrange
        count = 5
        # Act
        local_backend.execute_add_random(count)
        # Assert
        mock_manager.add_random_animal.assert_called_once_with(count)
    
    def test_failure(self, local_backend, mock_manager):
        # Arrange
        count = -1
        expected_error_msg = "追加回数は1以上を指定してください"
        # Act & Assert
        mock_manager.add_random_animal.side_effect = ValueError(expected_error_msg)
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_add_random(count)
        mock_manager.add_random_animal.assert_called_once_with(count)


class TestExecuteRemove:
    def test_success(self, local_backend, mock_manager):
        # Arrange
        animal_id = 1
        removed_animal_mock = MagicMock()
        removed_animal_mock.id = animal_id
        removed_animal_mock.name = "TestRemovedAnimal"
        mock_manager.remove_animal.return_value = removed_animal_mock
        # Act
        result = local_backend.execute_remove(animal_id)
        # Assert
        mock_manager.remove_animal.assert_called_once_with(animal_id)
        assert result == {"id": animal_id, "name": "TestRemovedAnimal"}
    
    def test_failure(self, local_backend, mock_manager):
        # Arrange
        animal_id = 1
        expected_error_msg = f"ID:{animal_id} に該当する動物は存在しません"
        # Act & Assert
        mock_manager.remove_animal.side_effect = ValueError(expected_error_msg)
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_remove(animal_id)
        mock_manager.remove_animal.assert_called_once_with(animal_id)


class TestExecuteEdit:
    @pytest.mark.parametrize(
        "attr, new_value",
        [
            ("type", "cat"),
            ("name", "Tama"),
            ("ability", "fly"),
        ]
    )
    def test_success(self, local_backend, mock_manager, attr, new_value):
        # Arrange
        animal_id = 1
        # Act
        local_backend.execute_edit(animal_id, attr, new_value)
        # Assert
        mock_manager.edit_animal.assert_called_once_with(animal_id, attr, new_value)

    @pytest.mark.parametrize(
        "attr, new_value, expected_error_msg",
        [
            ("type", "invalid_type", "無効な種類の動物です"),
            ("name", "", "名前は空白にできません"),
            ("ability", "invalid_ability", "無効な特技です"),
        ]
    )
    def test_failure_from_manager(self, local_backend, mock_manager, attr, new_value, expected_error_msg):
        # Arrange
        animal_id = 1
        mock_manager.edit_animal.side_effect = ValueError(expected_error_msg)
        # Act & Assert
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_edit(animal_id, attr, new_value)

    def test_failure_invalid_attr(self, local_backend, mock_manager):
        # Arrange
        animal_id = 1
        attr = "invalid_attr"
        new_value = "some_value"
        expected_error_msg = "無効な属性です"
        mock_manager.edit_animal.side_effect = ValueError(expected_error_msg)
        # Act & Assert
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_edit(animal_id, attr, new_value)
        
        mock_manager.edit_animal.assert_called_once_with(animal_id, attr, new_value)


class TestExecuteAct:
    def test_success(self, local_backend, mock_manager):
        # Arrange
        action_name = "voice"
        expected_results = ["ニャアと鳴いた", "ワンワンと吠えた"]
        mock_manager.act_animal.return_value = expected_results
        # Act
        results = local_backend.execute_act(action_name)
        # Assert
        mock_manager.act_animal.assert_called_once_with(action_name)
        assert results == expected_results

    def test_failure(self, local_backend, mock_manager):
        # Arrange        
        action_name = "invalid_action"
        expected_msg = "無効なアクションです"
        mock_manager.act_animal.side_effect = ValueError(expected_msg)
        # Act & Assert
        with pytest.raises(ValueError, match = expected_msg):
            local_backend.execute_act(action_name)


class TestIsValidAction:
    @pytest.mark.parametrize("action, expected", [
        ("voice", True),
        ("fly", True),
        ("invalid", False),
    ])
    def test_is_valid_action(self, local_backend, mock_manager, action, expected):
        # Arrange
        mock_manager.ALLOWED_ACTIONS = {"voice", "fly", "swim"}
        # Act & Assert
        assert local_backend.is_valid_action(action) == expected


class TestExecuteSearch:
    def test_success(self, local_backend, mock_manager):
        # Arrange
        attribute = "名前"
        keyword = "tama"
        animal = MagicMock(id=1,type_en="cat", type_jp="猫")
        animal.name = "Tama"
        animal.get_all_ability.return_value = {}
        mock_manager.search_animal.return_value = [animal]

        expected_dto = AnimalDTO(id=1, name="Tama", type_en="cat", type_jp="猫", abilities=[])
        # Act
        results = local_backend.execute_search(attribute, keyword)
        # Assert
        mock_manager.search_animal.assert_called_once_with("名前", "tama")
        assert results == [expected_dto]

    def test_failure(self, local_backend, mock_manager):
        # Arrange
        attribute = "invalid_attribute"
        keyword = "some_keyword"
        expected_error_msg = "無効な検索属性です"
        mock_manager.search_animal.side_effect = ValueError(expected_error_msg)
        # Act & Assert
        with pytest.raises(ValueError, match = expected_error_msg):
            local_backend.execute_search(attribute, keyword)

class TestExecuteLoad:
    def test_success(self, local_backend, mock_manager):
        # Arrange
        mock_manager.get_all_animals.return_value = []
        # Act
        result = local_backend.execute_load()
        # Assert
        mock_manager.get_all_animals.assert_called_once()
        assert isinstance(result, list)


class TestSave:
    def test_success(self, local_backend, mock_manager):
        # Act
        result = local_backend.save()
        # Assert
        mock_manager.save_to_file.assert_called_once()
        assert result == "ローカルデータを保存しました"
    
    def test_failure(self, local_backend, mock_manager):
        # Arrange
        error_msg = "データの保存に失敗しました"
        mock_manager.save_to_file.side_effect = IOError(error_msg)
        # Act & Assert
        with pytest.raises(IOError, match=error_msg):
            local_backend.save()
        mock_manager.save_to_file.assert_called_once()


class TestDataClear:
    def test_success(self, local_backend, mock_manager):
        # Act
        local_backend.clear_data()
        # Assert
        mock_manager.clear_data.assert_called_once()
        mock_manager.save_to_file.assert_called_once()
    
    def test_failure(self, local_backend, mock_manager):
        # Arrange
        error_msg = "データの保存に失敗しました"
        mock_manager.save_to_file.side_effect = IOError(error_msg)
        # Act & Assert
        with pytest.raises(IOError, match=error_msg):
            local_backend.clear_data()

        mock_manager.clear_data.assert_called_once()
        mock_manager.save_to_file.assert_called_once()
        

class TestHasUnsavedChanges:
    @pytest.mark.parametrize("is_changed", [True, False])
    def test_has_unsaved_changes(self, local_backend, mock_manager, is_changed):
        # Arrange
        mock_manager.is_changed.return_value = is_changed
        # Act
        result = local_backend.has_unsaved_changes()
        # Assert
        mock_manager.is_changed.assert_called_once()
        assert result == is_changed