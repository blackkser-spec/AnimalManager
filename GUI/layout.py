import tkinter   as tk
from tkinter import ttk
from controller.controller import Controller
from core.manager import AnimalManager

class Layout:
    def __init__(self, root, use_mode=None):
        self.use_mode = use_mode
        if not self.use_mode:
            root.destroy()
            return
        
        # Managerはローカル/APIどちらでも必要（型の定義やキャッシュとして利用可能）
        from core.storage import JsonStorage  #これは何か
        self.manager = AnimalManager(JsonStorage("data/animals.json"))
        self.ctrl = Controller(self, self.manager)
        if not self.ctrl:
            root.destroy()
            return

        self.root = root
        self.root.geometry("600x400+200+100")
        self.root.title("Tkinter Test")
        self.root.resizable(False,False)
        self.root.protocol("WM_DELETE_WINDOW", self.ctrl.on_close)
        
        self.create_widgets()
        self.manager.load_from_file()
        self.refresh_list()

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
        buttons = [("動物追加", self.ctrl.add), ("ランダム追加", self.ctrl.add_random),
                   ("動物削除", self.ctrl.remove), ("動物編集", self.ctrl.edit),
                   ("動物行動", self.ctrl.act), ("データ保存", self.ctrl.save),
                   ("データ消去", self.ctrl.data_clear)]
        for i, (text, method_name) in enumerate(buttons):
            tk.Button(self.tl_frame,text=text, command=method_name, width=10).pack(expand=True, fill="both")

    def _create_topright_panel(self):
        """右パネルのTreeviewと関連ウィジェットを生成する"""
        # --- 検索バーエリア ---
        search_frame = tk.Frame(self.tr_frame, bg="#f0f0f0", pady=4)
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        # アイコンラベル
        tk.Label(search_frame, text="🔍", bg="#f0f0f0", fg="#555").pack(side=tk.LEFT, padx=(8, 2))
        # 検索ジャンル
        self.search_attr = ttk.Combobox(
            search_frame,
            values=["すべて","ID", "種類", "名前", "特技"],
            width=8,
            state="readonly"
        )
        self.search_attr.pack(side=tk.LEFT, padx=2)
        self.search_attr.current(0)
        # 検索入力欄
        self.search_entry = tk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        self.search_entry.bind("<Return>", lambda event: self.ctrl.search()) # Enterキーで実行

        # 実行ボタン & クリアボタン
        tk.Button(search_frame, text="検索", command=self.ctrl.search, width=6, bg="#e1e1e1").pack(side=tk.LEFT, padx=2)
        tk.Button(search_frame, text="×", command=self.ctrl.clear_search, width=3, bg="#ffdddd").pack(side=tk.LEFT, padx=(2, 8))

        # --- Treeviewエリア ---
        columns = ("id", "type", "name")
        self.tree_animals = ttk.Treeview(self.tr_frame, columns=columns, show="headings")
        self.tree_animals.heading("id",   text="ID",   command=lambda: self.ctrl.sort_tree("id"))
        self.tree_animals.heading("type", text="種類", command=lambda: self.ctrl.sort_tree("type_en"))
        self.tree_animals.heading("name", text="名前", command=lambda: self.ctrl.sort_tree("name"))
        self.tree_animals.column ("id",   width=10,  anchor="w")
        self.tree_animals.column ("type", width=50,  anchor="w")
        self.tree_animals.column ("name", width=200, anchor="w")

        self.scrollbar = tk.Scrollbar(self.tr_frame)
        self.tree_menu = tk.Menu(self.tree_animals, tearoff=0)
        self.tree_menu.add_command(label="編集", command=self.ctrl.edit)
        self.tree_menu.add_command(label="削除", command=self.ctrl.remove)
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

        # bl_frame内でgridを使いウィジェットを配置することで、bl_frame自体のサイズが子のウィジェットによって変更されるのを防ぎます
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
        self.add_window = self.create_dialog("動物追加")
        #種別Combobox
        tk.Label(self.add_window, text="種類").pack(pady=2)
        animal_types = self.manager.get_available_animal_types()
        self.add_type_combo = ttk.Combobox(self.add_window, values=animal_types, state="readonly")
        self.add_type_combo.pack(pady=5)
        if animal_types:
            self.add_type_combo.current(0)
        #名前Entry
        tk.Label(self.add_window, text="名前").pack(pady=2)
        self.add_name_entry = tk.Entry(self.add_window)
        self.add_name_entry.pack(pady=5)
        #決定/キャンセルボタン
        self.create_ok_cancel_btn(
            self.add_window,
            lambda: self.ctrl.execute_add(self.add_type_combo.get(),self.add_name_entry.get()))
    
    def open_random_dialog(self):
        self.random_window = self.create_dialog("ランダム追加")
        #個数Entry
        tk.Label(self.random_window, text="追加する回数").pack(pady=5)
        frame = tk.Frame(self.random_window)
        frame.pack(pady=5)

        buttons = [(" 1回", 1), (" 5回", 5), ("10回", 10)]
        for i, (text, count) in enumerate(buttons):
            tk.Button(
                frame,
                text=text,
                command=lambda c=count: self.ctrl.execute_add_random(c),
                width=8
                ).grid(row=0, column=i, padx=1)
        tk.Button(self.random_window, text="キャンセル",
            command=self.random_window.destroy,
            width=8).pack(side=tk.BOTTOM, pady=10)
            
    def open_edit_dialog(self, animal_id):
        self.edit_window = self.create_dialog("登録情報編集", height=200)
        self.edit_target_id = animal_id
        # 編集項目combobox
        ttk.Label(self.edit_window, text="編集項目").pack(pady=1)
        self.edit_target = ttk.Combobox(
            self.edit_window,
            values=["種類の変更", "名前の変更", "特技の変更"],
            state="readonly"
        )
        self.edit_target.pack(pady=5)

        self.edit_target.bind("<<ComboboxSelected>>", self.change_editor)

        # 編集用ウィジェットを配置する親フレーム
        editor_frame = tk.Frame(self.edit_window)
        editor_frame.pack(pady=5, fill="x", expand=True)

        # type
        type_label = ttk.Label(editor_frame, text="変更後の動物の種類")
        self.type_combo = ttk.Combobox(
            editor_frame,
            values=self.manager.get_available_animal_types(),
            state="readonly"
        )
        # name
        name_label = ttk.Label(editor_frame, text="変更後の動物の名前")
        self.name_entry = tk.Entry(editor_frame)
        # ability
        ability_label = ttk.Label(editor_frame, text="追加する特技")
        self.ability_combo = ttk.Combobox(
            editor_frame,
            values=self.manager.get_available_abilities(),
            state="readonly"
        )

        # ウィジェットを辞書で管理
        self.edit_widgets = {
            "種類の変更": (type_label, self.type_combo),
            "名前の変更": (name_label, self.name_entry),
            "特技の変更": (ability_label, self.ability_combo)
        }

        # 決定・キャンセルボタン (下部に固定配置)
        self.create_ok_cancel_btn(self.edit_window, lambda: self.ctrl.execute_edit())


    def change_editor(self, event):
        # すべての編集用ウィジェットを一旦非表示にする
        for widgets in self.edit_widgets.values():
            for widget in widgets:
                widget.pack_forget()
        # choiceされた要素のウィジェットを表示する
        choice = self.edit_target.get()
        if choice in self.edit_widgets:
            label, field = self.edit_widgets[choice]
            label.pack(pady=1)
            field.pack(pady=5)

    def open_act_dialog(self):
        self.act_window = self.create_dialog("動物を行動させる")
        ttk.Label(self.act_window,text="行動の種類").pack(pady=1)
        self.act_target = ttk.Combobox(
            self.act_window,
            values=["voice", "fly", "swim"],
            state="readonly"
        )
        self.act_target.pack(pady=5)
        self.create_ok_cancel_btn(self.act_window, lambda: self.ctrl.execute_act(self.act_target.get()))
    
    def create_dialog(self, title, width=240, height=160):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(f"{width}x{height}")
        return window

    def create_ok_cancel_btn(self, parent, ok_cmd):
        btn_frame = tk.Frame(parent)
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        tk.Button(btn_frame, text="決定",
                  command=ok_cmd,
                  width=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="キャンセル",
                  command=parent.destroy,
                  width=8).pack(side=tk.LEFT, padx=5)

        
    def refresh_list(self, animals=None):
        for item in self.tree_animals.get_children():
            self.tree_animals.delete(item)

        if animals is None:
            # 明示的にID順で取得
            animals = sorted(self.manager.get_all_animals(), key=lambda x: x.id)

        for animal in animals:
            self.tree_animals.insert("", "end", values=(animal.id, animal.type_jp, animal.name))
