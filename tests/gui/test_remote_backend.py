import pytest
import requests
from unittest.mock import MagicMock
from controller.remote_backend import RemoteBackend
from controller.dto import AnimalDTO

@pytest.fixture
def mock_layout():
    return MagicMock()

@pytest.fixture
def remote_backend(mock_layout):
    backend = RemoteBackend(mock_layout)
    backend.session = MagicMock()
    return backend

def _setup_mock_response(remote_backend, method, status_code, json_data=None):
    """ステータスコードを指定したレスポンスのモックを作成"""
    mock_res = MagicMock()
    mock_res.status_code = status_code
    if json_data is not None:
        mock_res.json.return_value = json_data
    if status_code >= 400:
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError(f"{status_code} Error")
    else:
        mock_res.raise_for_status.return_value = None

    getattr(remote_backend.session, method).return_value = mock_res
    return mock_res

def _setup_communication_error(remote_backend, method, error_msg="Connection Error"):
    getattr(remote_backend.session, method).side_effect = Exception(error_msg)


class TestExecuteAdd:
    def test_success(self, remote_backend):
        # Arrange:
        _setup_mock_response(remote_backend, "post", 201)
        # Act
        remote_backend.execute_add("cat", "Tama")
        # Assert: APIが正しいパスで呼ばれたか確認
        remote_backend.session.post.assert_called_once()
        # execute_addの返り値が引数と一致するか
        args, kwargs = remote_backend.session.post.call_args
        assert "http://127.0.0.1:8080/animals" in args[0]
        assert kwargs["json"] == {"type": "cat", "name": "Tama"}

    def test_api_400_error(self, remote_backend):
        # Arrange: 名前が空などのビジネスロジックエラー
        _setup_mock_response(remote_backend, "post", 400)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: 400 Error"):
            remote_backend.execute_add("cat", "")

    def test_api_422_error(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "post", 422)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: 422 Error"):
            remote_backend.execute_add("unknown","Tama")

    def test_communication_error(self, remote_backend):
        # Arrange
        _setup_communication_error(remote_backend, "post", "Connection Refused")
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: Connection Refused"):
            remote_backend.execute_add("cat", "Tama")


class TestExecuteAddRandom:
    def test_success(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "post", 201)
        count = 3
        # Act
        remote_backend.execute_add_random(count)
        # Assert
        remote_backend.session.post.assert_called_once()
        args, kwargs = remote_backend.session.post.call_args
        assert "http://127.0.0.1:8080/animals/random" in args[0]
        assert kwargs["params"] == {"count": count}

    def test_api_400_error(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "post", 400)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: 400 Error"):
            remote_backend.execute_add_random(-1)

    def test_communication_error(self, remote_backend):
        # Arrange
        _setup_communication_error(remote_backend, "post", "Network Down")
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: Network Down"):
            remote_backend.execute_add_random(5)
        

class TestExecuteRemove:
    def test_success(self, remote_backend):
        # Arrange
        json_data = {"id": 1, "name": "Tama"}
        _setup_mock_response(remote_backend, "delete", 200, json_data=json_data)
        # Act
        result = remote_backend.execute_remove(json_data["id"])
        # Assert
        assert result == {"id": 1, "name": "Tama"}

    def test_api_404_error(self, remote_backend):
        # Arrange
        json_data = {"detail": "動物が見つかりません"}
        _setup_mock_response(remote_backend, "delete", 404, json_data=json_data)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: 404 Error"):
            remote_backend.execute_remove(999)

    def test_api_422_error(self, remote_backend):
        # Arrange: IDが数値でない場合など
        _setup_mock_response(remote_backend, "delete", 422)
        with pytest.raises(Exception, match="通信エラー: 422 Error"):
            remote_backend.execute_remove("invalid_id")

    def test_communication_error(self, remote_backend):
        # Arrange
        _setup_communication_error(remote_backend, "delete", "Connection Lost")
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: Connection Lost"):
            remote_backend.execute_remove(1)


