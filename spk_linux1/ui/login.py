# ui/login.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from models import database


class LoginFrame(tk.Frame):
    def __init__(self, parent, on_login=None):
        super().__init__(parent)
        self.on_login = on_login

        # use tb styles on background match - keep bg for compatibility
        self.configure(bg="white")
        self.build_ui()

    def build_ui(self):
        frm = tb.Frame(self, padding=20)
        frm.place(relx=0.5, rely=0.45, anchor="center")

        tb.Label(frm, text="Masuk ke Aplikasi SPK", font=("Helvetica", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0,10))

        tb.Label(frm, text="Username:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.entry_user = tb.Entry(frm)
        self.entry_user.grid(row=1, column=1, padx=6, pady=6)

        tb.Label(frm, text="Password:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.entry_pass = tb.Entry(frm, show="*")
        self.entry_pass.grid(row=2, column=1, padx=6, pady=6)

        btn = tb.Button(frm, text="Login", command=self.try_login, bootstyle="primary")
        btn.grid(row=3, column=0, columnspan=2, pady=(10,0), ipadx=10)

    def try_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Isi username dan password.")
            return

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        row = cur.fetchone()
        conn.close()

        if row:
            messagebox.showinfo("Sukses", f"Login berhasil. Selamat, {username}!")
            if callable(self.on_login):
                self.on_login(username)
        else:
            messagebox.showerror("Gagal", "Username atau password salah.")
