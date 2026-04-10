import pytest
from unittest.mock import MagicMock, patch
from controller.local_backend import LocalBackend
from controller.dto import AnimalDTO # DTOが必要になる可能性があるので追加

@pytest.fixture
def mock_layout():
    return MagicMock()

@pytest.fixture
def mock_manager():
    return MagicMock()

@pytest.fixture
def local_backend(mock_layout, mock_manager):
    return LocalBackend(mock_layout, mock_manager)

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
        expected_error_msg = "ID:1 に該当する動物は存在しません"
        # Act & Assert
        mock_manager.remove_animal.side_effect = ValueError(expected_error_msg)
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_remove(animal_id)
        mock_manager.remove_animal.assert_called_once_with(animal_id)

class TestExecuteEdit:
    @pytest.mark.parametrize(
        "attr, new_value, expected_func",
        [
            ("type", "cat", "edit_animal_type"),
            ("name", "Tama", "edit_animal_name"),
            ("ability", "fly", "edit_animal_ability"),
        ]
    )
    def test_success(self, local_backend, mock_manager, attr, new_value, expected_manager_func):
        # Arrange
        animal_id = 1

        mock_manager.edit_animal_type.return_value = MagicMock(id=animal_id, type_en=new_value)
        mock_manager.edit_animal_name.return_value = MagicMock(id=animal_id, name=new_value)
        mock_manager.edit_animal_ability.return_value = MagicMock(id=animal_id, ex_ability={new_value: {}})
        # Act
        local_backend.execute_edit(animal_id, attr, new_value)
        # Assert
        expected_mock_method = getattr(mock_manager, expected_manager_func)
        expected_mock_method.assert_called_once_with(animal_id, new_value)

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
        getattr(mock_manager, f"edit_animal_{attr}").side_effect = ValueError(expected_error_msg)
        # Act & Assert
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_edit(animal_id, attr, new_value)
        
        getattr(mock_manager, f"edit_animal_{attr}").assert_called_once_with(animal_id, new_value)

    def test_failure_invalid_attr(self, local_backend, mock_manager):
        # Arrange
        animal_id = 1
        attr = "invalid_attr"
        new_value = "some_value"
        expected_error_msg = "無効な属性です"
        # Act & Assert
        with pytest.raises(ValueError, match=expected_error_msg):
            local_backend.execute_edit(animal_id, attr, new_value)
        
        mock_manager.edit_animal_type.assert_not_called()
        mock_manager.edit_animal_name.assert_not_called()
        mock_manager.edit_animal_ability.assert_not_called()
