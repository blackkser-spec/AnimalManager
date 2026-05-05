import pytest
import requests
from unittest.mock import MagicMock
from controller.remote_backend import RemoteBackend
from controller.dto import AnimalDTO
from api.exceptions import BadRequest, NotFound, InternalServerError


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
    mock_res.text = "Error Text"
    if json_data is not None:
        mock_res.json.return_value = json_data or {}
    if status_code >= 400:
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError(f"{status_code} Error")
    else:
        mock_res.raise_for_status.return_value = None

    getattr(remote_backend.session, method).return_value = mock_res
    return mock_res

def _setup_communication_error(remote_backend, method, error_msg="Connection Error"):
    getattr(remote_backend.session, method).side_effect = requests.exceptions.RequestException(error_msg)


class TestHandleResponse:
    """_handle_response 内部のロジックを集中してテストする"""
    
    def test_handle_200_ok(self, remote_backend):
        mock_res = MagicMock(status_code=200)
        # 例外が発生しなければパス
        assert remote_backend._handle_response(mock_res) == mock_res

    def test_handle_400_bad_request(self, remote_backend):
        json_data = {"error": "invalid_name", "details": {"reason": "too short"}}
        mock_res = MagicMock(status_code=400)
        mock_res.json.return_value = json_data
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with pytest.raises(BadRequest) as exc:
            remote_backend._handle_response(mock_res)
        assert exc.value.key == "invalid_name"
        assert exc.value.details == {"reason": "too short"}

    def test_handle_404_not_found(self, remote_backend):
        json_data = {"error": "not_found_key"}
        mock_res = MagicMock(status_code=404)
        mock_res.json.return_value = json_data
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with pytest.raises(NotFound) as exc:
            remote_backend._handle_response(mock_res)
        assert exc.value.key == "not_found_key"

    def test_handle_422_validation_error(self, remote_backend):
        # FastAPI/Pydantic形式のエラー
        json_data = {"detail": "Invalid fields"}
        mock_res = MagicMock(status_code=422)
        mock_res.json.return_value = json_data
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with pytest.raises(BadRequest) as exc:
            remote_backend._handle_response(mock_res)
        assert exc.value.key == "validation_error"

    def test_handle_500_internal_error(self, remote_backend):
        mock_res = MagicMock(status_code=500)
        mock_res.json.return_value = {"error": "server_down"}
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with pytest.raises(InternalServerError) as exc:
            remote_backend._handle_response(mock_res)
        assert exc.value.key == "server_down"

    def test_handle_parse_error(self, remote_backend):
        mock_res = MagicMock(status_code=400)
        mock_res.json.side_effect = ValueError("Invalid JSON")
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with pytest.raises(InternalServerError) as exc:
            remote_backend._handle_response(mock_res)
        assert exc.value.key == "api_response_parse_error"


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
        assert kwargs["json"] == {"animal_type": "cat", "name": "Tama"}

    def test_error_propagation(self, remote_backend):
        # Arrange: 名前が空などのビジネスロジックエラー
        _setup_mock_response(remote_backend, "post", 400)
        # Act & Assert
        with pytest.raises(BadRequest):
            remote_backend.execute_add("cat", "")

    def test_communication_error(self, remote_backend):
        # Arrange
        _setup_communication_error(remote_backend, "post", "network_connection_error")
        # Act & Assert
        with pytest.raises(InternalServerError) as exc:
            remote_backend.execute_add("cat", "Tama")
        assert exc.value.key == "network_connection_error"


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

    def test_error_propagation(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "post", 400)
        # Act & Assert
        with pytest.raises(BadRequest):
            remote_backend.execute_add_random(-1)
        

class TestExecuteRemove:
    def test_success(self, remote_backend):
        # Arrange
        json_data = {"id": 1, "name": "Tama"}
        _setup_mock_response(remote_backend, "delete", 200, json_data=json_data)
        # Act
        result = remote_backend.execute_remove(json_data["id"])
        # Assert
        assert result == {"id": 1, "name": "Tama"}

    def test_error_propagation(self, remote_backend):
        # Arrange
        json_data = {"detail": "動物が見つかりません"}
        _setup_mock_response(remote_backend, "delete", 404, json_data=json_data)
        # Act & Assert
        with pytest.raises(NotFound):
            remote_backend.execute_remove(999)


class TestExecuteEdit:
    @pytest.mark.parametrize("attr, new_value", [
        ("name", "Pochi"),
        ("animal_type", "dog"),
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
    
    def test_error_propagation(self, remote_backend):
        _setup_mock_response(remote_backend, "patch", 404)
        with pytest.raises(NotFound):
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

    def test_error_propagation(self, remote_backend):
        # _handle_responseで400系がBadRequestになることを確認
        _setup_mock_response(remote_backend, "get", 400)
        with pytest.raises(BadRequest):
            remote_backend.execute_act("invalid_action")


class TestIsValidAction:
    @pytest.mark.parametrize("action, expected", [
        ("sound",  True),
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
            "animal_type": "cat", 
            "abilities": {"voice": {}}
        }]
        _setup_mock_response(remote_backend, "get", 200, json_data=json_data)
        # Act
        results = remote_backend.execute_search("名前", "tama")
        # Assert
        assert len(results) == 1
        assert isinstance(results[0], AnimalDTO)
        assert results[0].name == "Tama"

    def test_error_propagation(self, remote_backend):
        _setup_mock_response(remote_backend, "get", 500)
        with pytest.raises(InternalServerError):
            remote_backend.execute_search("invalid_attr", "keyword")


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
        assert result is False


class TestDataClear:
    def test_clear_data(self, remote_backend):
        # Arrange
        _setup_mock_response(remote_backend, "post", 200)
        # Act
        remote_backend.clear_data()
        # Assert
        remote_backend.session.post.assert_called_once()


class TestHasUnsavedChanges:
    def test_has_unsaved_changes(self, remote_backend):
        assert remote_backend.has_unsaved_changes() is False
