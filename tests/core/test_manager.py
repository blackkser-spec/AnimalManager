import pytest
from unittest.mock import MagicMock, patch
from core.manager import AnimalManager
from core.animal_repository import AnimalRepository
from core.exceptions import ValidationError, AnimalNotFoundError, SaveError


@pytest.fixture
def mock_repository():
    """    実際のファイル操作を行わないためのダミーのリポジトリを提供します。    """
    return MagicMock()

@pytest.fixture
def manager(mock_repository):
    """    テストごとに初期化されたAnimalManagerのインスタンスを提供します。    """
    return AnimalManager(mock_repository)


class TestAddAnimal:
    @pytest.mark.parametrize("animal_type, name", [
        ("cat", "add_Cat"),
        ("dog", "add_Dog"),
        ("duck", "add_Duck"),
    ])
    def test_success(self, manager, animal_type, name):
        # Act
        animal = manager.add_animal(animal_type, name)
        # Assert
        assert animal.type_en == animal_type
        assert animal.name == name
        assert animal.id in manager.animals
        assert len(manager.animals) == 1

    @pytest.mark.parametrize("animal_type, name, expected_error", [
        ("unknown", "add_Cat", "invalid_animal_type"),
        ("cat", "a" * 21, "name_too_long"),
        ("cat", "", "name_empty"),
        ("cat", "   ", "name_empty"),
    ])
    def test_failure(self, manager, animal_type, name, expected_error):
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.add_animal(animal_type, name)
        assert e.value.key == expected_error

    def test_extreme_name(self, manager):
        """サロゲートペア（絵文字など）の扱い"""
        # Act
        name = "🐱" * 20
        animal = manager.add_animal("cat", name)
        # Assert
        assert animal.name == name

class TestAddRandomAnimal:
    def test_success(self, manager):
        # Act
        result = manager.add_random_animal(3)
        # Assert
        assert len(result) == 3

    @pytest.mark.parametrize("count",[-1, 0])
    def test_failure_invalid_range(self, manager, count):
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.add_random_animal(count)
        assert e.value.key == "require_positive_int"

    @pytest.mark.parametrize("count", [0.1, "a"])
    def test_failure_invalid_type(self, manager, count):
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.add_random_animal(count)
        assert e.value.key == "require_int"

class TestGetAnimal:
    def test_success(self, manager):
        # Arrange
        original = manager.add_animal("bird","get_Bird")
        # Act
        result = manager.get_animal(original.id)
        # Assert
        assert result.type_jp == "鳥"
        assert result.name == "get_Bird"

    def test_failure(self, manager):
        # Act & Assert
        with pytest.raises(AnimalNotFoundError):
            manager.get_animal(999)


class TestGetAnimals:
    def test_success(self, manager):
        # Arrange
        manager.add_random_animal(5)
        # Act
        animals = manager.get_all_animals()
        # Assert
        assert len(animals) == 5


class TestRemoveAnimal:
    def test_success(self, manager):
        # Arrange
        animal = manager.add_animal("cat", "remove_Cat")
        # Act
        manager.remove_animal(animal.id)
        # Assert
        assert len(manager.animals) == 0

    def test_failure(self, manager):
        with pytest.raises(AnimalNotFoundError):
            manager.remove_animal(999)


