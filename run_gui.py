import tkinter as tk
from tkinter import messagebox
from GUI.layout import Layout

def select_mode():
    mode_window = tk.Tk()
    mode_window.title("起動モード選択")
    mode_window.geometry("300x150")

    mode = {"use_mode": None}

    def set_mode(use_mode):
        mode["use_mode"] = use_mode
        mode_window.destroy()

    tk.Label(mode_window, text="実行モードを選択してください", pady=20).pack()
    tk.Button(mode_window, text="ローカルモード", command=lambda: set_mode("local"), width=15).pack(side=tk.LEFT, padx=20)
    tk.Button(mode_window, text="APIモード", command=lambda: set_mode("remote"), width=15).pack(side=tk.RIGHT, padx=20)
    
    mode_window.mainloop()
    return mode["use_mode"]

if __name__ == "__main__":
    api_mode = select_mode()
    root = tk.Tk()
    app = Layout(root, use_mode=api_mode)
    root.mainloop()