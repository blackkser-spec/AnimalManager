import pytest
from core.animal import Animal, Bird, Cat, Dog, Duck, Fish, Penguin

@pytest.fixture
def duck():
    return Animal(
        id=1,
        name="TEST_DUCK",
        animal_type="duck",
        ability={"fly", "swim", "sound"},
        ex_ability=set()
    )
@pytest.fixture
def cat():
    return Animal(
        id=2,
        name="TEST_CAT",
        animal_type="cat",
        ex_ability=set()
    )

class TestToDict:
    def test_success(self, duck):
        # Act
        result = duck.to_dict()
        # Assert
        assert result == {
            "id": 1,
            "name": "TEST_DUCK",
            "animal_type": "duck",
            "ex_ability": []
        }
    
class TestFromDict:
    def test_success(self):
        # Arrange
        data = {
            "id": 1,
            "name": "TEST_DUCK",
            "animal_type": "duck",
            "ex_ability": ["sound", "fly", "swim"]
        }
        # Act
        result = Animal.from_dict(data)
        # Assert
        assert result.id == 1
        assert result.name == "TEST_DUCK"
        assert result.animal_type == "duck"
        assert result.ex_ability == {"sound", "fly", "swim"}

    def test_success_without_ex_ability(self):
        """ex_abilityがデータに存在しない場合でも正しくインスタンス化されるか"""
        # Arrange
        data = {
            "id": 2,
            "name": "TEST_CAT",
            "animal_type": "cat",
        }
        # Act
        result = Animal.from_dict(data)
        # Assert
        assert result.id == 2
        assert result.name == "TEST_CAT"
        assert result.animal_type == "cat"
        assert result.ex_ability == set() # 空の集合として初期化されることを確認

class TestGetAllAbility:
    def test_dynamic_addition(self, cat):
        """能力を持たない個体に後からex_abilityを追加して取得できるか"""
        # Arrange
        extra = {"fly"}
        cat.ex_ability = extra
        # Act
        result = cat.get_all_ability()
        # Assert
        assert result == extra

    def test_merge_additional_ability(self, duck):
        """元々の能力(ability)と追加の能力(ex_ability)がマージされるか"""
        # Arrange
        duck.ex_ability = {"super_swim"}
        # Act
        result = duck.get_all_ability()
        # Assert
        assert "fly" in result
        assert "swim" in result
        assert "super_swim" in result


class TestHasAbility:
    @pytest.mark.parametrize("animal, expected", [
        ("duck", True),
        ("cat", False),
    ])
    def test_success(self, request, animal, expected):
        # Arrange
        obj = request.getfixturevalue(animal)
        # Act & Assert
        assert obj.has_ability("fly") is expected


class TestAction:
    @pytest.mark.parametrize(
    "method_name, expected_key",[
        ("sound", "sound"),
        ("fly", "fly"),
        ("swim", "swim"),]
    )
    def test_success(self, duck, method_name, expected_key):
        # Arrange
        method = getattr(duck, method_name)
        # Act
        result = method()
        # Assert
        assert result == expected_key
    
    @pytest.mark.parametrize("method_name", ["sound", "fly", "swim"])
    def test_no_ability(self, cat, method_name):
        # Arrange
        method = getattr(cat, method_name)
        # Act
        result = method()
        # Assert
        assert result is None

class TestSubclasses:
    """各サブクラスが正しい初期値（鳴き声や能力）を持っているかの網羅テスト"""
    @pytest.mark.parametrize("cls, expected_action, expected_ability_key", [
        (Bird, "sound", "fly"),
        (Cat, "sound", None),
        (Dog, "sound", None),
        (Duck, "sound", "swim"),
        (Fish, None, "swim"),
        (Penguin, "sound", "swim"),
    ])
    def test_subclass_initialization(self, cls, expected_action, expected_ability_key):
        instance = cls(id=99, name="Test")
        assert instance.sound() == expected_action
        if expected_ability_key:
            assert expected_ability_key in instance.get_all_ability()