class TestEditAnimal:
    @pytest.mark.parametrize("attr, target_method", [
        ("type", "_edit_animal_type"),
        ("name", "_edit_animal_name"),
        ("ability", "_edit_animal_ability"),
    ])
    def test_dispatch_success(self, manager, attr, target_method):
        # Arrange
        animal = manager.add_animal("cat", "test")
        # Act & Assert
        with patch.object(AnimalManager, target_method) as mock_method:
            manager.edit_animal(animal.id, attr, "new_value")
            mock_method.assert_called_once_with(animal.id, "new_value")

    def test_dispatch_failure(self, manager):
        # Arrange
        animal = manager.add_animal("cat", "test")
        # Act
        with patch.object(AnimalManager, "_edit_animal_type") as mock_method:
            with pytest.raises(ValidationError) as e:
                manager.edit_animal(animal.id, "unknown", "new_value")
            assert e.value.key == "invalid_attribute"
            mock_method.assert_not_called()

    def test_edit_type_success(self, manager):
        # Arrange
        original = manager.add_animal("bird","edit_Bird")
        # Act
        edited = manager.edit_animal(original.id, "type", "cat")
        # Assert
        assert edited is not original
        assert edited.id == original.id
        assert manager.get_animal(original.id) is edited
        assert edited.type_jp == "猫"

    def test_edit_type_failure(self, manager):
        # Arrange
        original = manager.add_animal("bird","edit_Bird")
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.edit_animal(original.id, "type", "unknown")
        assert e.value.key == "invalid_animal_type"

    def test_edit_type_preserves_ex_ability(self, manager):
        """種類を変更しても、習得済みの特技がリセットされないことを保証します。"""
        # Arrange
        original = manager.add_animal("dog", "skill_dog")
        manager.edit_animal(original.id, "ability","fly")
        # Act
        edited = manager.edit_animal(original.id,"type", "cat")
        # Assert
        assert "fly" in edited.get_all_ability()

    def test_edit_name_success(self, manager):
        # Arrange
        original = manager.add_animal("bird","edit_Bird")
        # Act
        edited = manager.edit_animal(original.id, "name", "edited_Bird")
        # Assert
        assert edited is original
        assert edited.id == original.id
        assert manager.get_animal(original.id) is edited

        assert edited.name == "edited_Bird"

    @pytest.mark.parametrize(
            "new_name, error_key",[
                ("","name_empty"),
                ("a" * 21,"name_too_long"),
            ])
    def test_edit_name_failure(self, manager, new_name, error_key):
        # Arrange
        original = manager.add_animal("bird", "edit_Bird")
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.edit_animal(original.id, "name", new_name)
        assert e.value.key == error_key

    def test_edit_ability_success(self, manager):
        # Arrange
        original = manager.add_animal("bird","edit_Bird")
        original_ability = original.get_all_ability().copy()
        # Act
        edited = manager.edit_animal(original.id, "ability", "swim")
        edited_ability = edited.get_all_ability()
        # Assert
        assert edited is original
        assert edited.id == original.id
        assert manager.get_animal(original.id) is edited

        assert edited_ability != original_ability
        assert "swim" in edited_ability

    def test_edit_ability_failure(self, manager):
        # Arrange
        original = manager.add_animal("bird","edit_Bird")
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.edit_animal(original.id, "ability","unknown")            
        assert e.value.key == "invalid_ability"


class TestActAnimal:
    @pytest.mark.parametrize("action, expected_count", [
        ("voice", 2), # 両方鳴ける
        ("fly", 2),   # 両方飛べる
        ("swim", 1),  # Duckのみ泳げる
    ])
    def test_success(self, manager, action, expected_count):
        # Arrange
        manager.add_animal("bird", "act_Bird")
        manager.add_animal("duck", "act_Duck")
        # Act
        results = manager.act_animal(action)
        # Assert
        assert len(results) == expected_count

    def test_failure(self, manager):
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.act_animal("unknown")
        assert e.value.key == "invalid_action"

class TestSearchAnimal:
    def test_success(self, manager):
        # Arrange
        manager.add_animal("cat", "search_cat")
        # Act & Assert
        assert len(manager.search_animal("name", "search")) == 1
        assert len(manager.search_animal("type", "cat")) == 1
        assert len(manager.search_animal("type", "猫")) == 1
        assert len(manager.search_animal("ability", "fly")) == 0
        assert len(manager.search_animal("all", "search")) == 1

    def test_success_empty_keyword(self, manager):
        manager.add_random_animal(3)
        assert len(manager.search_animal("all", "")) == 3

    def test_failure(self, manager):
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.search_animal("unknown", "test")
        assert e.value.key == "invalid_search_attr"


