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

def test_get_animals_api(client):
    response = client.get("/animals")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.parametrize("animal_type, name", [
    ("cat", "APIタマ"),
    ("bird", "APIピーちゃん"),
    ("dog", "APIポチ"),
    ("duck", "APIドナルド"),
])
def test_add_animal_api(client, animal_type, name):
    payload = {"type": animal_type, "name": name}
    response = client.post("/animals", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert "id" in data

def test_add_animal_api_error_handling(client):
    """
    APIがManagerの例外を適切に400ステータスに変換するかテストします。
    バリデーションの詳細はManager側でテストされているため、ここでは境界線のみを確認します。
    """
    payload = {"type": "cat", "name": ""}
    response = client.post("/animals", json=payload)
    assert response.status_code == 400
    assert "名前を空白にはできません" in response.json()["detail"]

def test_get_invalid_animal_api(client):
    response = client.get("/animals/999")
    assert response.status_code == 404
    assert "存在しません" in response.json()["detail"]

def test_remove_animal_api(client):
    payload = {"type": "cat", "name": "APIねこ"}
    post_response = client.post("/animals", json=payload)
    assert post_response.status_code == 201
    created_animal_id = post_response.json()["id"]
    created_animal_name = post_response.json()["name"]
    
    response = client.delete(f"/animals/{created_animal_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == created_animal_id
    assert response.json()["name"] == created_animal_name

@pytest.mark.parametrize("animal_id, expected_status", [
    ("invalid-id", 422),    # 数値ではない（型不一致）
    ("0", 404)              # 0番（存在しないID）
])
def test_remove_animal_error_api(client, animal_id, expected_status):
    response = client.delete(f"/animals/{animal_id}")
    assert response.status_code == expected_status
    if expected_status == 404:
        assert "存在しません" in response.json()["detail"]
