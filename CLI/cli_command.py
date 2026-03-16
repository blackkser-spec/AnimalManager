from CLI import menu_printer

class CliCommand:
    def __init__(self, manager):
        self.manager = manager
        self.menu_printer = menu_printer


    def manage_animal_flow(self):
        """動物管理フローメソッド"""
        while True:
            self.menu_printer.print_manage_animal()
            choice = input("実行する処理のindexを入力: ")
            if not choice:
                return
            actions = {
                "1":self.add_animal_flow,
                "2":self.add_random_flow,
                "3":self.remove_animal_flow,
                "4":self.edit_animal_attribute_flow,
                "5":self.act_animal_flow}

            action = actions.get(choice)
            if action:
                # アクションがTrueを返したら、このメニューも終了してmainに戻る
                if action():
                    return
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
            return True
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def add_random_flow(self):
        """ランダムに動物を追加するフロー"""
        while True:
            input_count = input("追加したい回数を入力(未入力でキャンセル): ")
            if not input_count:
                return
            try:
                count = int(input_count)
                if count <= 0:
                    raise ValueError
                break
            except ValueError:
                self.menu_printer.print_error("無効な値が入力されました")
                continue
        
        added_animals = self.manager.add_random_animal(count)
        self.menu_printer.print_success(f"ランダムに{count}回動物を追加しました")
        for animal in added_animals:
            print(f"{animal.type_jp} の {animal.name} を追加しました")
            return True


    def remove_animal_flow(self):
        animal_id = self._select_animal_id_flow("削除したい動物のIDを入力")
        if animal_id is None:
            self.menu_printer.print_cancel("動物の削除をキャンセルしました")
            return

        removed_animal = self.manager.remove_animal(animal_id)
        if removed_animal:
            self.menu_printer.print_success(f"{removed_animal.name} を削除しました")
            return True
        else:
            self.menu_printer.print_error("動物が見つかりませんでした")
            return

    def edit_animal_attribute_flow(self):
        while True:
            target_id = self._select_animal_id_flow("変更したい動物のIDを入力")
            if target_id is None:
                self.menu_printer.print_cancel("属性の変更をキャンセルしました")
                return

            edit_map = {
                "1": self.edit_type_flow,
                "2": self.edit_name_flow,
                "3": self.edit_ability_flow
                }
            self.menu_printer.print_edit_choice()
            choice = input("実行する処理のindexを入力(未入力でキャンセル): ")
            if not choice:
                self.menu_printer.print_cancel("属性の変更をキャンセルしました")
                return
            elif choice in edit_map:
                action = edit_map[choice]
                result = action(target_id)
                if result is True:
                    return True
            else:
                self.menu_printer.print_error("無効な選択です")

    def edit_type_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        prompt = f"ID:{target_id} {target_animal.name} の新しい種類を入力"
        new_type = self._select_animal_type_flow(prompt).strip()
        if new_type is None:
            self.menu_printer.print_cancel("種類の変更をキャンセルしました")
            return

        try:
            self.manager.edit_animal_type(target_id, new_type)
            self.menu_printer.print_success(f"{target_animal.name} の種類を {new_type} に更新しました")
            return True
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def edit_name_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        prompt = f"ID:{target_id} {target_animal.name} の新しい名前を入力(未入力でキャンセル)"
        new_name = input(prompt).strip()
        if not new_name:
            self.menu_printer.print_cancel("名前の変更をキャンセルしました")
            return
        
        old_name = target_animal.name
        try:
            self.manager.edit_animal_name(target_id, new_name)
            self.menu_printer.print_success(f"{old_name} の名前を {new_name} に更新しました")
            return True
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def edit_ability_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        abilities = self.manager.get_available_abilities()
        self.menu_printer.print_ability_choice(abilities)
        while True:
            prompt = f"ID:{target_id} {target_animal.name} の新しい特技を入力(未入力でキャンセル)"
            new_ability = input(prompt).strip()

            if not new_ability:
                self.menu_printer.print_cancel("特技の変更をキャンセルしました")
                return
            elif new_ability not in abilities:
                self.menu_printer.print_error("無効な値が入力されました")
                continue
            else:
                try:
                    self.manager.edit_animal_ability(target_id, new_ability)
                    self.menu_printer.print_success(f"{target_animal.name} の特技を {new_ability} に更新しました")
                    return True
                except ValueError as e:
                    self.menu_printer.print_error(str(e))

    def act_animal_flow(self):
        self.menu_printer.print_act_choice()
        while True:
            choice = input("特技名かindexを入力(未入力でキャンセル): ")
            if not choice:
                return
            try:
                if choice.isdigit():
                    idx = int(choice) -2
                    if not (0 <= idx < len(self.manager.get_available_abilities())): raise IndexError
                    choice = self.manager.get_available_abilities()[idx]
                elif choice not in self.manager.get_available_abilities(): raise ValueError
                else:
                    self.menu_printer.print_error("無効な値が入力されました")
                    continue
            except (IndexError, ValueError):
                self.menu_printer.print_error("存在しない特技です")
                continue
            results = self.manager.act_animal(choice)
            for result in results:
                print(result)
            return True  

    def manage_list_flow(self):
        while True:
            self.menu_printer.print_manage_list()
            choice = input("実行する処理のindexを入力(未入力でキャンセル): ")
            if not choice:
                return
            actions = {
                "1":self.show_animal_list_flow,
                "2":self.sort_list_flow,
                "3":self.reset_manager_flow}
            action = actions.get(choice)
            if action:
                if action():
                    return
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
            choice = input("実行する処理のindexを入力(未入力でキャンセル): ")
            if not choice:
                return
            elif choice in category_map:
                category = category_map[choice]
                sorted_list = self.manager.sort_list(category)
                self.menu_printer.print_animal_list(sorted_list)
                return True
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
        self.menu_printer.print_animal_list(self.manager.get_all_animals())       
        self.menu_printer.print_search_choice()

        while True:
            choice = input()
            if not choice:
                return
            elif choice in ["1", "2", "3", "4"]:
                attr = search_map[choice]
                keyword = input("検索キーワードを入力してください: ")
                break
            else:
                self.menu_printer.print_error("無効な選択です")
                continue

        results = self.manager.search_animal(attr, keyword)
        if results:
            self.menu_printer.print_animal_list(results)
            return
        else:
            self.menu_printer.print_error("検索結果が見つかりませんでした")
            return

    def exit_manager(self):        
        self.manager.save_to_file()
        return True

    # --- 入力処理共通化メソッド ---

    def _select_animal_id_flow(self, prompt):
        """動物リストを表示し、ユーザーにIDを選択させるフロー"""
        self.menu_printer.print_animal_list(self.manager.get_all_animals())
        while True:
            target_id_str = input(f"{prompt}(未入力でキャンセル): ").strip()
            if not target_id_str:
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
            choice = input(f"{prompt}(未入力でキャンセル): ").strip()
            if not choice:
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
