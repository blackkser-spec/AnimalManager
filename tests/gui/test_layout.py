import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from gui.layout import Layout

@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()

@pytest.fixture
def app(root, mock_manager):
    with patch('gui.layout.Controller') as mock_ctrl_class, \
         patch('gui.layout.AnimalManager', return_value=mock_manager), \
         patch('core.animal_repository.AnimalRepository.load', return_value={"animals": []}), \
         patch('core.animal_repository.AnimalRepository.save', return_value=True):
        
        view = Layout(root, use_mode="local")
        # view.ctrl は Controller のモックインスタンス
        # view.manager は mock_manager フィクスチャのインスタンスになる
        yield view

@pytest.fixture
def mock_manager():
    return MagicMock()

class TestInitialization:
    def test_load_success(self, app):
        app.ctrl.load.assert_called_once()

    def test_initial_ui_state(self, app):
        assert app.root.title() == app.text["title"]["title"]
        assert isinstance(app.tree_animals, tk.ttk.Treeview)
        assert isinstance(app.log_text, tk.Text)
        assert isinstance(app.search_entry, tk.Entry)


class TestLeftPanel:
    @pytest.mark.parametrize("button_text_key, method_name", [
        ("add", "add"),
        ("add_random", "add_random"),
        ("remove", "remove"),
        ("edit", "edit"),
        ("act", "act"),
        ("save", "save"),
        ("clear", "clear_data"),
    ])
    def test_tl_buttons_connection(self, app, button_text_key, method_name):
        """左パネルの各ボタンがControllerの対応するメソッドを正しく呼び出すか検証"""
        # 翻訳辞書から期待されるテキストを取得
        expected_text = app.text["label"][button_text_key]
        
        target_button = None
        for child in app.tl_frame.winfo_children():
            if isinstance(child, tk.Button) and child.cget("text") == expected_text:
                target_button = child
                break
        
        assert target_button is not None, f"Button with text '{button_text_key}' not found"
        target_button.invoke()
        getattr(app.ctrl, method_name).assert_called_once()


class TestSearchBar:
    def test_search_entry_return(self, app):
        app.search_entry.focus_force()
        app.root.update()
        app.search_entry.event_generate("<Return>")
        app.root.update()
        app.ctrl.search.assert_called_once()

    def test_search_bar_buttons(self, app):
        app.btn_clear.invoke()
        app.ctrl.clear_search.assert_called_once()
        app.btn_search.invoke()
        app.ctrl.search.assert_called_once()

    def test_search_attr_options(self, app):
        """検索範囲の選択肢（Combobox）の内容と初期値を検証"""
        expected = ["all", "id", "animal_type", "name", "ability"]
        assert list(app.search_attr["values"]) == expected
        assert app.search_attr.get() == "all"
        
        app.search_attr.set("name")
        assert app.search_attr.get() == "name"


class TestTreeView:
    def test_columns_setup(self, app):
        expected_columns = ("id", "type", "name")
        assert app.tree_animals["columns"] == expected_columns
        assert app.tree_animals.heading("id")["text"] == app.text["headers"]["id"]
        assert app.tree_animals.heading("type")["text"] == app.text["headers"]["type"]
        assert app.tree_animals.heading("name")["text"] == app.text["headers"]["name"]

    @pytest.mark.parametrize("column_id, expected_sort_key", [
        ("id", "id"),
        ("type", "animal_type"),
        ("name", "name"),
    ])
    def test_column_sort(self, app, column_id, expected_sort_key):
        header_config = app.tree_animals.heading(column_id)
        app.root.tk.call(header_config["command"])
        app.ctrl.sort_tree.assert_called_with(expected_sort_key)

    def test_right_click_menu(self, app):
        item_id = app.tree_animals.insert("", "end", values=(1, "猫", "Tama"))
        app.root.update()

        area = app.tree_animals.bbox(item_id)
        assert area, "項目の描画領域が取得できませんでした"
        ax, ay, aw, ah = area
        click_x, click_y = ax + aw // 2, ay + ah // 2

        root_x = app.tree_animals.winfo_rootx() + click_x
        root_y = app.tree_animals.winfo_rooty() + click_y

        with patch.object(app.tree_menu, "post") as mock_post:
            app.tree_animals.event_generate("<Button-3>", x=click_x, y=click_y, rootx=root_x, rooty=root_y)
            app.root.update()

            assert app.tree_animals.selection()[0] == item_id
            mock_post.assert_called_once_with(root_x, root_y)

    def test_menu_commands(self, app):
        """右クリックメニューの各項目がControllerに繋がっているか検証"""
        app.tree_menu.invoke(0) # 編集
        app.ctrl.edit.assert_called_once()
        app.tree_menu.invoke(1) # 削除
        app.ctrl.remove.assert_called_once()
        

class TestUIUpdateLogic:
    def test_refresh_list(self, app):
        app.tree_animals.insert("", "end", values=(999, "不明", "消えるべきデータ"))
        animal1 = MagicMock(id=1, animal_type="cat")
        animal1.name = "Tama"
        animal2 = MagicMock(id=2, animal_type="dog")
        animal2.name = "Pochi"
        mock_animals = [animal1, animal2]
        
        app.refresh_list(mock_animals)
        
        items = app.tree_animals.get_children()
        assert len(items) == 2
        assert app.tree_animals.item(items[0])["values"] == [1, "cat", "Tama"]
        assert app.tree_animals.item(items[1])["values"] == [2, "dog", "Pochi"]