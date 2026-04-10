import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from API.api_main import app, manager

@pytest.fixture
def client():
    """テスト用のクライアントを生成するフィクスチャ"""
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_api_storage():
    """
    APIが使用するリポジトリをモックに差し替え、
    テストごとにデータをリセットしてID競合を防ぎます。
    """
    manager.repository = MagicMock()
    manager.data_clear()
    yield

@pytest.fixture
def sample_animal(client):
    """テスト用の動物を1匹作成してIDを返すフィクスチャ"""
    response = client.post("/animals", json={"type": "cat", "name": "TestCat"})
    return response.json()

class TestAddAnimal:
    def test_success(self, client):
        payload = {"type": "cat", "name": "AddCat"}
        response = client.post("/animals", json=payload)
        assert response.status_code == 201
        assert response.json()["name"] == "AddCat"

    def test_error_save_failed(self, client):
        """追加時の保存失敗(500)のテスト"""
        manager.repository.save.return_value = False
        payload = {"type": "cat", "name": "FailAnimal"}
        response = client.post("/animals", json=payload)
        assert response.status_code == 500

    def test_error_empty_name(self, client):
        payload = {"type": "cat", "name": ""}
        response = client.post("/animals", json=payload)
        assert response.status_code == 400
        assert "名前を空白にはできません" in response.json()["detail"]

class TestAddRandomAnimal:
    def test_success(self, client):
        response = client.post("/animals/random", params={"count": 3})
        assert response.status_code == 201
        assert len(response.json()) == 3

    def test_error_invalid_type(self, client):
        response = client.post("/animals/random", params={"count": "invalid"})
        assert response.status_code == 422
    
    def test_error_negative_value(self, client):
        response = client.post("/animals/random", params={"count": -1})
        assert response.status_code == 400
        assert "1以上を指定してください" in response.json()["detail"]

class TestRemoveAnimal:
    def test_success(self, client, sample_animal):
        response = client.delete(f"/animals/{sample_animal['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == sample_animal["id"]

    @pytest.mark.parametrize("animal_id, expected_status", [
        ("invalid-id", 422),
        ("0", 404)
    ])
    def test_error_invalid_id(self, client, animal_id, expected_status):
        response = client.delete(f"/animals/{animal_id}")
        assert response.status_code == expected_status
        if expected_status == 404:
            assert "存在しません" in response.json()["detail"]

class TestEditAnimal:
    def test_name_success(self, client, sample_animal):
        response = client.patch(f"/animals/{sample_animal['id']}", json={"type": "dog", "name": "EditedDog"})
        assert response.status_code == 200
        assert response.json()["name"] == "EditedDog"

    def test_ability_success(self, client, sample_animal):
        """特技のみを追加変更するテスト"""
        response = client.patch(f"/animals/{sample_animal['id']}", json={"ability": "fly"})
        assert response.status_code == 200
        assert "fly" in response.json()["abilities"]

    @pytest.mark.parametrize("animal_id, payload, expected_status",[
        ("invalid-id", {"name": "test"}, 422), # IDが数値でない場合はFastAPIのバリデーション(422)
        (999, {"name": "test"}, 404),          # 存在しないIDはManagerがAnimalNotFoundError(404)
        (1, {"name": ""}, 400),               # 不正なデータはManagerがValueError(400)
    ])
    def test_edit_error_status(self, client, sample_animal, animal_id, payload, expected_status):
        if expected_status == 400:
            animal_id = sample_animal["id"]
            
        response = client.patch(f"/animals/{animal_id}", json=payload)
        assert response.status_code == expected_status

class TestActAnimal:
    def test_success_voice(self, client, sample_animal):
        response = client.get("/animals/act/voice")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) == 1
        assert "TestCat" in results[0]

    def test_error_invalid_ability(self, client):
        response = client.get("/animals/act/invalid")
        assert response.status_code == 422

class TestGetAnimal:
    def test_get_detail_success(self, client, sample_animal):
        response = client.get(f"/animals/{sample_animal['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == sample_animal["id"]
        assert response.json()["name"] == sample_animal["name"]      
        assert response.json()["type_en"] == "cat"
        assert response.json()["type_jp"] == "猫"
        assert "abilities" in response.json()

    def test_get_detail_error(self, client):
        response = client.get("/animals/999")
        assert response.status_code == 404
        assert "存在しません" in response.json()["detail"]

class TestGetAvailableAnimalTypes:
    def test_success(self, client):
        response = client.get("/animals/types")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestGetAvailableAbilities:
    def test_success(self, client):
        response = client.get("/animals/abilities")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestSearchAnimal:
    def test_get_all(self, client):
        response = client.get("/animals")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_cat(self, client):
        response = client.get("/animals", params={"keyword": "cat"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_with_sort(self, client):
        client.post("/animals", json={"type": "cat", "name": "B_Cat"})
        client.post("/animals", json={"type": "cat", "name": "A_Cat"})
        # 名前順でソート
        response = client.get("/animals", params={"sort_by": "名前"})
        names = [a["name"] for a in response.json()]
        assert names == sorted(names)

class TestResetData:
    def test_success(self, client, sample_animal):
        response = client.post("/system/reset")
        assert response.status_code == 200
        assert response.json()["message"] == "Data has been reset successfully"
    
    def test_error(self, client):
        """
        保存失敗（リポジトリエラー等）を擬似的に発生させ、APIが500エラーを返せるかを検証。
        """
        manager.repository.save.return_value = False
        response = client.post("/system/reset")
        assert response.status_code == 500

if __name__ == "__main__":
    pytest.main()