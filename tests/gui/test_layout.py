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
    mgr = MagicMock()
    mgr.SEARCH_MAP = {
        "all": None,
        "id": None,
        "animal_type": None,
        "name": None,
        "ability": None
    }
    mgr.ALLOWED_SORT_KEYS = ["id", "animal_type", "name"]
    return mgr

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
        ("act", "act"),
        ("save", "save"),
        ("clear", "clear_data"),
    ])
    def test_tl_buttons_connection_simple(self, app, button_text_key, method_name):
        """引数なしでControllerメソッドを直接呼ぶボタンの検証"""
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

    def test_remove_button_connection(self, app):
        """削除ボタンが選択データを持ってControllerを呼ぶか検証"""
        expected_text = app.text["label"]["remove"]
        target_button = next(c for c in app.tl_frame.winfo_children() 
                             if isinstance(c, tk.Button) and c.cget("text") == expected_text)
        
        mock_data = [{"id": 1, "name": "Tama"}]
        with patch.object(app, "_get_selected_animals", return_value=mock_data):
            target_button.invoke()
        
        app.ctrl.remove.assert_called_once_with(mock_data)

    def test_edit_button_connection(self, app):
        """編集ボタンが選択IDを持ってControllerを呼ぶか検証"""
        expected_text = app.text["label"]["edit"]
        target_button = next(c for c in app.tl_frame.winfo_children() 
                             if isinstance(c, tk.Button) and c.cget("text") == expected_text)
        
        mock_data = [{"id": 10, "name": "Pochi"}]
        with patch.object(app, "_get_selected_animals", return_value=mock_data):
            target_button.invoke()
        
        app.ctrl.edit.assert_called_once_with(10)


class TestSearchBar:
    def test_search_entry_return(self, app):
        app.search_entry.focus_force()
        app.root.update()
        app.search_entry.event_generate("<Return>")
        app.root.update()
        app.ctrl.search.assert_called_once()

    def test_search_bar_buttons(self, app):
        app.btn_clear.invoke()
        app.ctrl.load.assert_called_once() # Layout.clear_searchはctrl.loadを呼ぶ
        app.btn_search.invoke()
        app.ctrl.search.assert_called_once_with("all", "")

    def test_search_attr_options(self, app, mock_manager):
        """検索範囲の選択肢（Combobox）の内容と初期値を検証"""
        headers = app.text["headers"]
        expected_labels = [headers.get(k, k) for k in mock_manager.SEARCH_MAP.keys()]
        
        assert list(app.search_attr["values"]) == expected_labels
        assert app.search_attr.get() == "all"
        
        app.search_attr.current(3) # name (keys[3]) を選択
        assert app.search_attr.get() == "name"


class TestTreeView:
    def test_columns_setup(self, app):
        expected_columns = ("id", "animal_type", "name")
        assert app.tree_animals["columns"] == expected_columns
        assert app.tree_animals.heading("id")["text"] == app.text["headers"]["id"]
        assert app.tree_animals.heading("animal_type")["text"] == app.text["headers"]["animal_type"]
        assert app.tree_animals.heading("name")["text"] == app.text["headers"]["name"]

    @pytest.mark.parametrize("column_id, expected_sort_key", [
        ("id", "id"),
        ("animal_type", "animal_type"),
        ("name", "name"),
    ])
    def test_column_sort(self, app, column_id, expected_sort_key):
        header_config = app.tree_animals.heading(column_id)
        app.root.tk.call(header_config["command"])
        app.ctrl.sort_tree.assert_called_with(expected_sort_key, "all", "")

    def test_right_click_menu(self, app):
        # Arrange
        item_id = app.tree_animals.insert("", "end", values=(1, "猫", "Tama"))
        app.root.update()

        area = app.tree_animals.bbox(item_id)
        assert area, "項目の描画領域が取得できませんでした"
        ax, ay, aw, ah = area
        click_x, click_y = ax + aw // 2, ay + ah // 2

        root_x = app.tree_animals.winfo_rootx() + click_x
        root_y = app.tree_animals.winfo_rooty() + click_y

        with patch.object(app.tree_menu, "post") as mock_post:
            # Act
            app.tree_animals.event_generate("<Button-3>", x=click_x, y=click_y, rootx=root_x, rooty=root_y)
            app.root.update()
            # Assert
            assert app.tree_animals.selection()[0] == item_id
            mock_post.assert_called_once_with(root_x, root_y)

    def test_menu_commands(self, app):
        """右クリックメニューの各項目がControllerに繋がっているか検証"""
        # Arrange
        mock_data = [{"id": 10, "name": "Pochi"}]
        with patch.object(app, "_get_selected_animals", return_value=mock_data):
            # Act & Assert
            app.tree_menu.invoke(0)
            app.ctrl.edit.assert_called_once_with(10)
            
            app.tree_menu.invoke(1)
            app.ctrl.remove.assert_called_once_with(mock_data)
        

class TestUIUpdateLogic:
    def test_refresh_list(self, app):
        # Arrange
        app.tree_animals.insert("", "end", values=(999, "不明", "消えるべきデータ"))
        animal1 = MagicMock(id=1, animal_type="cat")
        animal1.name = "Tama"
        animal2 = MagicMock(id=2, animal_type="dog")
        animal2.name = "Pochi"
        mock_animals = [animal1, animal2]
        # Act
        app.refresh_list(mock_animals)
        # Assert
        items = app.tree_animals.get_children()
        assert len(items) == 2
        assert app.tree_animals.item(items[0])["values"] == [1, "cat", "Tama"]
        assert app.tree_animals.item(items[1])["values"] == [2, "dog", "Pochi"]