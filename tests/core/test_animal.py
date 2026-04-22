import pytest
from core.animal import Animal, Bird, Cat, Dog, Duck, Fish, Penguin

@pytest.fixture
def duck():
    return Animal(
        id=1,
        name="TEST_DUCK",
        type_en="duck",
        type_jp="アヒル",
        voice_msg="ガアガアと鳴いた",
        ability={
            "fly": {"msg": "飛んだ！"},
            "swim": {"msg": "泳いだ！"}
        },
        ex_ability={}
    )
@pytest.fixture
def cat():
    return Animal(
        id=2,
        name="TEST_CAT",
        type_en="cat",
        type_jp="猫",
        voice_msg="ニャアと鳴いた",
        ex_ability={}
    )

class TestToDict:
    def test_success(self, duck):
        # Act
        result = duck.to_dict()
        # Assert
        assert result == {
            "id": 1,
            "name": "TEST_DUCK",
            "type_en": "duck",
            "type_jp": "アヒル",
            "ex_ability": {}
        }
    
class TestFromDict:
    def test_success(self):
        # Arrange
        data = {
            "id": 1,
            "name": "TEST_DUCK",
            "ex_ability":{
                "fly": {"msg": "飛んだ！"},
                "swim": {"msg": "泳いだ！"}
            }
        }
        # Act
        result = Animal.from_dict(data)
        # Assert
        assert result.id == 1
        assert result.name == "TEST_DUCK"
        assert result.ex_ability == data["ex_ability"]

    def test_success_without_ex_ability(self):
        """ex_abilityがデータに存在しない場合でも正しくインスタンス化されるか"""
        # Arrange
        data = {
            "id": 2,
            "name": "TEST_CAT",
        }
        # Act
        result = Animal.from_dict(data)
        # Assert
        assert result.id == 2
        assert result.name == "TEST_CAT"
        assert result.ex_ability == {} # ex_abilityが空の辞書として初期化されることを確認

class TestGetAllAbility:
    def test_dynamic_addition(self, cat):
        """能力を持たない個体に後からex_abilityを追加して取得できるか"""
        # Arrange
        extra = {"fly": {"msg": "マントで飛んだ！"}}
        cat.ex_ability = extra
        # Act
        result = cat.get_all_ability()
        # Assert
        assert result == extra

    def test_merge_additional_ability(self, duck):
        """元々の能力(ability)と追加の能力(ex_ability)がマージされるか"""
        # Arrange
        duck.ex_ability = {"swim": {"msg": "別の泳ぎ方"}}
        # Act
        result = duck.get_all_ability()
        # Assert
        assert "fly" in result
        assert "swim" in result
        assert result["fly"]["msg"] == "飛んだ！"
        assert result["swim"]["msg"] == "別の泳ぎ方"


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
    "method_name, expected_msg",[
        ("voice", "ガアガアと鳴いた"),
        ("fly", "飛んだ！"),
        ("swim", "泳いだ！"),]
    )
    def test_success(self, duck, method_name, expected_msg):
        # Arrange
        method = getattr(duck, method_name)
        # Act
        result = method()
        # Assert
        assert expected_msg in result
    
    @pytest.mark.parametrize("method_name", ["fly", "swim"])
    def test_no_ability(self, cat, method_name):
        # Arrange
        method = getattr(cat, method_name)
        # Act
        result = method()
        # Assert
        assert result is None

class TestSubclasses:
    """各サブクラスが正しい初期値（鳴き声や能力）を持っているかの網羅テスト"""
    @pytest.mark.parametrize("cls, expected_voice, expected_ability_key", [
        (Bird, "チュンチュン", "fly"),
        (Cat, "ニャア", None),
        (Dog, "ワンワン", None),
        (Duck, "ガアガア", "swim"),
        (Fish, "静かにしている", "swim"),
        (Penguin, "ぷーぷー", "swim"),
    ])
    def test_subclass_initialization(self, cls, expected_voice, expected_ability_key):
        instance = cls(id=99, name="Test")
        assert expected_voice in instance.voice()
        if expected_ability_key:
            assert expected_ability_key in instance.get_all_ability()