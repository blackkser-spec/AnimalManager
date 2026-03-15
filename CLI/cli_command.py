from CLI import menu_printer

class CliCommand:
    def __init__(self, manager):
        self.manager = manager
        self.menu_printer = menu_printer


    def manage_animal_flow(self):
        while True:
            menu_printer.print_manage_animal()
            choice = input("実行する処理のindexを入力: ")
            if choice == "0":
                return
            actions = {
                "1":self.add_animal_flow,
                "2":self.add_random_flow,
                "3":self.remove_animal_flow,
                "4":self.edit_animal_attribute_flow,
                "5":self.act_animal_flow}

            action = actions.get(choice)
            if action:
                action()
            else:
                self.menu_printer.print_error("無効な選択です")
            
    def add_animal_flow(self):
        animal_type = self._select_animal_type_flow("追加したい種類のindexまたは英名を入力")
        if animal_type is None:
            self.menu_printer.print_cancel("動物の追加をキャンセルしました")
            return

        name = input(f"{animal_type} につける名前を入力(未入力でキャンセル): ")
        if not name:
            self.menu_printer.print_cancel("名前の入力をキャンセルしました")
            return
        try:
            self.manager.add_animal(animal_type, name)
            self.menu_printer.print_success("動物を追加しました")
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def add_random_flow(self):
        while True:
            input_time = input("追加したい回数を入力(0でキャンセル): ")
            if input_time == "0":
                return
            try:
                exe_time = int(input_time)
                if exe_time <= 0:
                    raise ValueError
                break
            except ValueError:
                self.menu_printer.print_error("無効な値が入力されました")
                continue
        
        added_animals = self.manager.add_random_animal(exe_time)
        self.menu_printer.print_success(f"ランダムに{exe_time}回動物を追加しました")
        for animal in added_animals:
            print(f"{animal.type_jp} の {animal.name} を追加しました")


    def remove_animal_flow(self):
        animal_id = self._select_animal_id_flow("削除したい動物のIDを入力")
        if animal_id is None:
            self.menu_printer.print_cancel("動物の削除をキャンセルしました")
            return

        removed_animal = self.manager.remove_animal(animal_id)
        if removed_animal:
            self.menu_printer.print_success(f"{removed_animal.name} を削除しました")

    def edit_animal_attribute_flow(self):
        edit_map = {
            "1": self.edit_type,
            "2": self.edit_name,
            "3": self.edit_ability
            }
        self.menu_printer.print_edit_choice()
        choice = input("実行する処理のindexを入力(0でキャンセル): ")
        if choice == "0":
            return
        elif choice in edit_map:
            action = edit_map[choice]
            action()
        else:
            self.menu_printer.print_error("無効な選択です")

    def edit_type(self):
        target_id = self._select_animal_id_flow("変更したい動物のIDを入力")
        if target_id is None:
            self.menu_printer.print_cancel("種類の変更をキャンセルしました")
            return

        target_animal = self.manager.get_animal(target_id)
        prompt = f"ID:{target_id} {target_animal.name} の新しい種類を入力"
        new_type = self._select_animal_type_flow(prompt)
        if new_type is None:
            self.menu_printer.print_cancel("種類の変更をキャンセルしました")
            return

        updated_animal = self.manager.edit_animal_type(target_id, new_type)
        self.menu_printer.print_success(f"{updated_animal.name} の種類を {new_type} に更新しました")

    def edit_name(self):
        print("nameを編集します")

    def edit_ability(self):
        print("abilityを編集します")

    def act_animal_flow(self):
        pass

    def manage_list_flow(self):
        while True:
            menu_printer.print_manage_list()
            choice = input("実行する処理のindexを入力: ")
            if choice == "0":
                return
            actions = {
                "1":self.show_animal_list_flow,
                "2":self.sort_list_flow,
                "3":self.reset_manager_flow}
            action = actions.get(choice)
            if action:
                action()
            else:
                self.menu_printer.print_error("無効な選択です")
                continue

    def show_animal_list_flow(self):
        self.menu_printer.print_animal_list(self.manager.get_all_animals())
        return True
    
    def sort_list_flow(self):
        category_map = {
            "1": "id",
            "2": "type_en",
            "3": "name"
        }        
        self.menu_printer.print_sort_category()
        while True:
            choice = input("実行する処理のindexを入力: ")
            if choice == "0":
                return
            elif choice in category_map:
                category = category_map[choice]
                sorted_list = self.manager.sort_list(category)
                self.menu_printer.print_animal_list(sorted_list)
            else:
                self.menu_printer.print_error("無効な選択です")
                continue
        
    def reset_manager_flow(self):
        self.menu_printer.print_confirm("本当にリセットする場合 yes を入力してください")
        choice = input()
        if choice.lower().strip() != "yes":
            self.menu_printer.print_cancel("リセットをキャンセルしました")
            return
        else:
            self.manager.data_reset()
            self.menu_printer.print_success("データをリセットしました")


    def search_animal_flow(self):
        search_map = {"1": "ID", "2": "種類", "3": "名前", "4": "特技"}        
        self.menu_printer.print_search_choice()

        while True:
            choice = input()
            if choice == "0":
                return
            elif choice in ["1", "2", "3", "4"]:
                attr = search_map[choice]
                keyword = input("検索キーワードを入力してください: ")
                break
            else:
                self.menu_printer.print_error("無効な選択です")
                continue

        if self.manager.search_animal(attr, keyword):
            self.menu_printer.print_animal_list(self.manager.search_animal(attr, keyword))
            return
        else:
            self.menu_printer.print_error("検索結果が見つかりませんでした")
            return

    def exit_manager(self):        
        self.manager.save_to_file()
        return True

    # --- Private Helper Methods ---

    def _select_animal_id_flow(self, prompt):
        """動物リストを表示し、ユーザーにIDを選択させるフロー"""
        self.menu_printer.print_animal_list(self.manager.get_all_animals())
        while True:
            target_id_str = input(f"{prompt}(0でキャンセル): ")
            if target_id_str == "0":
                return None
            try:
                target_id = int(target_id_str)
                if self.manager.get_animal(target_id) is None:
                    self.menu_printer.print_error("無効なIDが入力されました")
                    continue
                return target_id
            except ValueError:
                self.menu_printer.print_error("IDは数値で入力してください")

    def _select_animal_type_flow(self, prompt):
        """動物の種類リストを表示し、ユーザーに種類を選択させるフロー"""
        types = self.manager.get_available_animal_types()
        self.menu_printer.print_animal_types(types)
        while True:
            choice = input(f"{prompt}(0でキャンセル): ").strip()
            if choice == "0":
                return None
            try:
                if choice.isdigit():
                    idx = int(choice) - 1
                    if not (0 <= idx < len(types)): raise IndexError
                    return types[idx]
                else:
                    if choice not in types: raise ValueError
                    return choice
            except (ValueError, IndexError):
                self.menu_printer.print_error("無効な値が入力されました")
