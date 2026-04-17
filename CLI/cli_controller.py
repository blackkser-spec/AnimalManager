from CLI import menu_printer

class CliController:
    def __init__(self, manager):
        self.manager = manager
        self.menu_printer = menu_printer


    # --- メインエントリーポイント (main.py から呼び出される主要フロー) ---

    def main_menu(self):
        """アプリケーションのメインループを開始します"""
        actions = {
            "1": self.manage_animal_flow,
            "2": self.manage_list_flow,
            "3": self.search_animal_flow,
            "4": self.exit_manager}
        try:
            while True:
                result = self._execute_menu_loop(self.menu_printer.print_menu, actions, "実行する処理のindexを入力")
                if result == "EXIT":
                    break
        except IOError:
            pass
        except (KeyboardInterrupt, EOFError):
            print("\n中断されました。終了します。")
            try:
                self.exit_manager()
            except IOError:
                pass

    def manage_animal_flow(self):
        """動物管理フローメソッド"""
        actions = {
            "1": self.add_animal_flow,
            "2": self.add_random_flow,
            "3": self.remove_animal_flow,
            "4": self.edit_animal_attr_flow,
            "5": self.act_animal_flow}
        return self._execute_menu_loop(self.menu_printer.print_manage_animal, actions, "実行する処理のindexを入力")

    def manage_list_flow(self):
        """リスト管理フローメソッド"""
        actions = {
            "1": self.show_animal_list_flow,
            "2": self.sort_list_flow,
            "3": self.clear_data_flow}
        return self._execute_menu_loop(self.menu_printer.print_manage_list, actions, "実行する処理のindexを入力")

    def search_animal_flow(self):
        """検索フローメソッド"""
        search_map = {"1": "ID", "2": "種類", "3": "名前", "4": "特技"} 
        
        while True:
            self.menu_printer.print_animal_list(self.manager.get_all_animals())       
            self.menu_printer.print_search_choice()

            attr = self._prompt_for_choice("検索項目をindexで入力", search_map, cancel_msg="検索を終了します")
            if attr is None:
                return "TO_MAIN"

            keyword = self._prompt_for_input("検索するキーワードを入力してください",
                                            cancel_msg="検索項目の選択に戻ります")
            if keyword is None:
                continue  # 属性選択のループ先頭に戻る

            try:
                results = self.manager.search_animal(attr, keyword)
                if results:
                    self.menu_printer.print_animal_list(results)
                else:
                    self.menu_printer.print_error("検索結果が見つかりませんでした")
                return "TO_MAIN"
            except ValueError as e:
                self.menu_printer.print_error(str(e))
                continue

    def exit_manager(self):
        try:
            self.manager.save_to_file()
            self.menu_printer.print_success("AnimalManagerを終了します")
            return "EXIT"
        except IOError as e:
            self.menu_printer.print_error(str(e))
            raise

    def _execute_menu_loop(self, print_func, actions, prompt):
        while True:
            print_func()
            action = self._prompt_for_choice(prompt, actions)
            if action is None:
                return "TO_BACK"

            result = action()
            if result in ("EXIT", "TO_MAIN"):
                return result


    # --- 個別のアクションフロー ---

    def add_animal_flow(self):
        animal_type = self._select_animal_type_flow("追加したい種類のindexまたは英名を入力")
        if animal_type is None:
            self.menu_printer.print_cancel("追加をキャンセルしました")
            return "TO_BACK"
        prompt = f"{animal_type} につける名前を入力"
        name = self._prompt_for_input(prompt, cancel_msg="名前の入力をキャンセルしました")
        if not name:
            return "TO_BACK"
        try:
            self.manager.add_animal(animal_type, name)
            self.menu_printer.print_success("動物を追加しました")
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def add_random_flow(self):
        """ランダムに動物を追加するフロー"""
        count = self._prompt_for_input("追加したい回数を入力",
                                        validator=self._validate_positive_int)
        if count is None:
            self.menu_printer.print_cancel("追加をキャンセルしました")
            return "TO_BACK"

        try:
            added_animals = self.manager.add_random_animal(count)
            self.menu_printer.print_success(f"ランダムに{count}回動物を追加しました")
            for animal in added_animals:
                print(f"{animal.type_jp} の {animal.name} を追加しました")
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def remove_animal_flow(self):
        try:
            animal_id = self._select_animal_id_flow("削除したい動物のIDを入力")
            if animal_id is None:
                self.menu_printer.print_cancel("削除をキャンセルしました")
                return "TO_BACK"

            removed_animal = self.manager.remove_animal(animal_id)
            self.menu_printer.print_success(f"{removed_animal.name} を削除しました")
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def edit_animal_attr_flow(self):
        target_id = self._select_animal_id_flow("変更したい動物のIDを入力", 
                                                cancel_msg="属性の変更をキャンセルしました")
        if target_id is None:
            return "TO_BACK"

        edit_flow_map = {
            "1": self.edit_type_flow,
            "2": self.edit_name_flow,
            "3": self.edit_ability_flow
        }
        self.menu_printer.print_edit_choice()
        selected_flow = self._prompt_for_choice("実行する処理のindexを入力", 
                                            edit_flow_map, 
                                            cancel_msg="属性の変更をキャンセルしました")
        if selected_flow is None:
            return "TO_BACK"
        return selected_flow(target_id)

    def edit_type_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        prompt = f"ID:{target_id} {target_animal.name} の新しい種類を入力"
        new_type = self._select_animal_type_flow(prompt, cancel_msg="種類の変更をキャンセルしました")
        if new_type is None:
            return "TO_BACK"

        try:
            self.manager.edit_animal(target_id, "type", new_type)
            self.menu_printer.print_success(f"{target_animal.name} の種類を {new_type} に更新しました") # type: ignore
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def edit_name_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        prompt = f"ID:{target_id} {target_animal.name} の新しい名前を入力"
        new_name = self._prompt_for_input(prompt, cancel_msg="名前の変更をキャンセルしました")
        if not new_name:
            return "TO_BACK"
        old_name = target_animal.name
        try:
            self.manager.edit_animal(target_id, "name", new_name)
            self.menu_printer.print_success(f"{old_name} の名前を {new_name} に更新しました") # type: ignore
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def edit_ability_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        abilities = self.manager.get_available_abilities()
        self.menu_printer.print_ability_choice(abilities)

        prompt = f"ID:{target_id} {target_animal.name} の新しい特技を入力"
        new_ability = self._prompt_for_input(prompt, 
                                             validator=self._validate_ability, 
                                             cancel_msg="特技の変更をキャンセルしました")
        if new_ability is None:
            return "TO_BACK"
        try:
            self.manager.edit_animal(target_id, "ability", new_ability)
            self.menu_printer.print_success(f"{target_animal.name} の特技を {new_ability} に更新しました") # type: ignore
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def act_animal_flow(self):
        self.menu_printer.print_act_choice()
        action_name = self._prompt_for_input("実行する特技名またはindexを入力", 
                                             validator=self._validate_action)
        if action_name is None:
            self.menu_printer.print_cancel("行動をキャンセルしました")
            return "TO_BACK"

        try:
            results = self.manager.act_animal(action_name)
            for result in results:
                print(result)
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))

    def show_animal_list_flow(self):
        try:
            self.menu_printer.print_animal_list(self.manager.get_all_animals())
            return "TO_MAIN"
        except (ValueError, Exception) as e:
            self.menu_printer.print_error(f"リストの取得に失敗しました: {e}")
            return "TO_MAIN"
    
    def sort_list_flow(self):
        category_map = {
            "1": "id",
            "2": "type_en",
            "3": "name"
        }        
        self.menu_printer.print_sort_category()
        category = self._prompt_for_choice("実行する処理のindexを入力", category_map)
        if category is None:
            self.menu_printer.print_cancel("ソートをキャンセルしました")
            return "TO_BACK"

        try:
            target_list = self.manager.get_all_animals()
            sorted_list = self.manager.sort_list(target_list, category)
            self.menu_printer.print_animal_list(sorted_list) # type: ignore
            return "TO_MAIN"
        except ValueError as e:
            self.menu_printer.print_error(str(e))
        
    def clear_data_flow(self):
        """データを全消去するフロー"""
        self.menu_printer.print_confirm("本当に消去する場合 yes を入力してください")
        user_input = self._get_raw_input("> ")
        if user_input != "yes":
            self.menu_printer.print_cancel("データの消去をキャンセルしました")
            return "TO_BACK"
        else:
            self.manager.clear_data()
            self.menu_printer.print_success("データを消去しました")
            return "TO_MAIN"

    # --- 入力処理共通化/ヘルパーメソッド ---

    def _get_raw_input(self, prompt):
        """実際に標準入力を受け取る唯一の場所。テスト時はここをMock化する。"""
        return input(prompt)

    def _select_animal_id_flow(self, prompt, cancel_msg=None):
        """動物リストを表示し、ユーザーにIDを選択させるフロー"""
        self.menu_printer.print_animal_list(self.manager.get_all_animals())

        return self._prompt_for_input(
            prompt,
            validator=self._validate_animal_id,
            cancel_msg=cancel_msg,
            error_msg="IDは数値で入力してください"
        )

    def _select_animal_type_flow(self, prompt, cancel_msg=None):
        """動物の種類リストを表示し、ユーザーに種類を選択させるフロー"""
        types = self.manager.get_available_animal_types()
        self.menu_printer.print_animal_types(types)

        return self._prompt_for_input(prompt, validator=self._validate_animal_type, cancel_msg=cancel_msg)

    def _prompt_for_choice(self, prompt, choices_map, allow_cancel=True, cancel_msg=None):
        """汎用的な選択プロンプト。ユーザーの選択に対応する値を返す。"""
        while True:
            cancel_text = "(未入力でキャンセル)" if allow_cancel else ""
            user_input = self._get_raw_input(f"{prompt}{cancel_text}: ").strip()

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
            user_input = self._get_raw_input(f"{prompt}{cancel_text}: ").strip()

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

    # --- Validators ---

    def _validate_positive_int(self, text):
        val = int(text)
        if val <= 0:
            raise ValueError("1以上の数値を入力してください")
        return val

    def _validate_animal_id(self, text):
        target_id = int(text)
        if self.manager.get_animal(target_id, raise_error=False) is None:
            raise ValueError("そのIDの動物は存在しません")
        return target_id

    def _validate_selection_from_list(self, text, valid_list, error_msg="無効な値です"):
        """数値(index)または文字列でリストから選択を検証する共通ロジック"""
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(valid_list):
                return valid_list[idx]
        elif text in valid_list:
            return text
        raise ValueError(error_msg)

    def _validate_animal_type(self, text):
        types = self.manager.get_available_animal_types()
        return self._validate_selection_from_list(text, types, "無効な値が入力されました")

    def _validate_ability(self, text):
        abilities = self.manager.get_available_abilities()
        return self._validate_selection_from_list(text, abilities, "リストにない特技です")

    def _validate_action(self, text):
        action_map = {
            "1": "voice",
            "2": "fly",
            "3": "swim"
        }
        text = text.lower()
        if text in action_map:
            return action_map[text]
        if text in action_map.values():
            return text
        raise ValueError("無効な選択です")
