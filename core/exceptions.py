class AnimalManagerError(Exception):
    def __init__(self, key="unknown_error", **kwargs):
        super().__init__(key)
        self.key = key
        self.kwargs = kwargs
        

class ValidationError(AnimalManagerError):
    pass


class NotFoundError(ValidationError):
    pass


class AnimalNotFoundError(NotFoundError):
    def __init__(self, animal_id):
        super().__init__("id_not_found", id=animal_id)


class RepositoryError(AnimalManagerError):
    pass


class SaveError(RepositoryError):
    def __init__(self, key="save_error", **kwargs):
        super().__init__(key, **kwargs)


class LoadError(RepositoryError):
    def __init__(self, key="load_error", **kwargs):
        super().__init__(key, **kwargs)