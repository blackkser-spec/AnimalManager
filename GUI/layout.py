import tkinter   as tk
from tkinter import ttk
from controller.controller import Controller
from core.manager import AnimalManager
from text.loader import get_text, set_language

class Layout:
    def __init__(self, root, use_mode=None, use_lang="jp"):
        self.use_mode = use_mode
        self.use_lang = use_lang
        set_language(self.use_lang)
        self.text = get_text()
        if not self.use_mode:
            root.destroy()
            return
        
        # Managerはローカル/APIどちらでも必要（型の定義やキャッシュとして利用可能）
        from core.animal_repository import AnimalRepository
        self.manager = AnimalManager(AnimalRepository("data/animals.json"))
        self.ctrl = Controller(self, self.manager)
        if not self.ctrl:
            root.destroy()
            return

        self.root = root
        self.root.geometry("600x400+200+100")
        self.root.title(self.text["title"]["title"])
        self.root.resizable(False,False)
        self.root.protocol("WM_DELETE_WINDOW", self.ctrl.on_close)
        
        self.create_widgets()
        self.ctrl.load()

    def create_widgets(self):
        """UIウィジェットを生成し、配置する"""
        self._setup_main_layout()
        self._create_topleft_panel()
        self._create_topright_panel()
        self._create_bottomleft_panel()

    def _setup_main_layout(self):
        """メインフレームの生成とグリッドレイアウトの設定"""
        self.tl_frame = tk.Frame(self.root, bg="gray")
        self.tr_frame = tk.Frame(self.root, bg="white")
        self.bl_frame = tk.Frame(self.root, bg="lightblue")
        self.br_frame = tk.Frame(self.root, bg="lightblue")

        self.tl_frame.grid(row=0, column=0, rowspan=4, columnspan=2, sticky="nsew")
        self.tr_frame.grid(row=0, column=2, rowspan=4, columnspan=4, sticky="nsew")
        self.bl_frame.grid(row=4, column=0, rowspan=2, columnspan=5, sticky="nsew")
        self.br_frame.grid(row=4, column=5, rowspan=2, sticky="nsew")        

        for i in range(5):
            self.root.grid_rowconfigure(i, weight=1)
        for i in range(5, 6):
            self.root.grid_rowconfigure(i, weight=3)
        for i in range(5):
            self.root.grid_columnconfigure(i, weight=1)
        for i in range(5, 6):
            self.root.grid_columnconfigure(i, weight=1)

    def _create_topleft_panel(self):
        """左パネルのボタン群を生成する"""
        buttons = [
            (self.text["label"]["add"],        self.ctrl.add),
            (self.text["label"]["add_random"], self.ctrl.add_random),
            (self.text["label"]["remove"],     self._on_remove_clicked),
            (self.text["label"]["edit"],       self._on_edit_clicked),
            (self.text["label"]["act"],        self.ctrl.act),
            (self.text["label"]["save"],       self.ctrl.save), 
            (self.text["label"]["clear"],      self.ctrl.clear_data)
        ]
        for i, (text, method_name) in enumerate(buttons):
            tk.Button(self.tl_frame,text=text, command=method_name, width=10).pack(expand=True, fill="both")

        # TreeView helper
    def _get_selected_animals(self):
        """現在選択されているアイテムの情報をリストで返す"""
        selected = self.tree_animals.selection()
        results = []
        for item_id in selected:
            item = self.tree_animals.item(item_id)
            results.append({"id": int(item["values"][0]), "name": item["values"][2]})
        return results

    def _on_remove_clicked(self):
        data = self._get_selected_animals()
        if not data:
            return self.log(self.text["error"]["no_selection"])
        self.ctrl.remove(data)

    def _on_edit_clicked(self):
        data = self._get_selected_animals()
        if not data:
            return self.log(self.text["error"]["no_selection"])
        self.ctrl.edit(data[0]["id"])

    def _create_topright_panel(self):
        """右パネルのTreeviewと関連ウィジェットを生成する"""
        # --- 検索バーエリア ---
        search_frame = tk.Frame(self.tr_frame, bg="#f0f0f0", pady=4)
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        # アイコンラベル
        tk.Label(search_frame, text="🔍", bg="#f0f0f0", fg="#555").pack(side=tk.LEFT, padx=(8, 2))
        # 検索ジャンル
        self.search_keys = list(self.manager.SEARCH_MAP.keys())
        search_labels = [self.text["headers"].get(k, k) for k in self.search_keys]
        self.search_attr = ttk.Combobox(
            search_frame,
            values=search_labels,
            width=8,
            state="readonly"
        )
        self.search_attr.pack(side=tk.LEFT, padx=2)
        self.search_attr.bind("<<ComboboxSelected>>", lambda e: e.widget.selection_clear())
        self.search_attr.current(0)
        # getをラップして翻訳ラベルではなく内部キー("all"等)を返すように拡張
        self.search_attr.get = lambda: self.search_keys[self.search_attr.current()]

        # 検索入力欄
        self.search_entry = tk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        self.search_entry.bind("<Return>", lambda e: self.ctrl.search(self.search_attr.get(), self.search_entry.get())) # Enterキーで実行

        # 実行ボタン & クリアボタン
        self.btn_search = tk.Button(search_frame, text=self.text["label"]["search"], command=lambda: self.ctrl.search(self.search_attr.get(), self.search_entry.get()), width=6, bg="#e1e1e1")
        self.btn_search.pack(side=tk.LEFT, padx=2)
        self.btn_clear = tk.Button(search_frame, text=self.text["icon"]["clear"], command=self.ctrl.clear_search, width=3, bg="#ffdddd")
        self.btn_clear.pack(side=tk.LEFT, padx=(2, 8))

        # --- Treeviewエリア ---
        columns = tuple(self.manager.ALLOWED_SORT_KEYS)
        self.tree_animals = ttk.Treeview(self.tr_frame, columns=columns, show="headings")
        self.tree_animals.heading("id",          text=self.text["headers"]["id"],          command=lambda: self.ctrl.sort_tree("id", self.search_attr.get(), self.search_entry.get()))
        self.tree_animals.heading("animal_type", text=self.text["headers"]["animal_type"], command=lambda: self.ctrl.sort_tree("animal_type", self.search_attr.get(), self.search_entry.get()))
        self.tree_animals.heading("name",        text=self.text["headers"]["name"],        command=lambda: self.ctrl.sort_tree("name", self.search_attr.get(), self.search_entry.get()))
        self.tree_animals.column ("id",          width=10,  anchor="w")
        self.tree_animals.column ("animal_type", width=50,  anchor="w")
        self.tree_animals.column ("name",        width=200, anchor="w")

        self.scrollbar = tk.Scrollbar(self.tr_frame)
        self.tree_menu = tk.Menu(self.tree_animals, tearoff=0)
        self.tree_menu.add_command(label=self.text["label"]["edit"], command=self._on_edit_clicked)
        self.tree_menu.add_command(label=self.text["label"]["remove"], command=self._on_remove_clicked)
        self.tree_animals.bind("<Button-3>", self.show_tree_menu)
    
        self.tree_animals.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.tree_animals.yview)

        # row=1 に配置 (row=0は検索バー)
        self.tree_animals.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        self.tr_frame.grid_rowconfigure(0, weight=0) # 検索バーは固定
        self.tr_frame.grid_rowconfigure(1, weight=1) # Treeviewは伸縮
        self.tr_frame.grid_columnconfigure(0, weight=1)

    def show_tree_menu(self, event):
        """Treeview右クリックでメニューを表示する"""
        # クリックされた位置のアイテムIDを取得
        item = self.tree_animals.identify_row(event.y)
        if not item:
            return
        # クリックされたアイテムを選択状態にする
        self.tree_animals.selection_set(item)
        # メニューを表示
        self.tree_menu.post(event.x_root, event.y_root)

    def _create_bottomleft_panel(self):
        self.log_text = tk.Text(self.bl_frame, height=2, width=40)
        scroll = tk.Scrollbar(self.bl_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scroll.set, state="disabled")

        self.bl_frame.grid_rowconfigure(0, weight=1)
        self.bl_frame.grid_columnconfigure(0, weight=1)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")
    # -----------------
    # dialog設定
    # -----------------
    def open_add_dialog(self):
        self.add_window = self.create_dialog(self.text["label"]["add"])
        #種別Combobox
        tk.Label(self.add_window, text=self.text["headers"]["type"]).pack(pady=2)
        animal_types = self.manager.get_available_animal_types()
        self.add_type_combo = ttk.Combobox(self.add_window, values=animal_types, state="readonly")
        self.add_type_combo.pack(pady=5)
        self.add_type_combo.bind("<<ComboboxSelected>>", lambda e: e.widget.selection_clear())
        if animal_types:
            self.add_type_combo.current(0)
        #名前Entry
        tk.Label(self.add_window, text=self.text["headers"]["name"]).pack(pady=2)
        self.add_name_entry = tk.Entry(self.add_window)
        self.add_name_entry.pack(pady=5)
        #決定/キャンセルボタン
        self.create_ok_cancel_btn(
            self.add_window,
            lambda: self.ctrl.execute_add(self.add_type_combo.get(),self.add_name_entry.get()))
    
    def open_random_dialog(self):
        self.random_window = self.create_dialog(self.text["label"]["add_random"])
        #個数Entry
        tk.Label(self.random_window, text=self.text["label"]["random_count"]).pack(pady=5)
        frame = tk.Frame(self.random_window)
        frame.pack(pady=5)

        buttons = [(self.text["label"]["count_1"], 1), 
                   (self.text["label"]["count_5"], 5), 
                   (self.text["label"]["count_10"],10)]
        for i, (text, count) in enumerate(buttons):
            tk.Button(
                frame,
                text=text,
                command=lambda c=count: self.ctrl.execute_add_random(c),
                width=8
                ).grid(row=0, column=i, padx=1)
        tk.Button(self.random_window, text=self.text["confirm"]["cancel"],
            command=self.random_window.destroy,
            width=8).pack(side=tk.BOTTOM, pady=10)
            
    def open_edit_dialog(self, animal_id):
        """動物情報を編集するためのダイアログを表示し、入力ウィジェットを動的に切り替える"""
        self.edit_window = self.create_dialog(self.text["label"]["edit"], height=200)
        # 1. 編集項目の選択エリア
        ttk.Label(self.edit_window, text=self.text["label"]["edit_item"]).pack(pady=1)
        # プログラム内部用のキー名と、画面表示用のラベルをペアで管理
        self.edit_options = [
            ("animal_type", self.text["label"]["edit_modes"]["type"]),
            ("name",        self.text["label"]["edit_modes"]["name"]),
            ("ability",     self.text["label"]["edit_modes"]["ability"])
        ]
        self.edit_keys = [opt[0] for opt in self.edit_options]
        edit_labels = [opt[1] for opt in self.edit_options]
        # 編集項目選択Combobox
        self.edit_target = ttk.Combobox(self.edit_window, values=edit_labels, state="readonly")
        self.edit_target.pack(pady=5)
        if edit_labels:
            self.edit_target.current(0)
        self.edit_target.bind("<<ComboboxSelected>>", self.change_editor)

        # 2. 入力ウィジェットの生成エリア
        editor_frame = tk.Frame(self.edit_window)
        editor_frame.pack(pady=5, fill="x", expand=True)

        # 種別 (Combobox)
        type_label = ttk.Label(editor_frame, text=self.text["label"]["new_type"])
        self.type_combo = ttk.Combobox(
            editor_frame,
            values=self.manager.get_available_animal_types(),
            state="readonly"
        )
        # 名前 (Entry)
        name_label = ttk.Label(editor_frame, text=self.text["label"]["new_name"])
        self.name_entry = tk.Entry(editor_frame)
        
        # 特技 (Combobox)
        ability_label = ttk.Label(editor_frame, text=self.text["label"]["new_ability"])
        self.ability_combo = ttk.Combobox(
            editor_frame,
            values=self.manager.get_available_abilities(),
            state="readonly"
        )

        # change_editorが内部キーでウィジェットを特定できるようにマッピングを保持
        self.edit_widgets = {
            "animal_type": (type_label, self.type_combo),
            "name":        (name_label, self.name_entry),
            "ability":     (ability_label, self.ability_combo)
        }

        def get_selected_attr():
            idx = self.edit_target.current()
            return self.edit_keys[idx] if idx >= 0 else None
        
        def get_display_label():
            idx = self.edit_target.current()
            return self.edit_options[idx][1] if idx >= 0 else ""
        
        def get_current_value():
            """表示ウィジェットから入力内容を取得"""
            attr = get_selected_attr()
            if attr == "animal_type": return self.type_combo.get()
            if attr == "name":        return self.name_entry.get()
            if attr == "ability":     return self.ability_combo.get()
            return ""
        # 4. 下部ボタンの配置
        self.create_ok_cancel_btn(
            self.edit_window, 
            lambda: self.ctrl.execute_edit(
                animal_id, 
                get_selected_attr(), 
                get_current_value(), 
                get_display_label()
            )
        )
        self.update_editor_widgets()

    def update_editor_widgets(self, event=None):
        """選択された項目に応じて入力ウィジェットを切り替える。初期表示時はevent=Noneで呼ばれる"""
        choice_idx = self.edit_target.current()

        if choice_idx < 0: return

        choice_key = self.edit_options[choice_idx][0]

        for label, field in self.edit_widgets.values():
            label.pack_forget()
            field.pack_forget()
        
        label, field = self.edit_widgets[choice_key]
        label.pack(pady=1)
        field.pack(pady=5)

    def open_act_dialog(self):
        self.act_window = self.create_dialog(self.text["label"]["act"])
        ttk.Label(self.act_window,text=self.text["label"]["act_type"]).pack(pady=1)
        self.act_target = ttk.Combobox(
            self.act_window,
            values=self.manager.ALLOWED_ACTIONS,
            state="readonly"
        )
        self.act_target.pack(pady=5)
        self.act_target.bind("<<ComboboxSelected>>", lambda e: e.widget.selection_clear())
        self.create_ok_cancel_btn(self.act_window, lambda: self.ctrl.execute_act(self.act_target.get()))
    
    def create_dialog(self, title, width=240, height=160):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(f"{width}x{height}")
        return window

    def create_ok_cancel_btn(self, parent, ok_cmd):
        btn_frame = tk.Frame(parent)
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        tk.Button(btn_frame, text=self.text["confirm"]["decision"],
                  command=ok_cmd,
                  width=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text=self.text["confirm"]["cancel"],
                  command=parent.destroy,
                  width=8).pack(side=tk.LEFT, padx=5)

        
    def refresh_list(self, animals=None):
        for item in self.tree_animals.get_children():
            self.tree_animals.delete(item)

        if animals is None:
            return

        for animal in animals:
            self.tree_animals.insert("", "end", values=(animal.id, animal.animal_type, animal.name))
