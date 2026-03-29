from tkinter import messagebox

class BaseController:
    def __init__(self, layout, manager):
        self.layout = layout
        self.manager = manager
        self.sort_desc = False
        self.last_sort_col = "id"

        if type(self) is BaseController:
            if layout.use_mode == "remote":
                from controller.remote import RemoteController
                self.backend = RemoteController(layout, manager)
            elif layout.use_mode == "local":
                from controller.local import LocalController
                self.backend = LocalController(layout, manager)
            else:
                self.backend = None
        else:
            self.backend = None

    def _post_action(self, window, msg):
        self.layout.refresh_list()
        if window:
            window.destroy()
        if msg:
            self.layout.log(msg)

    def add(self):
        self.layout.open_add_dialog()

    def execute_add(self, animal_type, name):
        try:
            self.backend.execute_add(animal_type, name)
            self._post_action(window=self.layout.add_window, msg=f"{animal_type} の {name} を追加しました")
        except Exception as e:
            self.layout.log(str(e))

    def add_random(self):
        self.layout.open_random_dialog()

    def execute_add_random(self, count):
        try:
            self.backend.execute_add_random(count)
            self._post_action(window=self.layout.random_window, msg=f"{count}回 動物を追加しました")
        except Exception as e:
            self.layout.log(str(e))

    def remove(self):
        selected = self.layout.tree_animals.selection()
        if not selected:
            self.layout.log("対象を選択してください")
            return

        for item_id in selected:
            try:
                item = self.layout.tree_animals.item(item_id)
                animal_id = int(item["values"][0])

                removed_animal = self.backend.execute_remove(animal_id)
                if removed_animal:
                    self.layout.log(f"削除完了: ID:{removed_animal['id']} {removed_animal['name']}")
            except Exception as e:
                self.layout.log(f"{e}")

        self._post_action(window=None, msg=None)

    def edit(self):
        selected = self.layout.tree_animals.selection()
        if not selected:
            self.layout.log("対象を選択してください")
            return
        item = self.layout.tree_animals.item(selected[0])
        animal_id = int(item["values"][0])
        self.layout.open_edit_dialog(animal_id)

    def execute_edit(self):
        animal_id = self.layout.edit_target_id
        edit_mode = self.layout.edit_target.get()
        edit_map = {
            "種類の変更": ("type", self.layout.type_combo.get),
            "名前の変更": ("name", self.layout.name_entry.get),
            "特技の変更": ("ability", self.layout.ability_combo.get),
        }
        if edit_mode not in edit_map:
            self.layout.log("編集項目を選択してください")
            return
        try:
            # edit_mapをattr, getterに分解する
            attr, getter = edit_map[edit_mode]
            self.backend.execute_edit(animal_id, attr, getter())
            self._post_action(window=self.layout.edit_window, msg="編集完了")
        except Exception as e:
            self.layout.log(str(e))

    def act(self): 
        self.layout.open_act_dialog()

    def execute_act(self, choice):
        if self.backend.is_valid_action(choice) is False:
            self.layout.log("不正な行動です")
            return
        try:
            results = self.backend.execute_act(choice)
            if not results:
                self.layout.log("実行可能な動物が見つかりませんでした")
            else:
                for r in results:
                    self.layout.log(r)

            self._post_action(window=self.layout.act_window, msg=None)
            
        except Exception as e:
            self.layout.log(str(e))
    
    def clear_search(self):
        self.layout.search_entry.delete(0, "end")
        self.layout.refresh_list()

    def search(self):
        attribute = self.layout.search_attr.get()
        keyword = self.layout.search_entry.get()
        try:
            animals = self.manager.search_animal(attribute, keyword)
            self.layout.refresh_list(animals)
        except ValueError as e:
            self.layout.log(str(e))

    def sort_tree(self, category):
        if self.last_sort_col == category:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_desc = False
            self.last_sort_col = category
        
        attribute = self.layout.search_attr.get()
        keyword = self.layout.search_entry.get()
        try:
            animals = self.manager.search_animal(attribute, keyword)
            animals.sort(key=lambda x: getattr(x, category))
            if self.sort_desc:
                animals.reverse()
            self.layout.refresh_list(animals)
        except ValueError as e:
            self.layout.log(str(e))

    def save(self):
        try:
            msg = self.backend.save()
            self._post_action(window=None, msg=msg or "データを保存しました")
        except Exception as e:
            self.layout.log(f"保存失敗: {e}")

    def data_clear(self):
        confirm = messagebox.askyesno("確認","本当にマネージャーのデータを消去しますか？")
        if confirm:
            self.backend.data_clear()
            self._post_action(window=None, msg="データを消去しました")
        else:
            self.layout.log("データ消去をキャンセルしました")
    
    def on_close(self):
        if self.backend.has_unsaved_changes():
            result = messagebox.askyesnocancel("確認", "変更内容を保存しますか？")
            if result is True:
                self.save()
                self.layout.root.destroy()
            elif result is False:
                self.layout.root.destroy()
        else:
            self.layout.root.destroy()
