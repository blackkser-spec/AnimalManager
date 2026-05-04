import requests
from .dto import AnimalDTO
from api.exceptions import BadRequest, NotFound, InternalServerError

class RemoteBackend:
    def __init__(self, layout):
        self.layout = layout
        self.base_url = "http://127.0.0.1:8080"
        self.session = requests.Session()

    def _handle_response(self, response):
        """共通のエラーハンドリング。APIが返す詳細なエラー情報を抽出する"""
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                error_key = error_data.get("error", "unknown_api_error")
                details = error_data.get("details", {})
                
                if response.status_code == 400:
                    raise BadRequest(key=error_key, **details)
                elif response.status_code == 404:
                    raise NotFound(key=error_key, **details)
                elif response.status_code == 422: # FastAPIのPydanticバリデーションエラー
                    # ここでは簡易的にBadRequestとして扱う
                    raise BadRequest(key="validation_error", details=error_data.get("detail", "Invalid input"))
                elif response.status_code >= 500:
                    raise InternalServerError(key=error_key, **details)
                else:
                    # その他
                    raise BadRequest(key=error_key, **details)
            except (ValueError, KeyError):
                # JSONパース失敗、または予期せぬJSON形式
                raise InternalServerError(key="api_response_parse_error", original_error=str(e), response_text=response.text)
        except requests.exceptions.RequestException as e:
            # ネットワーク接続自体が失敗した場合 (DNSエラー、接続拒否など)
            raise InternalServerError(key="network_connection_error", original_error=str(e))
        return response


    def execute_add(self, animal_type, name):
        try:
            payload = {"animal_type": animal_type, "name": name}
            response = self.session.post(f"{self.base_url}/animals", json=payload, timeout=5)
            self._handle_response(response)
        except (BadRequest, InternalServerError) as e:
            raise e

    def execute_add_random(self, count):
        try:
            payload = {"count": int(count)}
            response = self.session.post(f"{self.base_url}/animals/random", params=payload, timeout=5)
            self._handle_response(response)
        except (BadRequest, InternalServerError) as e:
            raise e

    def execute_remove(self, animal_id):
        try:
            response = self.session.delete(f"{self.base_url}/animals/{animal_id}", timeout=5)
            self._handle_response(response)
            data = response.json()
            return {"id": data["id"], "name": data["name"]}
        except (NotFound, BadRequest, InternalServerError) as e:
            raise e

    def execute_edit(self, animal_id, attr, new_value):
        try:
            api_attr = "animal_type" if attr == "type" else attr # managerの'type'をAPIの'animal_type'に変換
            payload = {api_attr: new_value}
            response = self.session.patch(f"{self.base_url}/animals/{animal_id}", json=payload, timeout=5)
            self._handle_response(response)
        except (NotFound, BadRequest, InternalServerError) as e:
            raise e

    def _to_dto(self, item):
        """JSON辞書をAnimalDTOに変換"""
        return AnimalDTO(
            id       = item.get("id", 0),
            name     = item.get("name", "Unknown"),
            animal_type  = item.get("animal_type", "unknown"),
            abilities= list(item.get("abilities", {}))
        )

    def execute_act(self, choice):
        try:
            response = self.session.get(f"{self.base_url}/animals/act/{choice}", timeout=5)
            self._handle_response(response)
            return response.json()
        except (BadRequest, InternalServerError) as e:
            raise e
    
    def is_valid_action(self, choice):
        # 将来的にAPI側から可能なアクションを取得するように拡張も可能
        ALLOWED_ACTIONS = {"sound", "fly", "swim"}
        return choice in ALLOWED_ACTIONS
    
    def execute_search(self, attribute, keyword):
        try:
            # APIのEnum値と一致させる
            params = {"search_attr": attribute, "keyword": keyword}
            response = self.session.get(f"{self.base_url}/animals", params=params, timeout=5)
            self._handle_response(response)
            data = response.json()
            return [self._to_dto(item) for item in data]
        except (BadRequest, InternalServerError) as e:
            raise e

    def execute_load(self):
        return self.execute_search("all", "")
        
    def save(self):
        return False

    def clear_data(self):
        try:
            response = self.session.post(f"{self.base_url}/system/clear", timeout=5)
            self._handle_response(response)
        except InternalServerError as e:
            raise e
    
    def has_unsaved_changes(self):
        return False