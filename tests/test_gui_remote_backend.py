import pytest
from unittest.mock import MagicMock
from controller.remote_backend import RemoteBackend
from controller.dto import AnimalDTO

@pytest.fixture
def mock_layout():
    return MagicMock()

@pytest.fixture
def mock_manager():
    return MagicMock()

@pytest.fixture
def remote_backend(mock_layout, mock_manager):
    backend = RemoteBackend(mock_layout, mock_manager)
    backend.session = MagicMock()
    return backend

class TestExecuteAdd:
    def test_success(self, remote_backend, mock_manager):
        # Arrange: サーバーの成功レスポンスをシミュレート
        mock_response = MagicMock()
        mock_response.status_code = 201
        remote_backend.session.post.return_value = mock_response

        # Act
        remote_backend.execute_add("cat", "Tama")

        # Assert: APIが正しいパスで呼ばれたか確認
        remote_backend.session.post.assert_called_once()
        args, kwargs = remote_backend.session.post.call_args
        assert "http://127.0.0.1:8080/animals" in args[0]
        assert kwargs["json"] == {"type": "cat", "name": "Tama"}
        
        # 通信成功後、Managerのデータがリロードされたか
        mock_manager.load_from_file.assert_called_once()

    def test_communication_error(self, remote_backend):
        # Arrange: 接続拒否などの通信エラーをシミュレート
        remote_backend.session.post.side_effect = Exception("Connection Refused")

        # Act & Assert: Backendが「通信エラー」として再送出するか確認
        with pytest.raises(Exception, match="通信エラー"):
            remote_backend.execute_add("cat", "Tama")

class TestExecuteRemove:
    def test_success(self, remote_backend, mock_manager):
        # Arrange: 削除成功時のJSONレスポンスを定義
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Tama"}
        remote_backend.session.delete.return_value = mock_response

        # Act
        result = remote_backend.execute_remove(1)

        # Assert
        assert result == {"id": 1, "name": "Tama"}
        mock_manager.load_from_file.assert_called_once()

    def test_api_error_status(self, remote_backend):
        # Arrange: 404エラーと詳細メッセージを返すシナリオ
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "動物が見つかりません"}
        remote_backend.session.delete.return_value = mock_response

        # Act & Assert
        with pytest.raises(Exception, match="APIエラー: 動物が見つかりません"):
            remote_backend.execute_remove(999)

class TestExecuteSearch:
    def test_success(self, remote_backend):
        # Arrange: 検索結果のリストを返すシナリオ
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1, 
                "name": "Tama", 
                "type_en": "cat", 
                "type_jp": "猫", 
                "abilities": {"voice": {}}
            }
        ]
        remote_backend.session.get.return_value = mock_response

        # Act
        results = remote_backend.execute_search("名前", "tama")

        # Assert
        assert len(results) == 1
        assert isinstance(results[0], AnimalDTO)
        assert results[0].name == "Tama"
