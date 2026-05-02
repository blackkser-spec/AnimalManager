import tkinter as tk
from tkinter import ttk
from gui.layout import Layout
from text.loader import get_text, set_language

text = get_text()

def select_mode():
    """起動モード（ローカル/リモート）を選択するウィンドウを表示"""
    mode_window = tk.Tk()
    mode_window.title(text["label"]["run_option"])
    mode_window.geometry("300x150")

    mode = {"use_mode": None}
    language = {"language": None}

    def set_mode(use_mode):
        mode["use_mode"] = use_mode
        mode_window.destroy()

    languages = text["languages"].values()
    tk.Label(mode_window, text=text["prompts"]["select_language"], pady=10).pack()
    language_combo = ttk.Combobox(mode_window, values=languages, state="readonly")
    language_combo.pack(pady=5)
    language_combo.current(0)
    language_combo.bind("<<ComboboxSelected>>",)


    tk.Label(mode_window, text=text["prompts"]["select_run_mode"], pady=10).pack()

    tk.Button(mode_window, text=text["label"]["local"], 
              command=lambda: set_mode("local"), width=15).pack(side=tk.LEFT, padx=20)
    tk.Button(mode_window, text=text["label"]["remote"], 
              command=lambda: set_mode("remote"), width=15).pack(side=tk.RIGHT, padx=20)
    
    
    mode_window.mainloop()
    return mode["use_mode"]

if __name__ == "__main__":
    api_mode = select_mode()
    root = tk.Tk()
    app = Layout(root, use_mode=api_mode)
    root.mainloop()