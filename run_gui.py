import tkinter as tk
from tkinter import ttk
from gui.layout import Layout
from text.loader import get_text, set_language

def select_mode():
    """起動モード（ローカル/リモート）を選択するウィンドウを表示"""
    text = get_text()
    
    mode_window = tk.Tk()
    mode_window.title(text["label"]["run_option"])
    mode_window.geometry("350x220")
    mode_window.resizable(False, False)

    selection = {"mode": None, "lang": "jp"}

    lang_map = {v: k for k, v in text["languages"].items()}

    def on_confirm(use_mode):
        selected_lang_name = language_combo.get()
        selection["lang"] = lang_map.get(selected_lang_name, "jp")
        selection["mode"] = use_mode
        mode_window.destroy()

    # 言語選択セクション
    tk.Label(mode_window, text=text["prompts"]["select_language"], font=("", 10, "bold")).pack(pady=(20, 5))
    language_combo = ttk.Combobox(mode_window, values=list(text["languages"].values()), state="readonly", width=25)
    language_combo.pack(pady=10)
    language_combo.current(0)
    language_combo.bind("<<ComboboxSelected>>", lambda e: (e.widget.selection_clear(), mode_window.focus()))

    # 区切り線
    tk.Frame(mode_window, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=20, pady=10)

    # モード選択セクション
    tk.Label(mode_window, text=text["prompts"]["select_run_mode"],font=("", 10, "bold")).pack(pady=5)
    
    btn_frame = tk.Frame(mode_window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text=text["label"]["local"], command=lambda: on_confirm("local"), width=15).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text=text["label"]["remote"], command=lambda: on_confirm("remote"), width=15).pack(side=tk.LEFT, padx=10)
    
    mode_window.mainloop()
    return selection["mode"], selection["lang"]

if __name__ == "__main__":
    api_mode, lang = select_mode()
    if api_mode:
        root = tk.Tk()
        app = Layout(root, use_mode=api_mode, use_lang=lang)
        root.mainloop()