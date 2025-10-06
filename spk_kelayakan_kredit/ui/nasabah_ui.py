# ui/nasabah_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from models import database

class NasabahFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        # form
        form = tk.Frame(self)
        form.pack(padx=12, pady=8, anchor="nw")

        tk.Label(form, text="Nama").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.entry_nama = tk.Entry(form, width=30)
        self.entry_nama.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(form, text="Usia (Kategori)").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.combo_usia = ttk.Combobox(form, values=[
            "1 - <25 tahun", "2 - 25-35 tahun", "3 - 36-50 tahun", "4 - >50 tahun"
        ], width=28, state="readonly")
        self.combo_usia.grid(row=1, column=1, padx=6, pady=6)

        tk.Label(form, text="Pendapatan (Kategori)").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        self.combo_pendapatan = ttk.Combobox(form, values=[
            "1 - <2 juta", "2 - 2-5 juta", "3 - 5-10 juta", "4 - >10 juta"
        ], width=28, state="readonly")
        self.combo_pendapatan.grid(row=2, column=1, padx=6, pady=6)

        tk.Label(form, text="Pekerjaan").grid(row=3, column=0, padx=6, pady=6, sticky="e")
        self.combo_pekerjaan = ttk.Combobox(form, values=[
            "1 - PNS/Karyawan Tetap", "2 - Wiraswasta", "3 - Buruh/Karyawan Kontrak", "4 - Lainnya"
        ], width=28, state="readonly")
        self.combo_pekerjaan.grid(row=3, column=1, padx=6, pady=6)

        tk.Label(form, text="Jaminan").grid(row=4, column=0, padx=6, pady=6, sticky="e")
        self.combo_jaminan = ttk.Combobox(form, values=[
            "1 - Sertifikat Rumah/Tanah", "2 - BPKB Kendaraan", "3 - Tanpa Jaminan"
        ], width=28, state="readonly")
        self.combo_jaminan.grid(row=4, column=1, padx=6, pady=6)

        btn_frame = tk.Frame(form)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Simpan", command=self.simpan_nasabah, bg="#2ecc71", fg="white").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Reset", command=self.reset_form, bg="#e67e22", fg="white").pack(side="left", padx=6)

        # tabel
        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=8)

        cols = ("ID", "Nama", "Usia", "Pendapatan", "Pekerjaan", "Jaminan")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True)

    def simpan_nasabah(self):
        nama = self.entry_nama.get().strip()
        usia = self.combo_usia.get().split(" - ")[0] if self.combo_usia.get() else None
        pendapatan = self.combo_pendapatan.get().split(" - ")[0] if self.combo_pendapatan.get() else None
        pekerjaan = self.combo_pekerjaan.get().split(" - ")[0] if self.combo_pekerjaan.get() else None
        jaminan = self.combo_jaminan.get().split(" - ")[0] if self.combo_jaminan.get() else None

        if not all([nama, usia, pendapatan, pekerjaan, jaminan]):
            messagebox.showerror("Error", "Semua field harus diisi!")
            return

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO nasabah (nama, usia, pendapatan, pekerjaan, jaminan) VALUES (?, ?, ?, ?, ?)",
            (nama, int(usia), int(pendapatan), int(pekerjaan), int(jaminan))
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Sukses", "Data nasabah berhasil ditambahkan.")
        # clear form
        self.reset_form()
        self.load_data()

    def reset_form(self):
        self.entry_nama.delete(0, tk.END)
        self.combo_usia.set("")
        self.combo_pendapatan.set("")
        self.combo_pekerjaan.set("")
        self.combo_jaminan.set("")

    def load_data(self):
        # clear existing rows
        for r in self.tree.get_children():
            self.tree.delete(r)

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nama, usia, pendapatan, pekerjaan, jaminan FROM nasabah")
        rows = cur.fetchall()
        conn.close()

        usia_map = {1: "<25 tahun", 2: "25-35 tahun", 3: "36-50 tahun", 4: ">50 tahun"}
        pend_map = {1: "<2 juta", 2: "2-5 juta", 3: "5-10 juta", 4: ">10 juta"}
        kerja_map = {1: "PNS/Karyawan Tetap", 2: "Wiraswasta", 3: "Buruh/Karyawan Kontrak", 4: "Lainnya"}
        jam_map = {1: "Sertifikat Rumah/Tanah", 2: "BPKB Kendaraan", 3: "Tanpa Jaminan"}

        for row in rows:
            id_, nama, usia, pend, kerja, jam = row
            self.tree.insert("", "end", values=(
                id_, nama,
                usia_map.get(usia, usia),
                pend_map.get(pend, pend),
                kerja_map.get(kerja, kerja),
                jam_map.get(jam, jam)
            ))
