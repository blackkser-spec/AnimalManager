from tkinter import messagebox

class Controller:
    def __init__(self, layout, manager):
        self.layout = layout
        self.manager = manager
        self.sort_desc = False
        self.last_sort_col = "id"

        if layout.use_mode == "remote":
            from controller.remote_backend import RemoteBackend
            self.backend = RemoteBackend(layout)
        elif layout.use_mode == "local":
            from controller.local_backend import LocalBackend
            self.backend = LocalBackend(layout, manager)
        else:
            self.backend = None

    def _post_action(self, window, msg):
        # アクション後は常に最新のリストを取得して反映させる
        self.load()
        if window:
            window.destroy()
        if msg:
            self.layout.log(msg)

    def _handle_action(self, func, *args, window=None, msg=None):
        try:
            result = func(*args)
            self._post_action(window, msg)
            return result
        except Exception as e:
            self.layout.log(f"エラー発生: {type(e).__name__}: {str(e)}")


    def add(self):
        self.layout.open_add_dialog()

    def execute_add(self, animal_type, name):
        self._handle_action(
            self.backend.execute_add, animal_type, name,
            window=self.layout.add_window,
            msg=f"{animal_type} {name} を追加しました")

    def add_random(self):
        self.layout.open_random_dialog()

    def execute_add_random(self, count):
        return self._handle_action(
            self.backend.execute_add_random, count,
            window=self.layout.random_window,
            msg=f"{count} 回のランダム追加に成功しました")

    def remove(self):
        selected = self.layout.tree_animals.selection()
        if not selected:
            self.layout.log("対象を選択してください")
            return

        def remove_loop():
            for item_id in selected:
                item = self.layout.tree_animals.item(item_id)
                animal_id = int(item["values"][0])
                removed = self.backend.execute_remove(animal_id)
                if removed:
                    self.layout.log(f"削除完了: ID:{removed['id']} {removed['name']}")

        self._handle_action(remove_loop, window=None, msg=None)

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

        attr, getter = edit_map[edit_mode]
        self._handle_action(
            self.backend.execute_edit, animal_id, attr, getter(),
            window=self.layout.edit_window,
            msg=f"ID:{animal_id} の {edit_mode}が完了"
        )

    def act(self): 
        self.layout.open_act_dialog()

    def execute_act(self, choice):
        if self.backend.is_valid_action(choice) is False:
            self.layout.log("不正な行動です")
            return
        results = self._handle_action(
            self.backend.execute_act, choice,
            window=self.layout.act_window,
            msg=None)

        if results:
            for r in results:
                self.layout.log(r)
    
    def clear_search(self):
        self.layout.search_entry.delete(0, "end")
        self.layout.refresh_list()

    def search(self):
        attribute = self.layout.search_attr.get()
        keyword = self.layout.search_entry.get()
        try:
            results = self.backend.execute_search(attribute, keyword)
            self.layout.refresh_list(results)
        except Exception as e:
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
            animals = self.backend.execute_search(attribute, keyword)
            # AnimalDTOはdataclassなのでgetattrで属性取得
            animals.sort(key=lambda x: getattr(x, category), reverse=self.sort_desc)
            self.layout.refresh_list(animals)
        except Exception as e:
            self.layout.log(str(e))
            
    def load(self):
        try:
            # backendからデータを取得してレイアウトに渡す
            results = self.backend.execute_load()
            self.layout.refresh_list(results)
        except Exception as e:
            self.layout.log(f"読み込み失敗: {e}")

    def save(self):
        result = self._handle_action(self.backend.save)
        if result:
            self.layout.log(result)

    def clear_data(self):
        confirm = messagebox.askyesno("確認","本当にマネージャーのデータを消去しますか？")
        if confirm:
            self._handle_action(self.backend.clear_data, msg="データを消去しました")
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
