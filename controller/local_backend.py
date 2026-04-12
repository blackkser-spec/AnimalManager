from tkinter import messagebox
from .dto import AnimalDTO

class LocalBackend:
    def __init__(self, layout, manager):
        self.layout = layout
        self.manager = manager

    def execute_add(self, animal_type, name):
        self.manager.add_animal(animal_type, name)

    def execute_add_random(self, count):
        self.manager.add_random_animal(count)

    def execute_remove(self, animal_id):
        removed_animal = self.manager.remove_animal(animal_id)
        return {"id": removed_animal.id, "name": removed_animal.name}

    def execute_edit(self, animal_id, attr, new_value):
        self.manager.edit_animal(animal_id, attr, new_value)

    def execute_act(self, choice):
        results = self.manager.act_animal(choice)
        return results
    
    def is_valid_action(self, choice):
        return choice in self.manager.ALLOWED_ACTIONS
    
    def execute_search(self, attribute, keyword):
        animals = self.manager.search_animal(attribute, keyword)
        return [self._to_dto(a) for a in animals]

    def _to_dto(self, animal):
        """AnimalインスタンスをAnimalDTOに変換"""
        return AnimalDTO(
            id       = animal.id,
            name     = animal.name,
            type_en  = animal.type_en,
            type_jp  = animal.type_jp,
            abilities= list(animal.get_all_ability().keys())
        )

    def execute_load(self):
        self.manager.load_from_file()

    def save(self):
        self.manager.save_to_file()
        return "ローカルデータを保存しました"

    def data_clear(self):
        self.manager.data_clear()
        self.manager.save_to_file()

    def has_unsaved_changes(self):
        return self.manager.is_changed()
