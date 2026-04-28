from cli import menu_printer
from enum import Enum, auto
from core.exceptions import ValidationError, RepositoryError

class FlowResult(Enum):
    TO_MAIN = auto()
    TO_BACK = auto()
    EXIT = auto()

class CliController:
    def __init__(self, manager):
        self.manager = manager
        self.menu_printer = menu_printer

    # --- メインエントリーポイント (main.py から呼び出される主要フロー) ---

    def main_menu(self):
        """アプリケーションのメインループ"""
        # actionsの並びはtext.TEXTS["main"]と揃えること
        actions = [
            self.manage_animal_flow,
            self.manage_list_flow,
            self.search_animal_flow,
            self.exit_manager
        ]
        try:
            while True:
                result = self._execute_menu_loop(
                    self.menu_printer.print_menu,
                    actions
                )
                if result == FlowResult.EXIT:
                    break
        except RepositoryError:
            pass
        except (KeyboardInterrupt, EOFError):
            self.menu_printer.print_error("keyboard_interrupt")
            try:
                self.exit_manager()
            except RepositoryError:
                pass

    def manage_animal_flow(self):
        """動物管理フローメソッド"""
        actions = [
            self.add_animal_flow,
            self.add_random_flow,
            self.remove_animal_flow,
            self.edit_animal_attr_flow,
            self.act_animal_flow
        ]
        return self._execute_menu_loop(
            self.menu_printer.print_manage_animal,
            actions
        )

    def manage_list_flow(self):
        """リスト管理フローメソッド"""
        actions = [
            self.show_animal_list_flow,
            self.sort_list_flow,
            self.clear_data_flow
        ]
        return self._execute_menu_loop(
            self.menu_printer.print_manage_list,
            actions
        )

    def search_animal_flow(self):
        """検索フローメソッド"""
        search_keys = ["all"] + list(self.manager.SEARCH_MAP.keys())
        
        while True:
            # header
            self.menu_printer.print_animal_list(self.manager.get_all_animals())       
            self.menu_printer.print_inline_options("search_choice_header", search_keys)
            # prompt
            attr = self._prompt_for_choice(
                search_keys,
                prompt=self.menu_printer.get_text("prompts", "select_search_attr")
            )
            if attr is None:
                self.menu_printer.print_cancel("search_finished")
                return FlowResult.TO_MAIN
            # input
            keyword = self._prompt_for_input(
                self.menu_printer.get_text("prompts", "input_keyword")
            )
            if keyword is None:
                self.menu_printer.print_cancel("search_reverted")
                continue

            try:
                results = self.manager.search_animal(attr, keyword)
                if results:
                    self.menu_printer.print_animal_list(results)
                    self.menu_printer.print_success("search", count=len(results))
                else:
                    self.menu_printer.print_error("search_not_found")
                return FlowResult.TO_MAIN
            except ValidationError as e:
                self.menu_printer.print_error(e.key, **e.kwargs)
                continue

    def exit_manager(self):
        try:
            self.manager.save_to_file()
            self.menu_printer.print_success("app_exited")
            return FlowResult.EXIT
        except RepositoryError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)
            raise

    def _execute_menu_loop(self, print_func, actions, prompt=None):
        while True:
            print_func()
            action = self._prompt_for_choice(actions, prompt=prompt)
            if action is None:
                return FlowResult.TO_BACK

            result = action()
            if result in (FlowResult.EXIT, FlowResult.TO_MAIN):
                return result


    # --- Manage Animal Actionフロー ---

    def add_animal_flow(self):
        animal_type = self._select_animal_type_flow(self.menu_printer.get_text("prompts", "select_animal_type"))
        if animal_type is None:
            self.menu_printer.print_cancel("add_cancelled")
            return FlowResult.TO_BACK

        prompt = self.menu_printer.get_text("prompts", "name_for_type", type=animal_type)
        name = self._prompt_for_input(prompt)
        if not name:
            self.menu_printer.print_cancel("add_cancelled")
            return FlowResult.TO_BACK
        try:
            self.manager.add_animal(animal_type, name)
            self.menu_printer.print_success("animal_added")
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)

    def add_random_flow(self):
        """ランダムに動物を追加するフロー"""
        count = self._prompt_for_input(self.menu_printer.get_text("prompts", "input_count"),
                                        validator=self._validate_positive_int)
        if count is None:
            self.menu_printer.print_cancel("add_cancelled")
            return FlowResult.TO_BACK

        try:
            added_animals = self.manager.add_random_animal(count)
            self.menu_printer.print_success("random_animals_added", count=count)
            for animal in added_animals:
                self.menu_printer.print_success("animal_added", type_jp=animal.type_jp, name=animal.name)
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)

    def remove_animal_flow(self):
        try:
            animal_id = self._select_animal_id_flow(self.menu_printer.get_text("prompts", "input_id"))
            if animal_id is None:
                self.menu_printer.print_cancel("remove_cancelled")
                return FlowResult.TO_BACK

            removed_animal = self.manager.remove_animal(animal_id)
            self.menu_printer.print_success("animal_removed", name=removed_animal.name)
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)

    def edit_animal_attr_flow(self):
        target_id = self._select_animal_id_flow(self.menu_printer.get_text("prompts", "input_id"))
        if target_id is None:
            self.menu_printer.print_cancel("edit_cancelled")
            return FlowResult.TO_BACK

        editable_keys = self.manager.EDITABLE_ATTRIBUTES
        edit_flows =   [self.edit_type_flow, 
                        self.edit_name_flow, 
                        self.edit_ability_flow]
        self.menu_printer.print_edit_choice(editable_keys)
        selected_flow = self._prompt_for_choice(edit_flows)
        if selected_flow is None:
            self.menu_printer.print_cancel("edit_cancelled")
            return FlowResult.TO_BACK
        return selected_flow(target_id)

    def edit_type_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        # "ID:{target_id} {target_animal.name} の新しい種類を入力"
        prompt = self.menu_printer.get_text("prompts", "new_type_formatted", id=target_id, name=target_animal.name)
        new_type = self._select_animal_type_flow(prompt)
        if new_type is None:
            self.menu_printer.print_cancel("edit_cancelled")
            return FlowResult.TO_BACK

        try:
            self.manager.edit_animal(target_id, "type", new_type)
            self.menu_printer.print_success("animal_type_updated", name=target_animal.name, type=new_type)
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)

    def edit_name_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        # "ID:{target_id} {target_animal.name} の新しい名前を入力"
        prompt = self.menu_printer.get_text("prompts", "new_name_formatted", id=target_id, name=target_animal.name)
        new_name = self._prompt_for_input(prompt)
        if not new_name:
            self.menu_printer.print_cancel("edit_cancelled")
            return FlowResult.TO_BACK
        old_name = target_animal.name
        try:
            self.manager.edit_animal(target_id, "name", new_name)
            #{old_name} の名前を {new_name} に更新しました
            self.menu_printer.print_success("animal_name_updated", old_name=old_name, new_name=new_name)
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)

    def edit_ability_flow(self, target_id):
        target_animal = self.manager.get_animal(target_id)
        abilities = self.manager.get_available_abilities()
        self.menu_printer.print_ability_choice(abilities)
        # "ID:{target_id} {target_animal.name} の新しい特技を入力"
        prompt = self.menu_printer.get_text("prompts", "new_ability_formatted", id=target_id, name=target_animal.name)
        new_ability = self._prompt_for_input(prompt, 
                                             validator=self._validate_ability)
        if new_ability is None:
            self.menu_printer.print_cancel("edit_cancelled")
            return FlowResult.TO_BACK
        try:
            self.manager.edit_animal(target_id, "ability", new_ability)
            # {target_animal.name} の特技を {new_ability} に更新しました
            self.menu_printer.print_success("animal_ability_updated", name=target_animal.name, ability=new_ability)
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)

    def act_animal_flow(self):
        available_actions = self.manager.ALLOWED_ACTIONS
        self.menu_printer.print_inline_options("action_choice_header", available_actions)
        action_name = self._prompt_for_input(self.menu_printer.get_text("prompts", "input_action"), 
                                             validator=lambda x: self._validate_selection_from_list(x, available_actions))
        if action_name is None:
            self.menu_printer.print_cancel("act_cancelled")
            return FlowResult.TO_BACK

        try:
            results = self.manager.act_animal(action_name)
            for result in results:
                self.menu_printer.print_message(result)
            # {len(results)} 件の行動を実行しました
            self.menu_printer.print_success("actions_performed", count=len(results))
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)
            return FlowResult.TO_BACK

    # --- Manage List Actionフロー ---

    def show_animal_list_flow(self):
        try:
            self.menu_printer.print_animal_list(self.manager.get_all_animals())
            return FlowResult.TO_MAIN
        except (ValueError, Exception):
            self.menu_printer.print_error("list_fetch_error")
            return FlowResult.TO_MAIN
    
    def sort_list_flow(self):
        category_keys = self.manager.ALLOWED_SORT_KEYS

        self.menu_printer.print_inline_options("sort_choice_header", category_keys)
        category = self._prompt_for_choice(category_keys)
        if category is None:
            self.menu_printer.print_cancel("sort_cancelled")
            return FlowResult.TO_BACK

        try:
            target_list = self.manager.get_all_animals()
            sorted_list = self.manager.sort_list(target_list, category)
            self.menu_printer.print_animal_list(sorted_list) # type: ignore
            # {category} 順にソートしました
            self.menu_printer.print_success("list_sorted", category=category)
            return FlowResult.TO_MAIN
        except ValidationError as e:
            self.menu_printer.print_error(e.key, **e.kwargs)
            return FlowResult.TO_BACK
        
    def clear_data_flow(self):
        """データを全消去するフロー"""
        self.menu_printer.print_confirm("clear_data_confirmation")
        # 入力待ち。メッセージは print_confirm で表示済みのため簡潔にする
        user_input = self._get_raw_input("> ").strip()
        if user_input.lower() == "yes":
            self.manager.clear_data()
            self.menu_printer.print_success("all_data_cleared")
            return FlowResult.TO_MAIN
        else:
            self.menu_printer.print_cancel("clear_data_cancelled")
            return FlowResult.TO_BACK

    # --- 入力処理共通化/ヘルパーメソッド ---

    def _get_raw_input(self, prompt):
        """実際に標準入力を受け取る唯一の場所。テスト時はここをMock化する。"""
        return input(prompt)

    def _select_animal_id_flow(self, prompt):
        """動物リストを表示し、ユーザーにIDを選択させるフロー"""
        self.menu_printer.print_animal_list(self.manager.get_all_animals())

        return self._prompt_for_input(
            prompt,
            validator=self._validate_animal_id,
            error_msg="invalid_value"
        )

    def _select_animal_type_flow(self, prompt):
        """動物の種類リストを表示し、ユーザーに種類を選択させるフロー"""
        types = self.manager.get_available_animal_types()
        self.menu_printer.print_animal_types(types)

        return self._prompt_for_input(prompt, validator=self._validate_animal_type)

    def _prompt_for_choice(self, choices, prompt=None, allow_cancel=True):
        """汎用的な選択プロンプト。リストまたは辞書を受け取り、ユーザーの選択に対応する値を返す。"""
        if prompt is None:
            prompt = self.menu_printer.get_text("prompts", "select_action")

        choices_map = choices
        if isinstance(choices, list):
            choices_map = {str(i+1): val for i, val in enumerate(choices)}

        while True:
            cancel_text = self.menu_printer.get_text("prompts", "cancel_if_empty") if allow_cancel else ""
            user_input = self._get_raw_input(f"{prompt}{cancel_text}: ").strip()

            if allow_cancel and not user_input:
                return None

            value = choices_map.get(user_input)
            if value is not None:
                return value
            else:
                self.menu_printer.print_error("invalid_selection")

    def _prompt_for_input(self, prompt, validator=None, allow_cancel=True, error_msg="invalid_value"):
        """汎用的な自由入力プロンプト。バリデーションとキャンセル処理を共通化。"""
        while True:
            cancel_text = self.menu_printer.get_text("prompts", "cancel_if_empty") if allow_cancel else ""
            user_input = self._get_raw_input(f"{prompt}{cancel_text}: ").strip()

            if allow_cancel and not user_input:
                return None
            
            if not user_input and not allow_cancel:
                self.menu_printer.print_error("input_required")
                continue

            if validator:
                try:
                    return validator(user_input)
                except (ValueError, IndexError) as e:
                    custom_error = str(e) if str(e) else error_msg
                    self.menu_printer.print_error(custom_error)
            else:
                return user_input

    # --- Validators ---

    def _validate_positive_int(self, text):
        try:
            val = int(text)
        except ValueError:
            raise ValueError("require_int")
            
        if val <= 0:
            raise ValueError("require_positive_int")
        return val

    def _validate_animal_id(self, text):
        try:
            target_id = int(text)
        except ValueError:
            raise ValueError("invalid_value")
            
        if self.manager.get_animal(target_id, raise_error=False) is None:
            raise ValueError("id_not_found")
        return target_id

    def _validate_selection_from_list(self, text, valid_list, error_msg="invalid_value"):
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
        return self._validate_selection_from_list(text, types, "invalid_value")

    def _validate_ability(self, text):
        abilities = self.manager.get_available_abilities()
        return self._validate_selection_from_list(text, abilities, "ability_not_found")
