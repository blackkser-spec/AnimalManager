import json
import pytest
import copy
from unittest.mock import patch
from core.animal_repository import AnimalRepository
from core.exceptions import SaveError, LoadError

# testで使用する仮Animalデータ
@pytest.fixture
def valid_data():
    return{
        "id_counter": 2,
        "naming_count": {"cat": 1},
        "animals": [
            {"id": 1, "name": "Tama", "type_en": "cat", "type_jp": "猫", "ex_ability": {}}]
    }


class TestSave:
    def test_success(self, tmp_path, valid_data):
        # Arrange
        file = tmp_path / "test.json"
        repo = AnimalRepository(file)
        # Act
        repo.save(valid_data)
        # Assert
        assert file.exists()
        
        with open(file, encoding="UTF-8") as f:
            saved = json.load(f)
        assert saved == valid_data

    def test_validation_error(self, tmp_path, valid_data):
        # Arrange
        file = tmp_path / "test.json"
        repo = AnimalRepository(file)
        
        invalid_data = copy.deepcopy(valid_data)
        invalid_data["id_counter"] = "invalid_type"
        # Act & Assert: Pydanticのバリデーション失敗を期待
        with pytest.raises(SaveError) as e:
            repo.save(invalid_data)
        assert e.value.key == "invalid_save_data"
        assert not file.exists()

    def test_os_error(self, tmp_path, valid_data):
        # Arrange
        file = tmp_path / "test.json"
        repo = AnimalRepository(file)
        with patch("builtins.open", side_effect=OSError):
            # Act & Assert
            with pytest.raises(SaveError) as e:
                repo.save(valid_data)

        assert e.value.key == "save_error"
        assert not file.exists() 


class TestLoad:
    def test_success(self, tmp_path, valid_data):
        # Arrange
        file = tmp_path / "test.json"
        repo = AnimalRepository(file)
        with open(file, "w", encoding="UTF-8") as f:
            json.dump(valid_data, f)
        # Act
        result = repo.load()
        # Assert
        assert result == valid_data

    def test_file_not_found(self, tmp_path):
        # Arrange
        file = tmp_path / "not_found.json"
        repo = AnimalRepository(file)
        # Act & Assert
        assert repo.load() is None

    def test_os_error(self, tmp_path):
        # Arrange
        file = tmp_path / "test.json"
        file.write_text("{}", encoding="UTF-8")
        repo = AnimalRepository(file)

        with patch("builtins.open", side_effect=OSError):
            # Act & Assert
            with pytest.raises(LoadError) as e:
                repo.load()

        assert e.value.key == "load_error"

    def test_json_broken(self, tmp_path):
        # Arrange
        file = tmp_path / "test.json"
        repo = AnimalRepository(file)
        # broken json
        with open(file, "w", encoding="UTF-8") as f:
            f.write("broken json")
        # Act & Assert
        with pytest.raises(LoadError) as e:
            repo.load()
        assert e.value.key == "file_broken_moved"
        
        broken_file = tmp_path / "test_broken.json"
        assert not file.exists()
        assert broken_file.exists()
    
    def test_validation_error(self, tmp_path, valid_data):
        # Arrange
        file = tmp_path / "test.json"
        invalid_data = copy.deepcopy(valid_data)
        invalid_data["id_counter"] = "unknown"
        repo = AnimalRepository(file)

        with open(file, "w", encoding="UTF-8") as f:
            json.dump(invalid_data, f)
        # Act & Assert
        with pytest.raises(LoadError) as e:
            repo.load()
        assert e.value.key == "file_broken_moved"
        
        broken_file = tmp_path / "test_broken.json"
        assert not file.exists()
        assert broken_file.exists()