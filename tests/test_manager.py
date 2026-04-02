import pytest
from unittest.mock import MagicMock
from core.manager import AnimalManager, AnimalNotFoundError

@pytest.fixture
def mock_repository():
    """    実際のファイル操作を行わないためのダミーのリポジトリを提供します。    """
    return MagicMock()

@pytest.fixture
def manager(mock_repository):
    """    テストごとに初期化されたAnimalManagerのインスタンスを提供します。    """
    return AnimalManager(mock_repository)

def test_add_animal(manager):
    """動物が正しく追加され、IDが採番されることをテストします。"""
    animal = manager.add_animal("bird", "ピーちゃん")
    
    assert animal.name == "ピーちゃん"
    assert animal.type_en == "bird"
    assert 1 in manager.animals
    assert len(manager.animals) == 1

@pytest.mark.parametrize("animal_type, name, expected_error", [
    ("unknown", "Tama", "無効な種類の動物です"),
    ("cat", "a" * 21, "名前は20文字以内で入力してください"),
    ("cat", "", "名前を空白にはできません"),
])
def test_add_animal_validation_logic(manager, animal_type, name, expected_error):
    """Managerレベルでのあらゆるバリデーションロジックを網羅します。"""
    with pytest.raises(ValueError, match=expected_error):
        manager.add_animal(animal_type, name)

def test_get_animal(manager):
    """存在するIDで動物が正しく取得できるかテストします。"""
    original = manager.add_animal("bird","getバード")
    result = manager.get_animal(original.id)

    assert result.type_jp == "鳥"
    assert result.name == "getバード"

def test_get_animal_not_found(manager):
    """存在しないIDを指定したときに例外が発生するかテストします。"""
    with pytest.raises(AnimalNotFoundError):
        manager.get_animal(999)

def test_remove_animal(manager):
    """動物の削除が正しく行われるかテストします。"""
    manager.add_animal("cat", "タマ")
    manager.remove_animal(1)
    
    assert len(manager.animals) == 0

def test_edit_animal_type(manager):
    original = manager.add_animal("bird","editバード")
    edited = manager.edit_animal_type(original.id, "cat")

    assert edited is not original
    assert edited.id == original.id
    assert manager.get_animal(original.id) is edited
    assert edited.type_jp == "猫"

def test_edit_animal_type_error(manager):
    original = manager.add_animal("bird","editバード")
    with pytest.raises(ValueError):
        manager.edit_animal_type(original.id, "unknown")

def test_edit_animal_name(manager):
    original = manager.add_animal("bird","editバード")
    edited = manager.edit_animal_name(original.id, "editedバード")

    assert edited is original
    assert edited.id == original.id
    assert manager.get_animal(original.id) is edited

    assert edited.name == "editedバード"

@pytest.mark.parametrize(
        "new_name, expected_disc",
        [
            ("","空白"),
            ("a" * 21,"20文字以内"),
        ])
def test_edit_animal_name_error(manager, new_name, expected_disc):
    original = manager.add_animal("bird", "editバード")
    with pytest.raises(ValueError, match=expected_disc):
        manager.edit_animal_name(original.id, new_name)

def test_edit_animal_ability(manager):
    original = manager.add_animal("bird","editバード")
    original_ability = original.get_all_ability().copy()

    edited = manager.edit_animal_ability(original.id, "swim")
    edited_ability = edited.get_all_ability()

    assert edited is original
    assert edited.id == original.id
    assert manager.get_animal(original.id) is edited

    assert edited_ability != original_ability
    assert "swim" in edited_ability

def test_edit_animal_ability_error(manager):
    original = manager.add_animal("bird","editバード")
    with pytest.raises(ValueError):
        manager.edit_animal_ability(original.id, "unknown")

def test_search_animal(manager):
    """検索ロジックが正しくフィルタリングを行うかテストします。"""
    manager.add_animal("bird", "Birdy")
    manager.add_animal("cat", "Kitty")
    
    # 「bird」を含む名前を検索
    results = manager.search_animal("名前", "bird")
    
    assert len(results) == 1
    assert results[0].name == "Birdy"