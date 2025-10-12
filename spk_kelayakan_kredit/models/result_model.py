# from models.database import get_connection

# def simpan_hasil(nasabah_id, nama, skor, status):
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute('''
#         INSERT INTO results (nasabah_id, nama, skor, status)
#         VALUES (?, ?, ?, ?)
#     ''', (nasabah_id, nama, skor, status))
#     conn.commit()
#     conn.close()

# def ambil_semua_hasil():
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute("SELECT id, nasabah_id, nama, skor, status, created_at FROM results ORDER BY created_at DESC")
#     rows = cur.fetchall()
#     conn.close()
#     return rows
