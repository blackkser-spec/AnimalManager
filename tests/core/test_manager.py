import pytest
from unittest.mock import MagicMock
from core.manager import AnimalManager, AnimalNotFoundError
from core.animal_repository import AnimalRepository

@pytest.fixture
def mock_repository():
    """    実際のファイル操作を行わないためのダミーのリポジトリを提供します。    """
    return MagicMock()

@pytest.fixture
def manager(mock_repository):
    """    テストごとに初期化されたAnimalManagerのインスタンスを提供します。    """
    return AnimalManager(mock_repository)

@pytest.mark.parametrize("animal_type, name", [
    ("cat", "add_Cat"),
    ("dog", "add_Dog"),
    ("duck", "add_Duck"),
])
def test_add_animal(manager, animal_type, name):
    animal = manager.add_animal(animal_type, name)
    
    assert animal.type_en == animal_type
    assert animal.name == name
    assert 1 in manager.animals
    assert len(manager.animals) == 1

@pytest.mark.parametrize("animal_type, name, expected_error", [
    ("unknown", "add_Cat", "無効な種類の動物です"),
    ("cat", "a" * 21, "名前は20文字以内で入力してください"),
    ("cat", "", "名前を空白にはできません"),
])
def test_add_animal_error(manager, animal_type, name, expected_error):
    """
    不正な入力に対するバリデーションが正しく機能するか。
    このテストはManagerの安全性における中心的な役割を担います。
    """
    with pytest.raises(ValueError, match=expected_error):
        manager.add_animal(animal_type, name)

def test_add_animal_with_extreme_name(manager):
    """
    サロゲートペア（絵文字など）の扱いが気になったため追加。
    """
    animal = manager.add_animal("cat", "🐱🐱🐱")
    assert animal.name == "🐱🐱🐱"

def test_add_random_animal(manager):
    result = manager.add_random_animal(3)
    assert len(result) == 3

@pytest.mark.parametrize("count",[(-1), (0)])
def test_add_random_animal_invalid_range(manager,count):
    with pytest.raises(ValueError):
        manager.add_random_animal(count)

@pytest.mark.parametrize("count", [0.1, "a"])
def test_add_random_animal_invalid_type(manager, count):
    with pytest.raises(ValueError):
        manager.add_random_animal(count)

def test_get_animal(manager):
    original = manager.add_animal("bird","get_Bird")
    result = manager.get_animal(original.id)

    assert result.type_jp == "鳥"
    assert result.name == "get_Bird"

def test_get_animal_not_found(manager):
    with pytest.raises(AnimalNotFoundError):
        manager.get_animal(999)

def test_get_all_animals_returns_correct_count(manager):
    manager.add_random_animal(5)
    animals = manager.get_all_animals()
    assert len(animals) == 5

def test_remove_animal(manager):
    animal = manager.add_animal("cat", "remove_Cat")
    manager.remove_animal(animal.id)
    
    assert len(manager.animals) == 0

def test_edit_animal_type(manager):
    original = manager.add_animal("bird","edit_Bird")
    edited = manager.edit_animal(original.id, "type", "cat")

    assert edited is not original
    assert edited.id == original.id
    assert manager.get_animal(original.id) is edited
    assert edited.type_jp == "猫"

def test_edit_animal_type_preserves_ex_ability(manager):
    """種類を変更しても、習得済みの特技がリセットされないことを保証します。"""
    original = manager.add_animal("dog", "skill_dog")
    manager.edit_animal(original.id, "ability","fly")
    
    edited = manager.edit_animal(original.id,"type", "cat")
    assert "fly" in edited.get_all_ability()

def test_edit_animal_type_error(manager):
    original = manager.add_animal("bird","edit_Bird")
    with pytest.raises(ValueError):
        manager.edit_animal(original.id, "type", "unknown")

def test_edit_animal_name(manager):
    original = manager.add_animal("bird","edit_Bird")
    edited = manager.edit_animal(original.id, "name", "edited_Bird")

    assert edited is original
    assert edited.id == original.id
    assert manager.get_animal(original.id) is edited

    assert edited.name == "edited_Bird"

@pytest.mark.parametrize(
        "new_name, expected_disc",
        [
            ("","空白"),
            ("a" * 21,"20文字以内"),
        ])
def test_edit_animal_name_error(manager, new_name, expected_disc):
    original = manager.add_animal("bird", "edit_Bird")
    with pytest.raises(ValueError, match=expected_disc):
        manager.edit_animal(original.id, "name", new_name)

