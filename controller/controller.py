from tkinter import messagebox
from text.loader import set_language, get_text
from typing import Any, Callable

class Controller:
    def __init__(self, layout, manager):
        self.layout = layout
        self.manager = manager
        self.sort_desc = False
        self.last_sort_col = "id"
        set_language(layout.use_lang)
        self.text = get_text()


        if layout.use_mode == "remote":
            from controller.remote_backend import RemoteBackend
            self.backend = RemoteBackend(layout)
        elif layout.use_mode == "local":
            from controller.local_backend import LocalBackend
            self.backend = LocalBackend(layout, manager)
        else:
            self.backend = None

    def _post_action(self, window: object, msg: str) -> None:
        self.load()
        if window:
            window.destroy()
        if msg:
            self.layout.log(msg)

    def _handle_action(self, func: Callable[..., Any], *args: Any, window: object | None=None, 
                       msg: str | None=None, reload: bool = True) -> Any | None:
        try:
            result = func(*args)
            if reload:
                self._post_action(window, msg)
            else:
                if window: window.destroy()
                if msg: self.layout.log(msg)
            return result
        except Exception as e:
            error_msg = self.text["error"]["error_occurred"].format(
                error_type=type(e).__name__,
                error_msg=str(e)
            )
            self.layout.log(error_msg)
            return None


    def add(self) -> None:
        self.layout.open_add_dialog()

    def execute_add(self, animal_type: str, animal_name: str) -> None:
        self._handle_action(
            self.backend.execute_add, animal_type, animal_name,
            window=self.layout.add_window,
            msg=self.text["success"]["animal_added"].format(animal_type=animal_type, animal_name=animal_name))

    def add_random(self) -> None:
        self.layout.open_random_dialog()

    def execute_add_random(self, count: int) -> None:
        self._handle_action(
            self.backend.execute_add_random, count,
            window=self.layout.random_window,
            msg=self.text["success"]["random_animals_added"].format(count=count))

    def remove(self, selected_animal_data: list[dict[str, Any]]) -> None:
        def remove_loop():
            for data in selected_animal_data:
                animal_id = data["id"]
                removed = self.backend.execute_remove(animal_id)
                if removed:
                    msg = self.text["success"]["animal_removed"].format(animal_id=animal_id, animal_name=removed['name'])
                    self.layout.log(msg)

        self._handle_action(remove_loop, window=None, msg=None)

    def edit(self, animal_id: int) -> None:
        self.layout.open_edit_dialog(animal_id)

    def execute_edit(self, animal_id: int, attr: str, new_value: str, display_label: str) -> None:
        if not attr:
            self.layout.log(self.text["error"]["no_selection"])
            return
        self._handle_action(
            self.backend.execute_edit, animal_id, attr, new_value,
            window=self.layout.edit_window,
            msg=self.text["success"]["animal_edit_completed"].format(animal_id=animal_id, edit_mode=display_label or attr)
        )

    def act(self) -> None:
        self.layout.open_act_dialog()

    def execute_act(self, choice: str) -> None:
        if self.backend.is_valid_action(choice) is False:
            self.layout.log(self.text["error"]["invalid_action"])
            return
        results = self._handle_action(
            self.backend.execute_act, choice,
            window=self.layout.act_window,
            msg=None)

        if results:
            for r in results:
                try:
                    msg = self.text["actions"][r["action_key"]][r["animal_type"]]
                    self.layout.log(msg.format(animal_name=r["name"]))

                except (KeyError, AttributeError):
                    fallback = (
                        f"{r['name']} "
                        f"({r['animal_type']}): "
                        f"{r['action_key']}"
                    )

                    self.layout.log(f"[Missing Text] {fallback}")

    def clear_search(self) -> None:
        self.layout.search_entry.delete(0, "end")
        self.layout.refresh_list()

    def search(self, attribute: str, keyword: str) -> None:
        # 検索時は全件ロードをスキップ
        results = self._handle_action(self.backend.execute_search, attribute, keyword, reload=False)
        if results is not None:
            self.layout.refresh_list(results)

    def sort_tree(self, category: str, attribute: str, keyword: str) -> None:
        if self.last_sort_col == category:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_desc = False
            self.last_sort_col = category
        
        # ソート時も自前でrefresh_listを呼ぶため全件ロードはスキップ
        results = self._handle_action(self.backend.execute_search, attribute, keyword, reload=False)
        if results is not None:
            results.sort(key=lambda x: getattr(x, category), reverse=self.sort_desc)
            self.layout.refresh_list(results)
            
    def load(self) -> None:
        try:
            # backendからデータを取得してレイアウトに渡す
            results = self.backend.execute_load()
            self.layout.refresh_list(results)
        except Exception:
            self.layout.log(self.text["error"]["load_error"])

    def save(self) -> None:
        result = self._handle_action(self.backend.save)
        if result is True:
            self.layout.log(self.text["success"]["data_saved"])
        elif result is False:
            self.layout.log(self.text["error"]["api_save_restricted"])

    def clear_data(self) -> None:
        confirm = messagebox.askyesno(
            self.text["confirm"]["decision"],
            self.text["confirm"]["clear_data_gui"]
        )
        if confirm:
            self._handle_action(self.backend.clear_data, msg=self.text["success"]["all_data_cleared"])
        else:
            self.layout.log(self.text["cancel"]["clear_data_cancelled"])
    
    def on_close(self) -> None:
        if self.backend.has_unsaved_changes():
            result = messagebox.askyesnocancel(
                self.text["confirm"]["decision"],
                self.text["confirm"]["save_on_close"]
            )
            if result is True:
                self.save()
                self.layout.root.destroy()
            elif result is False:
                self.layout.root.destroy()
        else:
            self.layout.root.destroy()
