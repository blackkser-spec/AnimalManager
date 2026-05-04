class NetworkError(Exception):
    def __init__(self, key: str = "network_error", **kwargs):
        super().__init__(key)
        self.key = key
        self.details = kwargs


class BadRequest(NetworkError):
    def __init__(self, key: str = "bad_request", **kwargs):
        super().__init__(key, **kwargs)


class NotFound(NetworkError):
    def __init__(self, key: str = "not_found", **kwargs):
        super().__init__(key, **kwargs)


class InternalServerError(NetworkError):
    def __init__(self, key: str = "internal_server_error", **kwargs):
        super().__init__(key, **kwargs)