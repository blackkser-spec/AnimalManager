import json
import pytest
import copy
from core.animal_repository import AnimalRepository

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
        with pytest.raises(ValueError, match="保存データの形式が正しくありません"):
            repo.save(invalid_data)

    def test_os_error(self, tmp_path, valid_data, monkeypatch):
        # Arrange
        file = tmp_path / "test.json"
        repo = AnimalRepository(file)
        # Errorを発生させるダミー関数を定義
        def mock_open(*args, **kwargs):
            raise OSError

        monkeypatch.setattr("builtins.open", mock_open)

        # Act & Assert
        with pytest.raises(IOError):
            repo.save(valid_data)
        assert not file.exists()  # 失敗した時はファイルが作られていないことを確認


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

    def test_json_broken(self, tmp_path):
        # Arrange
        file = tmp_path / "test.json"
        repo = AnimalRepository(file)
        # broken json
        with open(file, "w", encoding="UTF-8") as f:
            f.write("broken json")
        # Act & Assert
        with pytest.raises(ValueError) as e:
            repo.load()

        broken_file = tmp_path / "test_broken.json"
        assert broken_file.exists()
        assert "データファイル破損のため" in str(e.value)
    
    def test_validation_error(self, tmp_path, valid_data):
        # Arrange
        file = tmp_path / "test.json"
        invalid_data = copy.deepcopy(valid_data)
        invalid_data["id_counter"] = "unknown"
        repo = AnimalRepository(file)

        with open(file, "w", encoding="UTF-8") as f:
            json.dump(invalid_data, f)
        # Act & Assert
        with pytest.raises(ValueError) as e:
            repo.load()

        broken_file = tmp_path / "test_broken.json"
        assert broken_file.exists()
        assert "データの不整合" in str(e.value)