import tkinter as tk
from ui.nasabah_ui import NasabahWindow
from ui.kriteria_ui import KriteriaWindow
from ui.perhitungan_ui import PerhitunganWindow
from ui.report_ui import ReportWindow

class DashboardWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard SPK Kelayakan Kredit")
        self.root.geometry("800x500")  # ukuran sedang
        self.center_window(800, 500)   # ditengah layar

        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Selamat Datang di SPK Kelayakan Kredit", font=("Arial", 16, "bold")).pack(pady=20)

        tk.Button(frame, text="Kelola Data Nasabah", width=30, command=self.open_nasabah).pack(pady=5)
        tk.Button(frame, text="Kelola Kriteria", width=30, command=self.open_kriteria).pack(pady=5)
        tk.Button(frame, text="Perhitungan AHP & SAW", width=30, command=self.open_perhitungan).pack(pady=5)
        tk.Button(frame, text="Laporan", width=30, command=self.open_report).pack(pady=5)
        tk.Button(frame, text="Keluar", width=30, command=self.root.quit).pack(pady=20)

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def open_nasabah(self):
        NasabahWindow(self.root)

    def open_kriteria(self):
        new_root = tk.Toplevel(self.root)
        KriteriaWindow(new_root)

    def open_perhitungan(self):
        new_root = tk.Toplevel(self.root)
        PerhitunganWindow(new_root)

    def open_report(self):
        ReportWindow(self.root)
