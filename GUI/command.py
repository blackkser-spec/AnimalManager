from tkinter import messagebox

class Command:
    def __init__(self, layout, manager):
        self.layout = layout
        self.manager = manager
        self.sort_desc = False     # 降順フラグ
        self.last_sort_col = "id"  # 最後にソートした列
        
    def add(self):
        self.layout.open_add_dialog()

    def execute_add(self, animal_type, name):
        try:
            self.manager.add_animal(animal_type, name)
            self.layout.refresh_list()
            self.layout.add_window.destroy()
            self.layout.log(f"{animal_type} の {name} を追加しました")
        except ValueError as e:
            self.layout.log(str(e)) 

    def random_add(self):
        self.layout.open_random_dialog()

    def execute_random_add(self, count):
        try:
            self.manager.add_random_animal(count)
            self.layout.refresh_list()
            self.layout.random_window.destroy()
            self.layout.log(f"{count}回 動物を追加しました")
        except ValueError as e:
            self.layout.log(str(e))

    def remove(self):
        selected = self.layout.tree_animals.selection()
        if not selected:
            self.layout.log("対象を選択してください") 
            return

        for item_id in selected:
            try:
                item = self.layout.tree_animals.item(item_id)
                animal_id = int(item["values"][0])  # カラム0(ID)を整数として取得
                removed_animal = self.manager.remove_animal(animal_id)
                if removed_animal:
                    self.layout.log(f"ID:{animal_id} の {removed_animal.name} を削除しました")

            except ValueError as e:
                self.layout.log(str(e))
        # 複数選択を考慮し、ループの外でリストを一度だけ更新します
        self.layout.refresh_list()

    def edit(self):
        selected = self.layout.tree_animals.selection()
        if not selected:
            self.layout.log("対象を選択してください")
            return
        item = self.layout.tree_animals.item(selected[0])
        animal_id = int(item["values"][0])  # カラム0(ID)を整数として取得
        self.layout.open_edit_dialog(animal_id)

    def execute_edit(self):
        animal_id = self.layout.edit_target_id
        edit_mode = self.layout.edit_target.get()

        try:
            if edit_mode == "種類の変更":
                new_type = self.layout.type_combo.get()
                self.manager.edit_animal_type(animal_id, new_type)
            elif edit_mode == "名前の変更":
                new_name = self.layout.name_entry.get()
                self.manager.edit_animal_name(animal_id, new_name)
            elif edit_mode == "特技の変更":
                new_ability = self.layout.ability_combo.get()
                self.manager.edit_animal_ability(animal_id, new_ability)
            else:
                return # 何も選択されていない場合は何もしない
            self.layout.refresh_list()
            self.layout.edit_window.destroy()
            self.layout.log(f"編集完了: {edit_mode}")
        except ValueError as e:
            self.layout.log(str(e))

    def act(self):
        self.layout.open_act_dialog()

    def execute_act(self, choice):
        """UIからの選択をmanagerに直接渡し実行する"""
        if not choice:
            self.layout.log("行動を選択してください")
            self.layout.act_window.destroy()
            return
        # UIからの選択("voice"など)を直接managerに渡す
        results = self.manager.act_animal(choice)
        # 結果をコンソールに出力（将来的にはb_frameに表示）
        for result in results:
            self.layout.log(result)
        
        self.layout.act_window.destroy()
        
    def search(self):
        attribute = self.layout.search_attr.get()
        keyword = self.layout.search_entry.get()
        animals = self.manager.search_animal(attribute, keyword)
        self.layout.refresh_list(animals)

    def clear_search(self):
        self.layout.search_entry.delete(0, "end")
        self.layout.refresh_list()

    def sort_tree(self, category):
        # 同じ列なら昇順・降順を反転、違う列なら昇順リセット
        if self.last_sort_col == category:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_desc = False
            self.last_sort_col = category
        
        # 検索窓に入力されている内容に基づいてリストを取得
        attribute = self.layout.search_attr.get()
        keyword = self.layout.search_entry.get()
        animals = self.manager.search_animal(attribute, keyword)
        
        # 取得したリストをソート
        animals.sort(key=lambda x: getattr(x, category))
        if self.sort_desc:
            animals.reverse()
        self.layout.refresh_list(animals)
    
    def save(self):
        try:
            self.manager.save_to_file()
            self.layout.log("データを保存しました")
        except Exception as e:
            self.layout.log(f"データの保存に失敗{e}")

    def list_clear(self):
        confirm = messagebox.askyesno("確認","本当にマネージャーのデータを消去しますか？")
        if confirm:
            self.manager.data_reset()
            self.manager.save_to_file()
            self.layout.refresh_list()
            self.layout.log("データを消去しました")
    
    def on_close(self):
        if self.manager.is_changed():
            result = messagebox.askyesnocancel(
                "確認", "変更された要素があります。保存しますか？"
            )
            if result is True:
                self.manager.save_to_file()
                self.layout.root.destroy()
            elif result is False:
                self.layout.root.destroy()
            else:
                return
        else:
            self.layout.root.destroy()
