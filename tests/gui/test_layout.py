import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from GUI.layout import Layout

@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()

@pytest.fixture
def app(root, mock_manager):
    with patch('GUI.layout.Controller') as mock_ctrl_class, \
         patch('GUI.layout.AnimalManager', return_value=mock_manager), \
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
        assert app.root.title() == "Tkinter Test"
        assert isinstance(app.tree_animals, tk.ttk.Treeview)
        assert isinstance(app.log_text, tk.Text)
        assert isinstance(app.search_entry, tk.Entry)


class TestLeftPanel:
    @pytest.mark.parametrize("button_text, method_name", [
        ("動物追加", "add"),
        ("ランダム追加", "add_random"),
        ("動物削除", "remove"),
        ("動物編集", "edit"),
        ("動物行動", "act"),
        ("データ保存", "save"),
        ("データ消去", "clear_data"),
    ])
    def test_tl_buttons_connection(self, app, button_text, method_name):
        """左パネルの各ボタンがControllerの対応するメソッドを正しく呼び出すか検証"""
        target_button = None
        for child in app.tl_frame.winfo_children():
            if isinstance(child, tk.Button) and child.cget("text") == button_text:
                target_button = child
                break
        
        assert target_button is not None, f"Button with text '{button_text}' not found"
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
        expected = ["すべて", "ID", "種類", "名前", "特技"]
        assert list(app.search_attr["values"]) == expected
        assert app.search_attr.get() == "すべて"
        
        app.search_attr.set("名前")
        assert app.search_attr.get() == "名前"


class TestTreeView:
    def test_columns_setup(self, app):
        expected_columns = ("id", "type", "name")
        assert app.tree_animals["columns"] == expected_columns
        assert app.tree_animals.heading("id")["text"] == "ID"
        assert app.tree_animals.heading("type")["text"] == "種類"
        assert app.tree_animals.heading("name")["text"] == "名前"

    @pytest.mark.parametrize("column_id, expected_sort_key", [
        ("id", "id"),
        ("type", "type_en"),
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
        animal1 = MagicMock(id=1, type_jp="猫")
        animal1.name = "Tama"
        animal2 = MagicMock(id=2, type_jp="犬")
        animal2.name = "Pochi"
        mock_animals = [animal1, animal2]
        
        app.refresh_list(mock_animals)
        
        items = app.tree_animals.get_children()
        assert len(items) == 2
        assert app.tree_animals.item(items[0])["values"] == [1, "猫", "Tama"]
        assert app.tree_animals.item(items[1])["values"] == [2, "犬", "Pochi"]