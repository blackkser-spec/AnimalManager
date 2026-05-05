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
        mock_manager.load_from_file.side_effect = IOError("file not found")
        with pytest.raises(IOError, match="file not found"):
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
        # Act & Assert
        mock_manager.add_animal.side_effect = ValueError("Any error from manager")
        with pytest.raises(ValueError):
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
        # Act & Assert
        mock_manager.add_random_animal.side_effect = ValueError("Any error")
        with pytest.raises(ValueError):
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
        # Act & Assert
        mock_manager.remove_animal.side_effect = ValueError("ID not found")
        with pytest.raises(ValueError):
            local_backend.execute_remove(animal_id)
        mock_manager.remove_animal.assert_called_once_with(animal_id)


class TestExecuteEdit:
    @pytest.mark.parametrize(
        "attr, new_value",
        [
            ("animal_type", "cat"),
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
        "attr, new_value",
        [
            ("type", "invalid_type"),
            ("name", ""),
            ("ability", "invalid_ability"),
        ]
    )
    def test_failure_from_manager(self, local_backend, mock_manager, attr, new_value):
        # Arrange
        animal_id = 1
        mock_manager.edit_animal.side_effect = ValueError("Validation error")
        # Act & Assert
        with pytest.raises(ValueError):
            local_backend.execute_edit(animal_id, attr, new_value)

    def test_failure_invalid_attr(self, local_backend, mock_manager):
        # Arrange
        animal_id = 1
        attr = "invalid_attr"
        new_value = "some_value"
        mock_manager.edit_animal.side_effect = ValueError("Invalid attr")
        # Act & Assert
        with pytest.raises(ValueError):
            local_backend.execute_edit(animal_id, attr, new_value)
        
        mock_manager.edit_animal.assert_called_once_with(animal_id, attr, new_value)


class TestExecuteAct:
    def test_success(self, local_backend, mock_manager):
        # Arrange
        action_name = "voice"
        animal_mock = MagicMock()
        animal_mock.name = "Tama"
        animal_mock.animal_type = "cat"
        
        mock_manager.act_animal.return_value = [
            {"animal": animal_mock, "action_key": "sound"}
        ]
        # Act
        results = local_backend.execute_act(action_name)
        # Assert
        mock_manager.act_animal.assert_called_once_with(action_name)
        # Backendが変換したDTO形式のリストを検証
        assert results == [{"name": "Tama", "animal_type": "cat", "action_key": "sound"}]

    def test_failure(self, local_backend, mock_manager):
        # Arrange        
        action_name = "invalid_action"
        mock_manager.act_animal.side_effect = ValueError("Invalid")
        # Act & Assert
        with pytest.raises(ValueError):
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
        attribute = "name"
        keyword = "tama"
        animal = MagicMock(id=1, animal_type="cat")
        animal.name = "Tama"
        animal.get_all_ability.return_value = {}
        mock_manager.search_animal.return_value = [animal]

        expected_dto = AnimalDTO(id=1, name="Tama", animal_type="cat", abilities=[])
        # Act
        results = local_backend.execute_search(attribute, keyword)
        # Assert
        mock_manager.search_animal.assert_called_once_with("name", "tama")
        assert results == [expected_dto]

    def test_failure(self, local_backend, mock_manager):
        # Arrange
        attribute = "invalid_attribute"
        keyword = "some_keyword"
        mock_manager.search_animal.side_effect = ValueError("Invalid attr")
        # Act & Assert
        with pytest.raises(ValueError):
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
        assert result is True
    
    def test_failure(self, local_backend, mock_manager):
        # Arrange
        mock_manager.save_to_file.side_effect = IOError("Save failed")
        # Act & Assert
        with pytest.raises(IOError):
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
        mock_manager.save_to_file.side_effect = IOError()
        # Act & Assert
        with pytest.raises(IOError):
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