# ui/perhitungan_ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import numpy as np
import csv
from models import database
from models import kriteria_model
from methods import ahp as ahp_method

RI_TABLE = {1:0.0,2:0.0,3:0.58,4:0.90,5:1.12,6:1.24,7:1.32,8:1.41,9:1.45,10:1.49}

class PerhitunganFrame(tk.Frame):
    """
    PerhitunganFrame:
    - Menampilkan bobot kriteria (AHP) yang diambil langsung dari tabel kriteria.
    - Menjalankan SAW memakai bobot tersebut.
    - Menampilkan hasil SAW dalam window baru (tabel) dan bisa export CSV.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._saw_result = None
        self.build_ui()
        self.load_bobot_from_db()

    # ---------------- UI ----------------
    def build_ui(self):
        header = ttk.Label(self, text="Perhitungan AHP & SAW", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)

        # Frame AHP (read-only - bobot dari DB)
        frm_ahp = ttk.LabelFrame(self, text="AHP (Bobot kriteria dari DB)")
        frm_ahp.pack(fill="x", padx=12, pady=8)

        self.txt_bobot = tk.Text(frm_ahp, height=5, width=80)
        self.txt_bobot.pack(padx=8, pady=6)

        btn_frame_ahp = tk.Frame(frm_ahp)
        btn_frame_ahp.pack(fill="x", padx=8, pady=6)
        ttk.Button(btn_frame_ahp, text="Refresh Bobot", command=self.load_bobot_from_db).pack(side="left", padx=6)
        ttk.Button(btn_frame_ahp, text="Tampilkan CR (AHP)", command=self.show_cr).pack(side="left", padx=6)
        ttk.Button(btn_frame_ahp, text="Perbandingan Pasangan (AHP)", command=self.open_pairwise_dialog).pack(side="left", padx=6)
        ttk.Button(btn_frame_ahp, text="Tampilkan Matriks Pairwise", command=self.show_pairwise_matrix).pack(side="left", padx=6)

        # Frame SAW
        frm_saw = ttk.LabelFrame(self, text="SAW (Hitung ranking nasabah)")
        frm_saw.pack(fill="both", expand=True, padx=12, pady=8)

        lbl = ttk.Label(frm_saw, text="Klik 'Hitung SAW' untuk menjalankan metode Simple Additive Weighting menggunakan bobot kriteria saat ini.")
        lbl.pack(anchor="w", padx=8, pady=(6,0))

        btns = tk.Frame(frm_saw)
        btns.pack(anchor="w", padx=8, pady=8)
        ttk.Button(btns, text="Hitung SAW", command=self.hitung_saw).pack(side="left", padx=6)
        ttk.Button(btns, text="Hitung AHP (Full)", command=self.hitung_ahp_full).pack(side="left", padx=6)
        ttk.Button(btns, text="Tampilkan Hasil (jika tersedia)", command=self.show_results_window).pack(side="left", padx=6)

        self.txt_saw = tk.Text(frm_saw, height=6)
        self.txt_saw.pack(fill="both", padx=8, pady=6, expand=False)

    # ---------------- Helpers: AHP bobot ----------------
    def load_bobot_from_db(self):
        """
        Ambil kriteria dari tabel kriteria (ORDER BY id).
        Tampilkan nama + bobot di text area.
        Simpan internally untuk perhitungan SAW.
        """
        try:
            conn = database.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, nama, bobot FROM kriteria ORDER BY id")
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"Gagal membaca kriteria: {e}")
            return

        if not rows:
            self.criteria = []
            self.weights = np.array([])
            self.txt_bobot.delete("1.0", tk.END)
            self.txt_bobot.insert(tk.END, "Belum ada kriteria di database.")
            return

        # rows may be sqlite Row or tuples
        criteria = []
        weights = []
        for r in rows:
            # r could be (id,nama,bobot) or sqlite.Row
            nama = r[1]
            bobot = r[2]
            try:
                bw = float(bobot)
            except:
                bw = 0.0
            criteria.append(str(nama))
            weights.append(bw)

        weights = np.array(weights, dtype=float)
        # normalisasi bobot agar jumlah = 1 (jika belum)
        if not np.isclose(weights.sum(), 1.0):
            if weights.sum() == 0:
                # avoid division by zero: fallback equal weights
                weights = np.ones_like(weights) / len(weights)
            else:
                weights = weights / weights.sum()

        self.criteria = criteria
        self.weights = weights

        # show in text area
        self.txt_bobot.delete("1.0", tk.END)
        for name, w in zip(self.criteria, self.weights):
            self.txt_bobot.insert(tk.END, f"{name}: {w:.6f}\n")

    def show_cr(self):
        """
        Hitung CR (consistency ratio) dari bobot yang ada dengan merekonstruksi matriks pairwise
        a_ij = w_i / w_j (metode rekonstruksi). CR akan menjadi 0 jika w konsisten.
        Ini hanya memberikan info tambahan.
        """
        if not hasattr(self, "weights") or len(self.weights) == 0:
            messagebox.showinfo("Info", "Tidak ada bobot kriteria untuk dihitung.")
            return

        # If user has provided a pairwise matrix via dialog, prefer that
        if hasattr(self, 'criteria_pairwise'):
            pair = np.array(self.criteria_pairwise, dtype=float)
            n = pair.shape[0]
        else:
            w = self.weights
            n = w.size
            # reconstruct pairwise
            pair = np.zeros((n,n), dtype=float)
            for i in range(n):
                for j in range(n):
                    pair[i,j] = w[i] / w[j] if w[j] != 0 else 0.0

        # eigen
        eigvals = np.linalg.eigvals(pair)
        lambda_max = float(np.max(eigvals.real))
        CI = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        RI = RI_TABLE.get(n, 1.49)
        CR = CI / RI if RI != 0 else 0.0

        messagebox.showinfo("CR (info)", f"λ_max = {lambda_max:.6f}\nCI = {CI:.6f}\nCR = {CR:.6f}")

    # ---------------- AHP Pairwise UI ----------------
    def open_pairwise_dialog(self):
        """
        Buka dialog untuk input perbandingan pasangan (Saaty scale) antar kriteria.
        Pre-fill pendapatan vs jaminan = 1 dan disable agar selalu sama penting.
        Setelah submit, hitung bobot menggunakan eigenvector utama dan tampilkan CR.
        """
        if not hasattr(self, "criteria") or len(self.criteria) == 0:
            messagebox.showerror("Error", "Tidak ada kriteria di database.")
            return

        criteria = self.criteria
        n = len(criteria)

        dlg = tk.Toplevel(self)
        dlg.title("Perbandingan Pasangan - AHP")
        dlg.geometry("600x400")

        info = ttk.Label(dlg, text="Pilh nilai perbandingan menurut skala Saaty (1/9 ... 1 ... 9).\nNilai yang dipilih berlaku untuk kriteria i terhadap j (i vs j). Nilai kebalikan akan diisi otomatis.")
        info.pack(fill="x", padx=8, pady=6)

        frame = tk.Frame(dlg)
        frame.pack(fill="both", expand=True, padx=8, pady=6)

        # Saaty scale display -> float mapping
        saaty_opts = ["1/9","1/8","1/7","1/6","1/5","1/4","1/3","1/2","1","2","3","4","5","6","7","8","9"]
        saaty_map = {s: float(eval(s.replace('/','/'))) for s in saaty_opts}  # safe mapping using eval on simple strings

        # store comboboxes for pairs
        pair_vars = {}

        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = 0
        for i in range(n):
            for j in range(i+1, n):
                lbl = ttk.Label(inner, text=f"{criteria[i]}  vs  {criteria[j]}")
                lbl.grid(row=row, column=0, sticky="w", padx=6, pady=4)
                var = tk.StringVar(value="1")
                cmb = ttk.Combobox(inner, values=saaty_opts, textvariable=var, state="readonly", width=8)
                cmb.grid(row=row, column=1, padx=6, pady=4)
                pair_vars[(i,j)] = (var, cmb)
                row += 1

        # pre-fill pendapatan == jaminan to 1 if both criteria exist (but keep editable)
        # find indices
        idx_pend = None
        idx_jam = None
        # Optionally lock pendapatan == jaminan pair
        # find indices
        idx_pend = None
        idx_jam = None
        for idx, name in enumerate(criteria):
            nlow = name.lower()
            if "pendapatan" in nlow or "gaji" in nlow or "income" in nlow:
                idx_pend = idx
            if "jaminan" in nlow or "agunan" in nlow or "collateral" in nlow:
                idx_jam = idx

        # store optional lock widgets so we can toggle state
        pair_lock_vars = {}
        if idx_pend is not None and idx_jam is not None:
            key = (min(idx_pend, idx_jam), max(idx_pend, idx_jam))
            if key in pair_vars:
                var, cmb = pair_vars[key]
                var.set("1")
                # create a checkbox to allow user to lock/unlock this pair
                # default unlocked (user can edit); checkbox lets user lock it
                lock_var = tk.BooleanVar(value=False)
                def make_toggle(cmb_ref, lv):
                    def toggle():
                        state = "disabled" if lv.get() else "readonly"
                        cmb_ref.configure(state=state)
                    return toggle
                # find grid row for this pair to place checkbox next to combobox
                info_row = None
                # search children in inner frame: locate widget with same variable
                for child in inner.grid_slaves():
                    try:
                        # combobox has cget
                        if isinstance(child, ttk.Combobox) and child.cget('textvariable'):
                            if str(child.cget('textvariable')) == str(var):
                                info_row = int(child.grid_info().get('row', 0))
                                break
                    except Exception:
                        pass
                # place checkbox; if we couldn't find row, append at end
                if info_row is None:
                    info_row = row
                chk = ttk.Checkbutton(inner, text="Kunci pasangan", variable=lock_var, command=make_toggle(cmb, lock_var))
                chk.grid(row=info_row, column=2, padx=6, pady=4)
                # ensure combobox initial state: keep readonly (editable) unless locked
                if lock_var.get():
                    cmb.configure(state="disabled")
                pair_lock_vars[key] = (lock_var, chk)

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(fill="x", padx=8, pady=8)
        def submit_pairs():
            # build matrix
            mat = np.ones((n,n), dtype=float)
            try:
                for (i,j), (var, cmb) in pair_vars.items():
                    s = var.get()
                    if s == "":
                        raise ValueError(f"Nilai untuk {criteria[i]} vs {criteria[j]} belum dipilih")
                    val = saaty_map[s]
                    mat[i,j] = val
                    mat[j,i] = 1.0/val if val != 0 else 0.0

                # compute ahp
                weights, CI, CR = ahp_method.ahp_from_pairwise(mat)
                # store
                self.criteria_pairwise = mat
                try:
                    kriteria_model.save_pairwise_matrix('default', mat.tolist() if hasattr(mat, 'tolist') else mat)
                except Exception:
                    # non-fatal: ignore DB save errors but warn user
                    messagebox.showwarning('Warning', 'Gagal menyimpan matriks pairwise ke database (non-fatal).')
                self.weights = np.array(weights, dtype=float)

                # update text area
                self.txt_bobot.delete("1.0", tk.END)
                for name, w in zip(self.criteria, self.weights):
                    self.txt_bobot.insert(tk.END, f"{name}: {w:.6f}\n")

                dlg.destroy()

                msg = f"AHP selesai. λ_max info di bawah:\nCI = {CI:.6f}\nCR = {CR:.6f}"
                if CR > 0.1:
                    msg += "\nCR > 0.1 (tidak konsisten). Pertimbangkan mengoreksi input perbandingan."
                messagebox.showinfo("Hasil AHP", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal memproses perbandingan: {e}")

        ttk.Button(btn_frame, text="Submit & Hitung Bobot", command=submit_pairs).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Batal", command=dlg.destroy).pack(side="right", padx=6)

    def show_pairwise_matrix(self):
        """Tampilkan matriks pairwise kriteria — ambil dari DB jika tersedia, atau dari memory."""
        if not hasattr(self, 'criteria') or len(self.criteria) == 0:
            messagebox.showinfo("Info", "Tidak ada kriteria.")
            return

        # try load from DB by a fixed name (we use 'default' key)
        saved = kriteria_model.load_pairwise_matrix('default')
        if saved is not None:
            mat = saved
        elif hasattr(self, 'criteria_pairwise'):
            mat = self.criteria_pairwise.tolist() if hasattr(self.criteria_pairwise, 'tolist') else self.criteria_pairwise
        else:
            messagebox.showinfo("Info", "Belum ada matriks pairwise yang disimpan atau di-submit.")
            return

        # show in a simple Toplevel with Treeview
        win = tk.Toplevel(self)
        win.title("Matriks Pairwise")
        # columns
        cols = [f"C{i+1}" for i in range(len(mat))]
        tree = ttk.Treeview(win, columns=cols, show='headings')
        for i, c in enumerate(cols):
            tree.heading(c, text=self.criteria[i] if i < len(self.criteria) else c)
            tree.column(c, width=120)
        for i, row in enumerate(mat):
            vals = [f"{float(x):.6f}" for x in row]
            tree.insert("", "end", values=vals)
        tree.pack(fill="both", expand=True, padx=6, pady=6)

    # ---------------- SAW computation ----------------
    def _map_criteria_to_columns(self, criteria_list):
        """
        Map nama kriteria (string) ke column name di tabel nasabah.
        Returns list of column names (strings), in same order as criteria_list.
        If a mapping cannot be found for some criteria, raise ValueError.
        Known mappings:
          - contains 'usia' -> 'usia'
          - contains 'pendapatan' or 'gaji' -> 'pendapatan'
          - contains 'pekerjaan' or 'job' -> 'pekerjaan'
          - contains 'jaminan' or 'agunan' -> 'jaminan'
        Otherwise try exact match to nasabah table columns.
        """
        # get existing columns from nasabah table
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(nasabah)")
        cols_info = cur.fetchall()
        conn.close()
        existing_cols = [c[1] for c in cols_info]  # name is at index 1

        mapped = []
        for crit in criteria_list:
            cn = crit.lower()
            if "usia" in cn:
                col = "usia"
            elif "pendapatan" in cn or "gaji" in cn or "income" in cn:
                col = "pendapatan"
            elif "pekerjaan" in cn or "job" in cn:
                col = "pekerjaan"
            elif "jaminan" in cn or "agunan" in cn or "collateral" in cn:
                col = "jaminan"
            else:
                # try exact match or safer variant
                cand = crit.strip().lower()
                if cand in existing_cols:
                    col = cand
                elif crit in existing_cols:
                    col = crit
                else:
                    # not found
                    raise ValueError(f"Kriteria '{crit}' tidak dapat dimapping ke kolom tabel nasabah.")
            if col not in existing_cols:
                raise ValueError(f"Kolom '{col}' (mapping dari kriteria '{crit}') tidak ditemukan di tabel nasabah.")
            mapped.append(col)
        return mapped

    def hitung_saw(self):
        """
        Core SAW computation:
         - ambil kriteria & bobot dari DB (done earlier)
         - map kriteria -> kolom nasabah
         - ambil data nasabah (id,nama,columns...)
         - normalisasi (benefit/cost)
         - skor = norm.dot(weights)
         - simpan hasil ke self._saw_result dan tampilkan ringkasan di text area
        """
        try:
            if not hasattr(self, "criteria") or len(self.criteria) == 0:
                messagebox.showerror("Error", "Tidak ada kriteria di database. Tambahkan kriteria terlebih dahulu.")
                return

            # map criteria names to nasabah columns
            cols = self._map_criteria_to_columns(self.criteria)  # may raise ValueError

            # load nasabah data (id, nama, col1, col2, ...)
            conn = database.get_connection()
            cur = conn.cursor()
            select_cols = ", ".join([f'"{c}"' for c in cols])
            sql = f"SELECT id, nama, {select_cols} FROM nasabah"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()

            if not rows:
                messagebox.showinfo("Info", "Data nasabah kosong.")
                return

            # build matrix and names
            names = []
            ids = []
            matrix = []
            for r in rows:
                ids.append(r[0])
                names.append(r[1])
                vals = []
                for i, c in enumerate(cols):
                    raw = r[2 + i]
                    try:
                        vals.append(float(raw))
                    except:
                        raise ValueError(f"Nilai untuk kolom '{c}' pada nasabah '{r[1]}' bukan angka: {raw}")
                matrix.append(vals)
            matrix = np.array(matrix, dtype=float)  # shape (n_alt, n_crit)

            # prepare weights (align with criteria order)
            weights = self.weights.copy()
            if weights.size != matrix.shape[1]:
                # mismatch: provide clear message
                raise ValueError(f"Jumlah bobot ({weights.size}) tidak cocok dengan jumlah kriteria yang dipetakan ({matrix.shape[1]}). Periksa tabel kriteria.")
            # ensure normalized
            if not np.isclose(weights.sum(), 1.0):
                weights = weights / weights.sum()

            # decide benefit flags: usia -> cost, others -> benefit
            benefit_flags = []
            for c in cols:
                if "usia" in c.lower():
                    benefit_flags.append(False)
                else:
                    benefit_flags.append(True)

            # normalization SAW
            n_alt, n_crit = matrix.shape
            norm = np.zeros_like(matrix, dtype=float)

            for j in range(n_crit):
                col = matrix[:, j]
                if benefit_flags[j]:
                    maxv = np.max(col)
                    if maxv == 0:
                        norm[:, j] = 0.0
                    else:
                        norm[:, j] = col / maxv
                else:
                    # cost
                    minv = np.min(col)
                    # avoid division by zero
                    safe_col = np.where(col == 0, 1e-9, col)
                    norm[:, j] = minv / safe_col

            # compute scores
            scores = norm.dot(weights)

            # prepare result rows sorted by score desc
            results = []
            for idx in range(n_alt):
                results.append({
                    "id": ids[idx],
                    "nama": names[idx],
                    "score": float(scores[idx]),
                    "raw_values": matrix[idx,:].tolist(),
                    "r_values": norm[idx,:].tolist()
                })
            # sort
            results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
            # assign rank
            for i, row in enumerate(results_sorted, start=1):
                row["rank"] = i

            # store result for later display/export
            self._saw_result = {
                "criteria": self.criteria,
                "columns": cols,
                "weights": weights.tolist(),
                "results": results_sorted
            }

            # show brief output
            out_lines = []
            out_lines.append("SAW selesai. Contoh 10 teratas:")
            for item in results_sorted[:10]:
                out_lines.append(f"#{item['rank']}  {item['nama']}  -> {item['score']:.6f}")
            self.txt_saw.delete("1.0", tk.END)
            self.txt_saw.insert(tk.END, "\n".join(out_lines))
            messagebox.showinfo("Sukses", "Perhitungan SAW selesai. Klik 'Tampilkan Hasil' untuk tabel lengkap.")
        except Exception as e:
            messagebox.showerror("Error SAW", f"Gagal menghitung SAW:\n{e}")

    def hitung_ahp_full(self):
        """
        Hitung AHP full:
         - Ambil bobot kriteria (dari pairwise jika user input, atau dari DB)
         - Untuk tiap kriteria, bangun matriks pairwise antar alternatif menggunakan rasio nilai
         - Hitung bobot lokal alternatif per kriteria (eigenvector)
         - Agregasi global score = sum_k (w_k * local_priority_k)
         - Tampilkan CR untuk kriteria dan rata-rata CR alternatif
        """
        try:
            if not hasattr(self, "criteria") or len(self.criteria) == 0:
                messagebox.showerror("Error", "Tidak ada kriteria di database. Tambahkan kriteria terlebih dahulu.")
                return

            # criteria weights: prefer self.weights (from pairwise dialog) if available
            if hasattr(self, "criteria_pairwise"):
                # already computed by pairwise dialog
                crit_weights = np.array(self.weights, dtype=float)
                crit_pair = np.array(self.criteria_pairwise, dtype=float)
                # compute CR for criteria pairwise
                _, CI_crit, CR_crit = ahp_method.ahp_from_pairwise(crit_pair)
            else:
                # reconstruct from DB weights
                w = np.array(self.weights, dtype=float)
                crit_weights, CI_crit, CR_crit, crit_pair = ahp_method.ahp_from_weights(w)

            # map criteria to columns
            cols = self._map_criteria_to_columns(self.criteria)

            # load nasabah data
            conn = database.get_connection()
            cur = conn.cursor()
            select_cols = ", ".join([f'"{c}"' for c in cols])
            sql = f"SELECT id, nama, {select_cols} FROM nasabah"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()

            if not rows:
                messagebox.showinfo("Info", "Data nasabah kosong.")
                return

            ids = [r[0] for r in rows]
            names = [r[1] for r in rows]
            matrix = []
            for r in rows:
                vals = []
                for i, c in enumerate(cols):
                    raw = r[2 + i]
                    try:
                        vals.append(float(raw))
                    except:
                        raise ValueError(f"Nilai untuk kolom '{c}' pada nasabah '{r[1]}' bukan angka: {raw}")
                matrix.append(vals)
            M = np.array(matrix, dtype=float)  # shape (n_alt, n_crit)
            n_alt, n_crit = M.shape

            if crit_weights.size != n_crit:
                raise ValueError(f"Jumlah bobot kriteria ({crit_weights.size}) tidak cocok dengan jumlah kriteria ({n_crit}).")

            # benefit flags as before
            benefit_flags = []
            for c in cols:
                if "usia" in c.lower():
                    benefit_flags.append(False)
                else:
                    benefit_flags.append(True)

            # For each criterion, build pairwise matrix among alternatives using ratio
            local_priority_matrix = np.zeros((n_alt, n_crit), dtype=float)
            alt_crs = []
            for j in range(n_crit):
                col = M[:, j]
                # build pairwise
                pair_alt = np.ones((n_alt, n_alt), dtype=float)
                for i in range(n_alt):
                    for k in range(n_alt):
                        vi = col[i]
                        vk = col[k]
                        # avoid division by zero
                        if vi == 0 and vk == 0:
                            pair_alt[i,k] = 1.0
                        elif vk == 0:
                            pair_alt[i,k] = 1e9
                        else:
                            ratio = vi / vk
                            if benefit_flags[j]:
                                pair_alt[i,k] = ratio
                            else:
                                # cost: smaller better -> invert
                                pair_alt[i,k] = vk / vi if vi != 0 else 1e9

                # compute local priorities
                w_local, CI_local, CR_local = ahp_method.ahp_from_pairwise(pair_alt)
                local_priority_matrix[:, j] = w_local
                alt_crs.append(CR_local)

            # aggregate global scores
            crit_weights = np.array(crit_weights, dtype=float)
            if not np.isclose(crit_weights.sum(), 1.0):
                crit_weights = crit_weights / crit_weights.sum()

            global_scores = local_priority_matrix.dot(crit_weights)

            # prepare results similar to SAW structure
            results = []
            for idx in range(n_alt):
                results.append({
                    "id": ids[idx],
                    "nama": names[idx],
                    "score": float(global_scores[idx]),
                    "local_priorities": local_priority_matrix[idx,:].tolist(),
                    "raw_values": M[idx,:].tolist()
                })
            results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
            for i, row in enumerate(results_sorted, start=1):
                row["rank"] = i

            # store result
            self._saw_result = {
                "method": "ahp_full",
                "criteria": self.criteria,
                "columns": cols,
                "weights": crit_weights.tolist(),
                "results": results_sorted,
                "CR_criteria": float(CR_crit),
                "CR_alternatives_avg": float(np.mean(alt_crs))
            }

            # show brief output
            out_lines = []
            out_lines.append("AHP (Full) selesai. Contoh 10 teratas:")
            out_lines.append(f"CR Kriteria = {CR_crit:.6f}; Rata-rata CR Alternatif = {np.mean(alt_crs):.6f}")
            for item in results_sorted[:10]:
                out_lines.append(f"#{item['rank']}  {item['nama']}  -> {item['score']:.6f}")
            self.txt_saw.delete("1.0", tk.END)
            self.txt_saw.insert(tk.END, "\n".join(out_lines))
            messagebox.showinfo("Sukses", "Perhitungan AHP (Full) selesai. Klik 'Tampilkan Hasil' untuk tabel lengkap.")

        except Exception as e:
            messagebox.showerror("Error AHP Full", f"Gagal menghitung AHP Full:\n{e}")

    # ---------------- Results Window ----------------
    def show_results_window(self):
        if not self._saw_result:
            messagebox.showinfo("Info", "Belum ada hasil SAW. Klik 'Hitung SAW' terlebih dahulu.")
            return

        data = self._saw_result
        criteria = data["criteria"]
        cols = data["columns"]
        results = data["results"]

        win = tk.Toplevel(self)
        win.title("Hasil SAW - Ranking Nasabah")
        win.geometry("900x500")

        # top buttons
        top = tk.Frame(win)
        top.pack(fill="x", pady=6, padx=6)
        ttk.Button(top, text="Export CSV", command=lambda: self._export_csv(results, criteria, cols)).pack(side="left", padx=6)
        ttk.Button(top, text="Tutup", command=win.destroy).pack(side="right", padx=6)

        # treeview columns: Rank, ID, Nama, Score, then each criteria
        tree_cols = ["Rank", "ID", "Nama", "Score"] + criteria
        tree = ttk.Treeview(win, columns=tree_cols, show="headings")
        for c in tree_cols:
            tree.heading(c, text=c)
            # set width
            if c == "Nama":
                tree.column(c, width=220)
            elif c == "Score":
                tree.column(c, width=100, anchor="center")
            elif c == "Rank":
                tree.column(c, width=60, anchor="center")
            else:
                tree.column(c, width=120)
        tree.pack(fill="both", expand=True, padx=6, pady=6)

        # insert rows
        for item in results:
            row_vals = [item["rank"], item["id"], item["nama"], round(item["score"], 6)]
            # add readable labels for each criterion if mapping known
            for j, raw in enumerate(item["raw_values"]):
                colname = cols[j]
                # map some known columns to friendly labels
                if colname == "usia":
                    v = {1:"<25",2:"25-35",3:"36-50",4:">50"}.get(int(raw), str(raw))
                elif colname == "pendapatan":
                    v = {1:"<2jt",2:"2-5jt",3:"5-10jt",4:">10jt"}.get(int(raw), str(raw))
                elif colname == "pekerjaan":
                    v = {1:"PNS/Tetap",2:"Wiraswasta",3:"Buruh/Kontrak",4:"Lainnya"}.get(int(raw), str(raw))
                elif colname == "jaminan":
                    v = {1:"Sertifikat",2:"BPKB",3:"Tanpa Jaminan"}.get(int(raw), str(raw))
                else:
                    v = str(raw)
                row_vals.append(v)
            tree.insert("", "end", values=row_vals)

    def _export_csv(self, results, criteria, cols):
        if not results:
            messagebox.showinfo("Info", "Tidak ada data untuk diexport.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not file_path:
            return
        header = ["Rank","ID","Nama","Score"] + criteria
        try:
            with open(file_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for item in results:
                    row = [item["rank"], item["id"], item["nama"], f"{item['score']:.6f}"]
                    # write raw values (or mapped labels)
                    for j, raw in enumerate(item["raw_values"]):
                        colname = cols[j]
                        if colname == "usia":
                            v = {1:"<25",2:"25-35",3:"36-50",4:">50"}.get(int(raw), raw)
                        elif colname == "pendapatan":
                            v = {1:"<2jt",2:"2-5jt",3:"5-10jt",4:">10jt"}.get(int(raw), raw)
                        elif colname == "pekerjaan":
                            v = {1:"PNS/Tetap",2:"Wiraswasta",3:"Buruh/Kontrak",4:"Lainnya"}.get(int(raw), raw)
                        elif colname == "jaminan":
                            v = {1:"Sertifikat",2:"BPKB",3:"Tanpa Jaminan"}.get(int(raw), raw)
                        else:
                            v = raw
                        row.append(v)
                    writer.writerow(row)
            messagebox.showinfo("Sukses", f"Hasil berhasil diexport ke {file_path}")
        except Exception as e:
            messagebox.showerror("Error export", f"Gagal menyimpan CSV: {e}")