class TestExecuteEdit:
    @pytest.mark.parametrize("attr, new_value", [
        ("name", "Pochi"),
        ("type", "dog"),
        ("ability", "swim"),
    ])
    def test_success(self, remote_backend, attr, new_value):
        # Arrange
        animal_id = 1
        _setup_mock_response(remote_backend, "patch", 200)     
        # Act
        remote_backend.execute_edit(animal_id, attr, new_value)
        # Assert
        remote_backend.session.patch.assert_called_once()
        args, kwargs = remote_backend.session.patch.call_args
        assert f"http://127.0.0.1:8080/animals/{animal_id}" in args[0]
        assert kwargs["json"] == {attr: new_value}
    
    def test_api_400_error(self, remote_backend):
        # Arrange: 不正な値（名前が長すぎるなど）
        _setup_mock_response(remote_backend, "patch", 400)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: 400 Error"):
            remote_backend.execute_edit(1, "name", "Too long name" * 10)

    def test_api_422_error(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "patch", 422)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: 422 Error"):
            remote_backend.execute_edit(1, "unknown_attr", "NewName")

    def test_api_404_error(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "patch", 404)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: 404 Error"):
            remote_backend.execute_edit(999, "name", "NewName")

    def test_communication_error(self, remote_backend):
        # Arrange
        _setup_communication_error(remote_backend, "patch", "Timeout")
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー: Timeout"):
            remote_backend.execute_edit(1, "name", "NewName")


class TestExecuteAct:
    def test_success(self, remote_backend):
        # Arrange
        action = "voice"
        json_data = ["ニャアと鳴いた", "ワンワンと吠えた"]
        _setup_mock_response(remote_backend, "get", 200, json_data=json_data)
        # Act
        result = remote_backend.execute_act(action)
        # Assert
        assert result == json_data
        remote_backend.session.get.assert_called_once()

    def test_api_422_error(self, remote_backend):
        _setup_mock_response(remote_backend, "get", 422)
        with pytest.raises(Exception, match="通信エラー\(行動実行\)"):
            remote_backend.execute_act("invalid_action")
        
    def test_communication_error(self, remote_backend):
        # Arrange
        _setup_communication_error(remote_backend, "get", "Network Timeout")
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー\(行動実行\): Network Timeout"):
            remote_backend.execute_act("voice")

class TestIsValidAction:
    @pytest.mark.parametrize("action, expected", [
        ("voice",  True),
        ("fly",    True),
        ("swim",   True),
        ("dance",  False),
        ("",       False),
        (None,     False),
    ])
    def test_is_valid_action(self, remote_backend, action, expected):
        assert remote_backend.is_valid_action(action) is expected


class TestExecuteSearch:
    def test_success(self, remote_backend):
        # Arrange
        json_data = [{
            "id": 1, 
            "name": "Tama", 
            "type_en": "cat", 
            "type_jp": "猫", 
            "abilities": {"voice": {}}
        }]
        _setup_mock_response(remote_backend, "get", 200, json_data=json_data)
        # Act
        results = remote_backend.execute_search("名前", "tama")
        # Assert
        assert len(results) == 1
        assert isinstance(results[0], AnimalDTO)
        assert results[0].name == "Tama"

    def test_api_422_error(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "get", 422)
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー"):
            remote_backend.execute_search("invalid_attr", "keyword")

    def test_communication_error(self, remote_backend):
        # Arrange
        _setup_communication_error(remote_backend, "get", "Timeout")
        # Act & Assert
        with pytest.raises(Exception, match="通信エラー"):
            remote_backend.execute_search("すべて", "Tama")


class TestExecuteLoad:
    def test_success(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "get", 200, json_data=[])
        # Act
        results = remote_backend.execute_load()
        # Assert
        remote_backend.session.get.assert_called_once()
        assert results == []


class TestSave:
    def test_save(self, remote_backend):
        # Act
        result = remote_backend.save()
        # Assert
        assert result == "APIモードは自動保存の為 この機能は制限されています"


class TestDataClear:
    def test_clear_data(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "post", 200)
        # Act
        remote_backend.clear_data()
        # Assert
        remote_backend.session.post.assert_called_once()

    def test_communication_error(self, remote_backend):
        _setup_communication_error(remote_backend, "post", "Server Down")
        with pytest.raises(Exception, match="通信エラー"):
            remote_backend.clear_data()


class TestHasUnsavedChanges:
    def test_has_unsaved_changes(self, remote_backend):
        # APIモードは常に自動保存ならFalseを期待
        assert remote_backend.has_unsaved_changes() is False
