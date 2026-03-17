from CLI import menu_printer

class CliCommand:
    def __init__(self, manager):
        self.manager = manager
        self.menu_printer = menu_printer


    def manage_animal_flow(self):
        """動物管理フローメソッド"""
        while True:
            self.menu_printer.print_manage_animal()
            actions = {
                "1":self.add_animal_flow,
                "2":self.add_random_flow,
                "3":self.remove_animal_flow,
                "4":self.edit_animal_attribute_flow,
                "5":self.act_animal_flow}
            action = self._prompt_for_choice("実行する処理のindexを入力", actions)
            if action is None:
                return # Cancelled
            # アクションがTrueを返したら、このメニューも終了してmainに戻る
            if action():
                return
            
    def add_animal_flow(self):
        animal_type = self._select_animal_type_flow("追加したい種類のindexまたは英名を入力")
        if animal_type is None:
            self.menu_printer.print_cancel("動物の追加をキャンセルしました")
            return

        prompt = f"{animal_type} につける名前を入力"
        name = self._prompt_for_input(prompt, cancel_msg="名前の入力をキャンセルしました")
        if not name:
            return
        try:
            self.manager.add_animal(animal_type, name)
            self.menu_printer.print_success("動物を追加しました")
            return True
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def add_random_flow(self):
        """ランダムに動物を追加するフロー"""
        def positive_int_validator(text):
            val = int(text)
            if val <= 0:
                raise ValueError("1以上の数値を入力してください")
            return val

        count = self._prompt_for_input("追加したい回数を入力", validator=positive_int_validator)
        if count is None:
            return

        added_animals = self.manager.add_random_animal(count)
        self.menu_printer.print_success(f"ランダムに{count}回動物を追加しました")
        for animal in added_animals:
            print(f"{animal.type_jp} の {animal.name} を追加しました")
            return True


    def remove_animal_flow(self):
        animal_id = self._select_animal_id_flow("削除したい動物のIDを入力")
        if animal_id is None:
            return

        removed_animal = self.manager.remove_animal(animal_id)
        self.menu_printer.print_success(f"{removed_animal.name} を削除しました")
        return True

    def edit_animal_attribute_flow(self):
        while True:
            target_id = self._select_animal_id_flow("変更したい動物のIDを入力", cancel_msg="属性の変更をキャンセルしました")
            if target_id is None:
                return

            edit_map = {
                "1": self.edit_type_flow,
                "2": self.edit_name_flow,
                "3": self.edit_ability_flow
            }
            self.menu_printer.print_edit_choice()
            action = self._prompt_for_choice("実行する処理のindexを入力", edit_map, cancel_msg="属性の変更をキャンセルしました")
            if action is None:
                return
            if action(target_id): # Execute the chosen edit flow
                return True

    def edit_type_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        prompt = f"ID:{target_id} {target_animal.name} の新しい種類を入力"
        new_type = self._select_animal_type_flow(prompt, cancel_msg="種類の変更をキャンセルしました")
        if new_type is None:
            return

        try:
            self.manager.edit_animal_type(target_id, new_type)
            self.menu_printer.print_success(f"{target_animal.name} の種類を {new_type} に更新しました")
            return True
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def edit_name_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        prompt = f"ID:{target_id} {target_animal.name} の新しい名前を入力"
        new_name = self._prompt_for_input(prompt, cancel_msg="名前の変更をキャンセルしました")
        if not new_name:
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

        def ability_validator(text):
            if text.isdigit():
                idx = int(text) - 1
                if 0 <= idx < len(abilities):
                    return abilities[idx]
            elif text in abilities:
                return text
            raise ValueError("リストにない特技です")

        prompt = f"ID:{target_id} {target_animal.name} の新しい特技を入力"
        new_ability = self._prompt_for_input(prompt, validator=ability_validator, cancel_msg="特技の変更をキャンセルしました")
        if new_ability is None:
            return
        try:
            self.manager.edit_animal_ability(target_id, new_ability)
            self.menu_printer.print_success(f"{target_animal.name} の特技を {new_ability} に更新しました")
            return True
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def act_animal_flow(self):
        # ユーザーに提示する選択肢と内部的なアクション名のマッピング
        action_map = {
            "1": "voice",
            "2": "fly",
            "3": "swim"
        }
        self.menu_printer.print_act_choice()

        def action_validator(choice):
            choice = choice.lower()
            if choice in action_map: # "1", "2", "3"
                return action_map[choice]
            if choice in action_map.values(): # "voice", "fly", "swim"
                return choice
            raise ValueError("無効な選択です")

        action_name = self._prompt_for_input("実行する特技名またはindexを入力", validator=action_validator)
        if action_name is None:
            return

        results = self.manager.act_animal(action_name)
        for result in results:
            print(result)
        return True

    def manage_list_flow(self):
        while True:
            self.menu_printer.print_manage_list()
            actions = {
                "1":self.show_animal_list_flow,
                "2":self.sort_list_flow,
                "3":self.reset_manager_flow}
            action = self._prompt_for_choice("実行する処理のindexを入力", actions)
            if action is None:
                return
            if action():
                return

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
        category = self._prompt_for_choice("実行する処理のindexを入力", category_map)
        if category is None:
            return

        sorted_list = self.manager.sort_list(category)
        self.menu_printer.print_animal_list(sorted_list)
        return True
        
    def reset_manager_flow(self):
        self.menu_printer.print_confirm("本当にリセットする場合 yes を入力してください")
        choice = input().strip().lower()
        if choice != "yes":
            self.menu_printer.print_cancel("リセットをキャンセルしました")
            return
        else:
            self.manager.data_reset()
            self.menu_printer.print_success("データをリセットしました")


    def search_animal_flow(self):
        search_map = {"1": "ID", "2": "種類", "3": "名前", "4": "特技"} 
        self.menu_printer.print_animal_list(self.manager.get_all_animals())       
        self.menu_printer.print_search_choice()

        attr = self._prompt_for_choice("検索項目をindexで入力", search_map, allow_cancel=False)

        keyword = input("検索キーワードを入力してください: ").strip()
        results = self.manager.search_animal(attr, keyword)
        if results:
            self.menu_printer.print_animal_list(results)
        else:
            self.menu_printer.print_error("検索結果が見つかりませんでした")
        return True

    def exit_manager(self):        
        self.manager.save_to_file()
        return True

    # --- 入力処理共通化/ヘルパーメソッド ---

    def _select_animal_id_flow(self, prompt, cancel_msg=None):
        """動物リストを表示し、ユーザーにIDを選択させるフロー"""
        self.menu_printer.print_animal_list(self.manager.get_all_animals())

        def id_validator(text):
            target_id = int(text)
            if self.manager.get_animal(target_id) is None:
                raise ValueError("そのIDの動物は存在しません")
            return target_id

        return self._prompt_for_input(
            prompt,
            validator=id_validator,
            cancel_msg=cancel_msg,
            error_msg="IDは数値で入力してください"
        )

    def _select_animal_type_flow(self, prompt, cancel_msg=None):
        """動物の種類リストを表示し、ユーザーに種類を選択させるフロー"""
        types = self.manager.get_available_animal_types()
        self.menu_printer.print_animal_types(types)

        def type_validator(choice):
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(types):
                    return types[idx]
            elif choice in types:
                return choice
            raise ValueError("無効な値が入力されました")

        return self._prompt_for_input(prompt, validator=type_validator, cancel_msg=cancel_msg)

    def _prompt_for_choice(self, prompt, choices_map, allow_cancel=True, cancel_msg=None):
        """汎用的な選択プロンプト。ユーザーの選択に対応する値を返す。"""
        while True:
            cancel_text = "(未入力でキャンセル)" if allow_cancel else ""
            user_input = input(f"{prompt}{cancel_text}: ").strip()

            if allow_cancel and not user_input:
                if cancel_msg:
                    self.menu_printer.print_cancel(cancel_msg)
                return None

            value = choices_map.get(user_input)
            if value is not None:
                return value
            else:
                self.menu_printer.print_error("無効な選択です")

    def _prompt_for_input(self, prompt, validator=None, allow_cancel=True, cancel_msg=None, error_msg="無効な値が入力されました"):
        """汎用的な自由入力プロンプト。バリデーションとキャンセル処理を共通化。"""
        while True:
            cancel_text = "(未入力でキャンセル)" if allow_cancel else ""
            user_input = input(f"{prompt}{cancel_text}: ").strip()

            if allow_cancel and not user_input:
                if cancel_msg:
                    self.menu_printer.print_cancel(cancel_msg)
                return None
            
            if not user_input and not allow_cancel:
                self.menu_printer.print_error("入力は必須です")
                continue

            if validator:
                try:
                    return validator(user_input)
                except (ValueError, IndexError) as e:
                    # バリデータからエラーメッセージが渡された場合はそれを使用
                    custom_error = str(e) if str(e) else error_msg
                    self.menu_printer.print_error(custom_error)
            else:
                return user_input
