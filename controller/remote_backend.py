import requests
from .dto import AnimalDTO
from api.exceptions import BadRequest, NotFound, InternalServerError

class RemoteBackend:
    def __init__(self, layout):
        self.layout = layout
        self.base_url = "http://127.0.0.1:8080"
        self.session = requests.Session()

    def _request(self, method, url, **kwargs):
        """低レイヤーの通信処理。ネットワーク接続エラーのみをキャッチして変換する"""
        try:
            func = getattr(self.session, method.lower())
            return func(url, timeout=5, **kwargs)
        except requests.exceptions.RequestException as e:
            raise InternalServerError(key="network_connection_error", original_error=str(e))

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
                elif response.status_code == 422:
                    # ここでは簡易的にBadRequestとして扱う
                    raise BadRequest(key="validation_error", errors=error_data.get("detail"))
                elif response.status_code >= 500:
                    raise InternalServerError(key=error_key, **details)
                else:
                    # その他
                    raise BadRequest(key=error_key, **details)
            except (ValueError, KeyError):
                # JSONパース失敗、または予期せぬJSON形式
                raise InternalServerError(key="api_response_parse_error", original_error=str(e), response_text=response.text)
        return response

    def execute_add(self, animal_type, name):
        payload = {"animal_type": animal_type, "name": name}
        response = self._request("POST", f"{self.base_url}/animals", json=payload)
        self._handle_response(response)

    def execute_add_random(self, count):
        payload = {"count": int(count)}
        response = self._request("POST", f"{self.base_url}/animals/random", params=payload)
        self._handle_response(response)

    def execute_remove(self, animal_id):
        response = self._request("DELETE", f"{self.base_url}/animals/{animal_id}")
        self._handle_response(response)
        data = response.json()
        return {"id": data["id"], "name": data["name"]}

    def execute_edit(self, animal_id, attr, new_value):
        payload = {attr: new_value}
        response = self._request("PATCH", f"{self.base_url}/animals/{animal_id}", json=payload)
        self._handle_response(response)

    def _to_dto(self, item):
        return AnimalDTO(
            id       = item.get("id", 0),
            name     = item.get("name", "Unknown"),
            animal_type  = item.get("animal_type", "unknown"),
            abilities= list(item.get("abilities", {}).keys()) if isinstance(item.get("abilities"), dict) else []
        )

    def execute_act(self, choice):
        response = self._request("GET", f"{self.base_url}/animals/act/{choice}")
        self._handle_response(response)
        return response.json()
    
    def is_valid_action(self, choice):
        ALLOWED_ACTIONS = {"sound", "fly", "swim"}
        return choice in ALLOWED_ACTIONS
    
    def execute_search(self, attribute, keyword):
        params = {"search_attr": attribute, "keyword": keyword}
        response = self._request("GET", f"{self.base_url}/animals", params=params)
        self._handle_response(response)
        data = response.json()
        return [self._to_dto(item) for item in data]

    def execute_load(self):
        return self.execute_search("all", "")
        
    def save(self):
        return False

    def clear_data(self):
        response = self._request("POST", f"{self.base_url}/system/clear")
        self._handle_response(response)
    
    def has_unsaved_changes(self):
        return False