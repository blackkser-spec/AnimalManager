from controller.base import BaseController
from tkinter import messagebox

class LocalController(BaseController):
    def execute_add(self, animal_type, name):
        try:
            self.manager.add_animal(animal_type, name)
        except ValueError as e:
            raise e

    def execute_add_random(self, count):
        try:
            self.manager.add_random_animal(count)
        except ValueError as e:
            raise e

    def execute_remove(self, animal_id):
        try:
            removed_animal = self.manager.remove_animal(animal_id)
            return {"id": removed_animal.id, "name": removed_animal.name}
        except ValueError as e:
            raise ValueError(str(e))

    def execute_edit(self, animal_id, attr, new_value):
        edit_map = {
            "type": self.manager.edit_animal_type,
            "name": self.manager.edit_animal_name,
            "ability": self.manager.edit_animal_ability,
        }
        try:
            func = edit_map.get(attr)
            if not func:
                raise ValueError("無効な属性です")
            func(animal_id, new_value)
            
        except ValueError as e:
            raise e

    def execute_act(self, choice):
        results = self.manager.act_animal(choice)
        return results
    
    def is_valid_action(self, choice):
        return choice in self.manager.ALLOWED_ACTIONS

    def save(self):
        self.manager.save_to_file()
        return "ローカルデータを保存しました"

    def data_clear(self):
        self.manager.data_clear()
        self.manager.save_to_file()

    def has_unsaved_changes(self):
        return self.manager.is_changed()