class TestSortList:
    @pytest.mark.parametrize("attr", [
        "id",
        "name",
        "type_en",
        "type_jp",])
    def test_success(self, manager, attr):
        # Arrange
        manager.add_random_animal(5)
        animals = manager.get_all_animals()
        # Act
        expected_list = sorted([getattr(a, attr) for a in manager.animals.values()])
        actual_list = [getattr(a, attr) for a in manager.sort_list(animals, attr)]
        # Assert
        assert actual_list == expected_list

    def test_failure(self, manager):
        # Act & Assert
        with pytest.raises(ValidationError) as e:
            manager.sort_list([], "unknown")
        assert e.value.key == "invalid_sort_key"


class TestClearData:
    def test_success(self, manager):
        # Arrange
        manager.add_random_animal(5)
        # Act
        manager.clear_data()
        # Assert
        assert len(manager.animals) == 0
        assert manager.id_counter == 0
        assert all(count == 0 for count in manager.naming_count.values())
        assert not manager.is_changed()


class TestDataPersistence:
    def test_save_success(self, manager, mock_repository):
        #Arrange
        manager.add_animal("bird", "save_Bird")
        #Act
        manager.save_to_file()
        #Assert
        mock_repository.save.assert_called_once()

    def test_save_failed(self, manager, mock_repository):
        #Arrange
        mock_repository.save.side_effect = SaveError("save_error")
        #Act & Assert
        with pytest.raises(SaveError, match="save_error"):
            manager.save_to_file()
        mock_repository.save.assert_called_once()
        
    def test_is_changed_flow(self, manager):
        #Default
        assert not manager.is_changed()
        #Change
        manager.add_animal("bird", "changed_Bird")
        assert manager.is_changed()
        #Save
        manager.save_to_file()
        assert not manager.is_changed()
        #Clear
        manager.add_animal("cat", "changed_Cat")
        manager.clear_data()
        assert not manager.is_changed()

    def test_is_changed_revert(self, manager):
        """値を変更した後、手動で元に戻した場合に変更なしと判定されるかテストします。"""
        #Arrange
        animal = manager.add_animal("dog", "original_name")
        manager.save_to_file() 
        #Act
        manager.edit_animal(animal.id, "name", "new_name")
        manager.edit_animal(animal.id, "type", "cat")
        assert manager.is_changed()
        #revert
        manager.edit_animal(animal.id, "name", "original_name")
        manager.edit_animal(animal.id, "type", "dog")
        #Assert
        assert not manager.is_changed()

    def test_load_success(self, manager, mock_repository):
        #Arrange
        manager.naming_count["dog"] = 2
        manager.naming_count["cat"] = 1
        manager.add_animal("dog", "manual_dog")
        mock_repository.load.return_value = manager._get_serializable_data()
        #Act
        manager.load_from_file()
        #Assert
        mock_repository.load.assert_called_once()
        assert len(manager.animals) == 1
        assert manager.id_counter == 1
        assert manager.naming_count["dog"] == 2
        assert manager.naming_count["cat"] == 1

    def test_load_failure(self, manager, mock_repository):
        #Arrange
        mock_repository.load.return_value = None
        #Act & Assert
        manager.load_from_file() # 戻り値なし（エラーも起きない）
        assert manager.animals == {}
        mock_repository.load.assert_called_once()

    def test_full_integration_load_flow(self, tmp_path):
        #Arrange
        file_path = tmp_path / "animals.json"
        repository = AnimalRepository(file_path)
        manager = AnimalManager(repository)
        #Act
        manager.add_random_animal(3)
        original_ids = [a.id for a in manager.get_all_animals()]
        manager.save_to_file()
        manager.clear_data()
        assert len(manager.get_all_animals()) == 0
        #Assert
        manager.load_from_file()
        loaded_ids = [a.id for a in manager.get_all_animals()]
        assert loaded_ids == original_ids