def test_edit_animal_ability(manager):
    original = manager.add_animal("bird","edit_Bird")
    original_ability = original.get_all_ability().copy()

    edited = manager.edit_animal(original.id, "ability", "swim")
    edited_ability = edited.get_all_ability()

    assert edited is original
    assert edited.id == original.id
    assert manager.get_animal(original.id) is edited

    assert edited_ability != original_ability
    assert "swim" in edited_ability

def test_edit_animal_ability_error(manager):
    original = manager.add_animal("bird","edit_Bird")
    with pytest.raises(ValueError):
        manager.edit_animal(original.id, "ability","unknown")

@pytest.mark.parametrize("action, expected_count", [
    ("voice", 2), # 両方鳴ける
    ("fly", 2),   # 両方飛べる
    ("swim", 1),  # Duckのみ泳げる
])
def test_act_animal(manager, action, expected_count):
    manager.add_animal("bird", "act_Bird")
    manager.add_animal("duck", "act_Duck")

    results = manager.act_animal(action)
    assert len(results) == expected_count

def test_act_animal_error(manager):
    with pytest.raises(ValueError, match="無効なアクションです"):
        manager.act_animal("unknown")

def test_search_animal(manager):
    manager.add_animal("cat", "search_cat")

    assert len(manager.search_animal("名前", "search")) == 1
    assert len(manager.search_animal("種類", "cat")) == 1
    assert len(manager.search_animal("種類", "猫")) == 1
    assert len(manager.search_animal("特技", "fly")) == 0
    assert len(manager.search_animal("すべて", "search")) == 1

def test_search_animal_error(manager):
    with pytest.raises(ValueError):
        manager.search_animal("unknown", "test")

@pytest.mark.parametrize("attr", [
    "id",
    "name",
    "type_en",
    "type_jp",])
def test_sort_list(manager, attr):
    manager.add_random_animal(5)
    animals = manager.get_all_animals()
    expected_list = sorted([getattr(a, attr) for a in manager.animals.values()])
    actual_list = [getattr(a, attr) for a in manager.sort_list(animals, attr)]

    assert actual_list == expected_list

def test_sort_list_error(manager):
    with pytest.raises(ValueError):
        manager.sort_list([], "unknown")

def test_clear_data(manager):
    manager.add_random_animal(5)
    manager.clear_data()

    assert len(manager.animals) == 0
    assert manager.id_counter == 0
    assert all(count == 0 for count in manager.naming_count.values())
    assert manager.initial_state_data == manager._get_serializable_data()

def test_save_to_file(manager, mock_repository):
    #Arrange
    manager.add_animal("bird", "save_Bird")
    mock_repository.save.return_value = True
    #Act
    manager.save_to_file()
    #Assert
    mock_repository.save.assert_called_once()

def test_save_to_file_failed(manager, mock_repository):
    mock_repository.save.side_effect = IOError("ファイルの保存中にエラーが発生しました")
    with pytest.raises(IOError, match="ファイルの保存中にエラーが発生しました"):
        manager.save_to_file()
    mock_repository.save.assert_called_once()
    
def test_is_changed(manager):
    #Default
    assert manager.is_changed() == False
    #Change
    manager.add_animal("bird", "changed_Bird")
    assert manager.is_changed() == True
    #Save
    manager.save_to_file()
    assert manager.is_changed() == False
    #Clear
    manager.add_animal("cat", "changed_Cat")
    manager.clear_data()
    assert manager.is_changed() == False

def test_is_changed_revert(manager):
    """値を変更した後、手動で元に戻した場合に変更なしと判定されるかテストします。"""
    #Arrange
    animal = manager.add_animal("dog", "original_name")
    manager.save_to_file() 
    #Act
    manager.edit_animal(animal.id, "name", "new_name")
    manager.edit_animal(animal.id, "type", "cat")
    assert manager.is_changed() == True
    #revert
    manager.edit_animal(animal.id, "name", "original_name")
    manager.edit_animal(animal.id, "type", "dog")
    #Assert
    assert manager.is_changed() == False

def test_load_from_file(manager, mock_repository):
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

def test_load_from_file_failed(manager, mock_repository):
    mock_repository.load.return_value = None
    manager.load_from_file() # 戻り値なし（エラーも起きない）
    assert manager.animals == {}
    mock_repository.load.assert_called_once()

def test_full_load_flow(tmp_path):
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
