from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
import pymysql
from functools import wraps
from datetime import datetime, date, time, timedelta
from datetime import time as dtime
import os
from werkzeug.utils import secure_filename
from flask import send_file
import random
import string
import json
from pdf_cetak import cetak_semua_gaji_pdf, cetak_semua_absensi_pdf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit


app = Flask(__name__)
app.secret_key = "secretkey_salma"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


UPLOAD_FOLDER_IZIN = os.path.join(app.root_path, "uploads", "izin")
UPLOAD_FOLDER_FOTO = os.path.join(app.root_path, "static", "foto_profil")
UPLOAD_FOLDER_SP = os.path.join(app.root_path, "uploads", "sp")

os.makedirs(UPLOAD_FOLDER_SP, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_IZIN, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_FOTO, exist_ok=True)

ALLOWED_EXT = {'jpg', 'jpeg', 'png', 'webp'}



JAM_MASUK_BATAS   = dtime(8, 0)  
JAM_PULANG_LEMBUR = dtime(20, 0) 


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@app.route("/uploads/izin/<filename>")
def serve_foto_izin(filename):
    if "user_id" not in session:
        return redirect(url_for("index"))
    return send_from_directory(UPLOAD_FOLDER_IZIN, filename)


# ======================
# DATABASE CONFIG
# ======================
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "dbsalma_ta_absengaji"
}


def get_db_connection():
    return pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        cursorclass=pymysql.cursors.DictCursor
    )


# ======================
# GENERATE ID
# ======================
def generate_id_user_salma(role):
    conn = get_db_connection()
    cursor = conn.cursor()
    prefix = "AD" if role == "admin" else "KR"
    cursor.execute("""
        SELECT id_user_salma FROM users_salma
        WHERE id_user_salma LIKE %s
        ORDER BY id_user_salma DESC LIMIT 1
    """, (prefix + "%",))
    last = cursor.fetchone()
    cursor.close()
    conn.close()
    if not last:
        return f"{prefix}001"
    number = int(last["id_user_salma"][2:])
    return f"{prefix}{number+1:03d}"


# ======================
# HELPER: LIMIT IZIN
# ======================
def get_limit_izin(cursor, id_user):
    """Ambil limit izin berdasarkan jabatan karyawan."""
    cursor.execute("""
        SELECT j.limit_izin_salma, j.limit_sakit_salma, j.limit_cuti_salma
        FROM users_salma u
        JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.id_user_salma = %s
    """, (id_user,))
    row = cursor.fetchone()
    if not row:
        return {"izin": 2, "sakit": 3, "cuti": 12}
    return {
        "izin":  int(row["limit_izin_salma"]  or 2),
        "sakit": int(row["limit_sakit_salma"] or 3),
        "cuti":  int(row["limit_cuti_salma"]  or 12),
    }


def hitung_hari_terpakai(cursor, id_user, jenis, tgl_mulai_dt):
    """
    Hitung total hari izin berstatus pending/disetujui
    untuk jenis tertentu dalam bulan (izin/sakit) atau tahun (cuti).
    """
    if jenis == "cuti":
        tahun = tgl_mulai_dt.year
        cursor.execute("""
            SELECT tanggal_mulai_salma, tanggal_selesai_salma
            FROM izin_salma
            WHERE id_user_salma = %s
              AND jenis_izin_salma = %s
              AND status_izin_salma IN ('pending', 'disetujui')
              AND YEAR(tanggal_mulai_salma) = %s
        """, (id_user, jenis, tahun))
    else:
        bulan = tgl_mulai_dt.month
        tahun = tgl_mulai_dt.year
        cursor.execute("""
            SELECT tanggal_mulai_salma, tanggal_selesai_salma
            FROM izin_salma
            WHERE id_user_salma = %s
              AND jenis_izin_salma = %s
              AND status_izin_salma IN ('pending', 'disetujui')
              AND MONTH(tanggal_mulai_salma) = %s
              AND YEAR(tanggal_mulai_salma)  = %s
        """, (id_user, jenis, bulan, tahun))

    rows = cursor.fetchall()
    total = 0
    for r in rows:
        mulai   = r["tanggal_mulai_salma"]
        selesai = r["tanggal_selesai_salma"]
        if mulai and selesai:
            total += (selesai - mulai).days + 1
    return total

def generate_kode_tiket():
    """Generate kode tiket unik: TKT-YYYYMMDD-XXXX"""
    tanggal = datetime.now().strftime("%Y%m%d")
    acak    = ''.join(random.choices(string.digits, k=4))
    return f"TKT-{tanggal}-{acak}"

def cek_dan_buat_sp(cursor, conn, id_user):
    cursor.execute("""
        SELECT COUNT(*) as n FROM absensi_salma
        WHERE id_user_salma = %s
          AND status_absensi_salma = 'alpha'
          AND YEAR(tanggal_absensi_salma) = YEAR(NOW())
    """, (id_user,))
    total_alpha = cursor.fetchone()["n"]

    if total_alpha >= 9:
        level = 3
    elif total_alpha >= 6:
        level = 2
    elif total_alpha >= 3:
        level = 1
    else:
        return

    cursor.execute("""
        SELECT id_sp FROM surat_peringatan_salma
        WHERE id_user_salma = %s AND level_sp = %s
    """, (id_user, level))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO surat_peringatan_salma
                (id_user_salma, level_sp, total_alpha, status_sp)
            VALUES (%s, %s, %s, 'menunggu_admin')
        """, (id_user, level, total_alpha))
        conn.commit()

def hitung_status_jam(jam_masuk, jam_pulang):
    """
    Terima jam_masuk dan jam_pulang (bisa datetime.time ATAU
    datetime.timedelta dari pymysql), kembalikan dict status telat/lembur.
    """
    result = dict(
        telat=False, menit_telat=0, label_telat="",
        lembur=False, menit_lembur=0, label_lembur=""
    )
 
    def ke_time(val):
        """Konversi timedelta → time agar bisa dibandingkan."""
        if val is None:
            return None
        if hasattr(val, 'seconds'):          # timedelta dari pymysql
            total_detik = int(val.seconds)
            return dtime(total_detik // 3600, (total_detik % 3600) // 60)
        return val                           # sudah datetime.time
 
    jm = ke_time(jam_masuk)
    jp = ke_time(jam_pulang)
 
    # ── CEK TELAT ────────────────────────────────────────────
    if jm:
        batas_m  = JAM_MASUK_BATAS.hour * 60 + JAM_MASUK_BATAS.minute
        masuk_m  = jm.hour * 60 + jm.minute
        if masuk_m > batas_m:
            selisih = masuk_m - batas_m
            result["telat"]       = True
            result["menit_telat"] = selisih
            j, m = divmod(selisih, 60)
            result["label_telat"] = f"{j}j {m}m" if j else f"{m}m"
 
    # ── CEK LEMBUR ───────────────────────────────────────────
    if jp:
        lembur_m  = JAM_PULANG_LEMBUR.hour * 60 + JAM_PULANG_LEMBUR.minute
        pulang_m  = jp.hour * 60 + jp.minute
        if pulang_m > lembur_m:
            selisih = pulang_m - lembur_m
            result["lembur"]       = True
            result["menit_lembur"] = selisih
            j, m = divmod(selisih, 60)
            result["label_lembur"] = f"{j}j {m}m" if j else f"{m}m"
 
    return result
 
def hitung_nilai_template(tipe, nilai, gaji_pokok, gaji_per_hari, menit_terlambat=0):
    if tipe == "nominal":
        return float(nilai)
    elif tipe == "persen_gaji_harian":
        return float(gaji_per_hari) * float(nilai) / 100
    elif tipe == "persen_gaji_bulanan":
        return float(gaji_pokok) * float(nilai) / 100
    elif tipe == "per_jam_terlambat":
        jam_terlambat = menit_terlambat / 60
        return float(nilai) * jam_terlambat
    return 0.0



# ======================
# LOGIN PAGE
# ======================
@app.route("/")
def index():
    return render_template("Salma_RFID_PreLogin.html")

@app.route("/login_user")
def login_user():
    return render_template("Salma_Login.html")

@app.route("/rfid/cari")
def rfid_cari():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"status": "error", "pesan": "Masukkan ID kartu atau ID user"})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cari berdasarkan ID kartu atau ID user
    cursor.execute("""
        SELECT u.username_salma, u.nama_salma, u.id_user_salma
        FROM users_salma u
        WHERE (u.id_user_salma = %s OR EXISTS (
            SELECT 1 FROM rfid_kartu_salma k 
            WHERE k.id_user_salma = u.id_user_salma AND k.id_kartu = %s
        ))
        AND u.role_salma = 'karyawan' 
        AND u.status_user_salma = 'aktif'
    """, (q, q))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        return jsonify({
            "status": "ok", 
            "username": user["username_salma"], 
            "nama": user["nama_salma"],
            "id_user": user["id_user_salma"]
        })
    else:
        return jsonify({"status": "error", "pesan": "Kartu/ID user tidak ditemukan atau akun nonaktif"})
        
# ======================
# LOGIN
# ======================
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT * FROM users_salma
        WHERE username_salma=%s AND status_user_salma='aktif'
    """, (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return render_template("Salma_Login.html", error="Username tidak ditemukan atau akun tidak aktif.")

    if user["password_salma"] != password:
        return render_template("Salma_Login.html", error="Password salah.")

    # 🔥 SESSION
    session["user_id"] = user["id_user_salma"]
    session["role"] = user["role_salma"]

    if user["role_salma"] == "admin":
        return redirect(url_for("admin_dashboard"))

    elif user["role_salma"] == "karyawan":
        return redirect(url_for("karyawan_dashboard"))

    return "Role tidak dikenali"


# ======================
# PROTECT ADMIN
# ======================
def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "role" not in session or session["role"] != "admin":
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrap


# ======================
# DASHBOARD ADMIN
# ======================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    keyword        = request.args.get("keyword", "").strip()
    filter_jabatan = request.args.get("jabatan", "").strip()

    cursor.execute("SELECT COUNT(*) as total FROM users_salma WHERE role_salma='karyawan' AND status_user_salma='aktif' ORDER BY id_user_salma DESC LIMIT 1")
    total_user = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) as total FROM absensi_salma a
        JOIN users_salma u ON a.id_user_salma = u.id_user_salma
        WHERE a.tanggal_absensi_salma=%s AND a.status_absensi_salma='hadir'
        AND u.status_user_salma='aktif'
    """, (today,))
    total_hadir = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) as total FROM absensi_salma a
        JOIN users_salma u ON a.id_user_salma = u.id_user_salma
        WHERE a.tanggal_absensi_salma=%s AND a.status_absensi_salma='alpha'
        AND u.status_user_salma='aktif'
    """, (today,))
    tidak_hadir = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) as total FROM absensi_salma a
        JOIN users_salma u ON a.id_user_salma = u.id_user_salma
        WHERE a.tanggal_absensi_salma=%s AND a.status_absensi_salma IN ('izin','sakit')
        AND u.status_user_salma='aktif'
    """, (today,))
    total_izin = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) as n FROM users_salma u
        WHERE u.role_salma='karyawan' AND u.status_user_salma='aktif'
        AND u.id_user_salma NOT IN (
            SELECT id_user_salma FROM absensi_salma WHERE tanggal_absensi_salma=%s
        )
    """, (today,))
    belum_absen = cursor.fetchone()["n"]
    terlambat = 0

    cursor.execute("""
        SELECT COUNT(*) as n FROM surat_peringatan_salma 
        WHERE status_sp = 'menunggu_admin'
    """)
    notif_sp = cursor.fetchone()["n"]

    cursor.execute("""
        SELECT COUNT(*) as n FROM surat_peringatan_salma 
        WHERE status_sp = 'tidak_direspon' AND level_sp = 3
    """)
    notif_sp3_nonaktif = cursor.fetchone()["n"]

    

    cursor.execute("SELECT * FROM jabatan_salma ORDER BY nama_jabatan_salma")
    jabatan_list = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as n FROM pengajuan_khusus_salma WHERE status_khusus='pending'")
    notif_khusus = cursor.fetchone()["n"]

    query = """
        SELECT u.*, j.nama_jabatan_salma, j.id_jabatan_salma,
            (SELECT COUNT(*) FROM absensi_salma a
            WHERE a.id_user_salma = u.id_user_salma
            AND a.status_absensi_salma = 'alpha'
            AND YEAR(a.tanggal_absensi_salma) = YEAR(NOW())
            ) AS total_alpha_tahun
        FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.role_salma = 'karyawan'
    """
    params = []
    if keyword:
        query += " AND (u.nama_salma LIKE %s OR u.id_user_salma LIKE %s OR u.nip_salma LIKE %s)"
        params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
    if filter_jabatan:
        query += " AND u.id_jabatan_salma = %s"
        params.append(filter_jabatan)
    query += " ORDER BY u.id_user_salma ASC"
    cursor.execute(query, params)
    karyawan = cursor.fetchall()

    cursor.execute("""
        SELECT a.*, u.nama_salma, u.foto_profil_salma
        FROM absensi_salma a
        JOIN users_salma u ON a.id_user_salma = u.id_user_salma
        ORDER BY a.tanggal_absensi_salma DESC
        LIMIT 5
    """)
    recent_absen = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as n FROM izin_salma WHERE status_izin_salma='pending'")
    notif_izin = cursor.fetchone()["n"]

    cursor.execute("""
        SELECT COUNT(*) as n FROM gaji_salma
        WHERE bulan_gaji_salma=%s AND tahun_gaji_salma=%s AND status_gaji_salma='belum_dibayar'
    """, (datetime.now().month, datetime.now().year))
    notif_gaji = cursor.fetchone()["n"]

    cursor.execute("SELECT COUNT(*) as n FROM request_admin_salma WHERE status_request='menunggu'")
    notif_request = cursor.fetchone()["n"]

    notif_belum_absen = belum_absen


    cursor.execute("""
        SELECT COUNT(*) as n FROM surat_peringatan_salma 
        WHERE status_sp = 'dikirim'
    """)
    notif_sp_dikirim = cursor.fetchone()["n"]
    cursor.close()
    conn.close()

    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"

    return render_template(
        "Salma_Dashboard_Admin.html",
        total_user=total_user,
        total_hadir=total_hadir,
        tidak_hadir=tidak_hadir, 
        total_izin=total_izin,
        belum_absen=belum_absen, 
        terlambat=terlambat,
        karyawan=karyawan, 
        recent_absen=recent_absen,
        tanggal_str=tanggal_str, 
        keyword=keyword,
        filter_jabatan=filter_jabatan,
        jabatan_list=jabatan_list,
        notif_izin=notif_izin,
        notif_gaji=notif_gaji,
        notif_belum_absen=notif_belum_absen,
        notif_request=notif_request,
        notif_khusus=notif_khusus, 
        notif_sp=notif_sp,
        notif_sp_dikirim=notif_sp_dikirim,   
        notif_sp3_nonaktif=notif_sp3_nonaktif

    )

# ======================
# TAMBAH KARYAWAN
# ======================
@app.route("/admin/tambah_karyawan_page")
@admin_required
def tambah_karyawan_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jabatan_salma")
    jabatan = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("Salma_Tambah_Karyawan.html", jabatan=jabatan)


@app.route("/admin/tambah_karyawan", methods=["POST"])
@admin_required
def tambah_karyawan():
    conn = get_db_connection()
    cursor = conn.cursor()
    new_id = generate_id_user_salma("karyawan")
    cursor.execute("""
        INSERT INTO users_salma
        (id_user_salma, username_salma, password_salma, nama_salma,
         nip_salma, id_jabatan_salma, email_salma,
         nama_bank_salma, no_rekening_salma, atas_nama_salma,
         role_salma, status_user_salma)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'karyawan','aktif')
    """, (
        new_id, request.form["username"], request.form["password"],
        request.form["nama"], request.form["nip"], request.form["id_jabatan"],
        request.form["email"], request.form.get("nama_bank", ""),
        request.form.get("no_rekening", ""), request.form.get("atas_nama", ""),
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_dashboard"))



# ======================
# PROSES GAJI
# ======================

@app.route("/admin/proses_gaji/<id_user>", methods=["GET", "POST"])
@admin_required
def proses_gaji(id_user):
    conn = get_db_connection()
    cursor = conn.cursor()
 
    now = datetime.now()
 
    try:
        bulan = int(request.args.get("bulan", now.month))
        tahun = int(request.args.get("tahun", now.year))
    except (ValueError, TypeError):
        bulan = now.month
        tahun = now.year
 
    if bulan < 1 or bulan > 12:
        bulan = now.month
    if tahun < 2000 or tahun > now.year:
        tahun = now.year
 
    # ── DATA KARYAWAN ─────────────────────────────────────────────────────────
    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma, j.gaji_per_hari_salma, j.tunjangan_salma,
               j.limit_sakit_salma, j.limit_izin_salma
        FROM users_salma u
        JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.id_user_salma = %s
    """, (id_user,))
    karyawan = cursor.fetchone()
    if not karyawan:
        cursor.close(); conn.close()
        return "Data karyawan tidak ditemukan"
 
    limit_sakit = int(karyawan.get('limit_sakit_salma') or 3)
    limit_izin  = int(karyawan.get('limit_izin_salma') or 2)
 
    # ── ABSENSI ───────────────────────────────────────────────────────────────
    cursor.execute("""
        SELECT * FROM absensi_salma
        WHERE id_user_salma=%s AND MONTH(tanggal_absensi_salma)=%s AND YEAR(tanggal_absensi_salma)=%s
    """, (id_user, bulan, tahun))
    absensi = cursor.fetchall()
 
    total_hadir = sum(1 for a in absensi if a["status_absensi_salma"] == "hadir")
    total_sakit = sum(1 for a in absensi if a["status_absensi_salma"] == "sakit")
    total_izin  = sum(1 for a in absensi if a["status_absensi_salma"] == "izin")
    total_alpha = sum(1 for a in absensi if a["status_absensi_salma"] == "alpha")
    total_hari  = len(absensi)
 
    total_menit_lembur    = 0
    total_menit_terlambat = 0
 
    for a in absensi:
        info = hitung_status_jam(a.get("jam_masuk_salma"), a.get("jam_pulang_salma"))
        if info["lembur"]:
            total_menit_lembur += info["menit_lembur"]
        if info["telat"]:
            total_menit_terlambat += info["menit_telat"]
 
    def format_durasi(m):
        j, m = divmod(m, 60)
        return f"{j}j {m}m" if j else f"{m} menit"
 
    label_lembur    = format_durasi(total_menit_lembur)    if total_menit_lembur    else "0"
    label_terlambat = format_durasi(total_menit_terlambat) if total_menit_terlambat else "0"
 
    gaji_per_hari = float(karyawan["gaji_per_hari_salma"] or 0)
    tunjangan     = float(karyawan["tunjangan_salma"]     or 0)
    gaji_pokok    = total_hadir * gaji_per_hari
 
    # ── TEMPLATE POTONGAN ─────────────────────────────────────────────────────
    cursor.execute("SELECT * FROM potongan_template_salma WHERE aktif_salma=1")
    potongan_templates = cursor.fetchall()
 
    persen_sakit = 5
    persen_izin  = 10
    for pt in potongan_templates:
        nama = pt["nama_potongan_salma"].lower()
        if "sakit" in nama:
            persen_sakit = float(pt["nilai_potongan_salma"])
        elif "izin" in nama:
            persen_izin  = float(pt["nilai_potongan_salma"])
 
    # ── HITUNG POTONGAN DENGAN LIMIT ──────────────────────────────────────────
    # Alpha: selalu potong penuh
    potongan_alpha = total_alpha * gaji_per_hari
 
    # Sakit: hanya potong jika melebihi limit
    if total_sakit <= limit_sakit:
        potongan_sakit = 0
        kelebihan_sakit = 0
    else:
        kelebihan_sakit = total_sakit - limit_sakit
        potongan_sakit = kelebihan_sakit * gaji_per_hari * (persen_sakit / 100)
 
    # Izin: hanya potong jika melebihi limit
    if total_izin <= limit_izin:
        potongan_izin = 0
        kelebihan_izin = 0
    else:
        kelebihan_izin = total_izin - limit_izin
        potongan_izin = kelebihan_izin * gaji_per_hari * (persen_izin / 100)
 
    # ── POTONGAN KETERLAMBATAN OTOMATIS ───────────────────────────────────────
    potongan_terlambat      = 0
    nama_template_terlambat = ""
    persen_terlambat_aktif  = False
 
    for pt in potongan_templates:
        if pt["tipe_potongan_salma"] == "per_jam_terlambat":
            jam_terlambat          = total_menit_terlambat / 60
            potongan_terlambat     = float(pt["nilai_potongan_salma"]) * jam_terlambat
            nama_template_terlambat = pt["nama_potongan_salma"]
            persen_terlambat_aktif = True
            break
 
    potongan_absensi = potongan_alpha + potongan_sakit + potongan_izin + potongan_terlambat
 
    # ── TEMPLATE BONUS ────────────────────────────────────────────────────────
    cursor.execute("SELECT * FROM bonus_template_salma WHERE aktif_salma=1")
    bonus_templates = cursor.fetchall()
 
    # ── DATA GAJI TERSIMPAN ───────────────────────────────────────────────────
    cursor.execute("""
        SELECT * FROM gaji_salma
        WHERE id_user_salma=%s AND bulan_gaji_salma=%s AND tahun_gaji_salma=%s
        LIMIT 1
    """, (id_user, bulan, tahun))
    data_gaji = cursor.fetchone()
 
    dipilih_bonus    = []
    dipilih_potongan = []
 
    # ── POST ──────────────────────────────────────────────────────────────────
    if request.method == "POST":
        dipilih_bonus    = request.form.getlist("bonus_ids")
        dipilih_potongan = request.form.getlist("potongan_ids")
 
        total_bonus  = 0
        detail_bonus = []
 
        for bt in bonus_templates:
            if str(bt["id_bonus_template"]) in dipilih_bonus:
                if bt["tipe_bonus_salma"] == "per_jam":
                    key       = f"jam_lembur_{bt['id_bonus_template']}"
                    jam_input = float(request.form.get(key, 0) or 0)
                    nominal   = float(bt["nilai_bonus_salma"]) * jam_input
                    detail_bonus.append({
                        "nama":       bt["nama_bonus_salma"],
                        "keterangan": f"{jam_input:.1f} jam × Rp {float(bt['nilai_bonus_salma']):,.0f}/jam",
                        "nominal":    nominal
                    })
                    total_bonus += nominal
                else:
                    nominal = hitung_nilai_template(
                        bt["tipe_bonus_salma"], bt["nilai_bonus_salma"],
                        gaji_pokok, gaji_per_hari
                    )
                    detail_bonus.append({
                        "nama":       bt["nama_bonus_salma"],
                        "keterangan": bt["keterangan_salma"] or "",
                        "nominal":    nominal
                    })
                    total_bonus += nominal
 
        total_potongan_template = 0
        detail_potongan         = []
 
        # Potongan absensi otomatis — selalu masuk detail
        if potongan_alpha > 0:
            detail_potongan.append({
                "nama":       "Potongan Alpha",
                "keterangan": f"{total_alpha} hari × Rp {gaji_per_hari:,.0f}",
                "nominal":    potongan_alpha
            })
        if potongan_sakit > 0:
            detail_potongan.append({
                "nama":       "Potongan Sakit",
                "keterangan": f"Kelebihan {kelebihan_sakit} hari dari limit {limit_sakit} × {persen_sakit}% gaji harian",
                "nominal":    potongan_sakit
            })
        if potongan_izin > 0:
            detail_potongan.append({
                "nama":       "Potongan Izin",
                "keterangan": f"Kelebihan {kelebihan_izin} hari dari limit {limit_izin} × {persen_izin}% gaji harian",
                "nominal":    potongan_izin
            })
        if potongan_terlambat > 0:
            jam_t = total_menit_terlambat / 60
            detail_potongan.append({
                "nama":       nama_template_terlambat or "Potongan Keterlambatan",
                "keterangan": f"{jam_t:.2f} jam terlambat × Rp {float(next(pt['nilai_potongan_salma'] for pt in potongan_templates if pt['tipe_potongan_salma'] == 'per_jam_terlambat')):,.0f}/jam",
                "nominal":    potongan_terlambat
            })
 
        # Potongan dari template yang dipilih admin
        for pt in potongan_templates:
            if str(pt["id_potongan_template"]) in dipilih_potongan:
                nominal = hitung_nilai_template(
                    pt["tipe_potongan_salma"], pt["nilai_potongan_salma"],
                    gaji_pokok, gaji_per_hari,
                    menit_terlambat=total_menit_terlambat
                )
                ket = pt["keterangan_salma"] or ""
                if pt["tipe_potongan_salma"] == "per_jam_terlambat":
                    jam_t = total_menit_terlambat / 60
                    ket   = f"{jam_t:.2f} jam terlambat × Rp {float(pt['nilai_potongan_salma']):,.0f}/jam"
                elif pt["tipe_potongan_salma"] == "persen_gaji_bulanan":
                    ket = f"{float(pt['nilai_potongan_salma']):.0f}% × Rp {gaji_pokok:,.0f}"
                elif pt["tipe_potongan_salma"] == "persen_gaji_harian":
                    ket = f"{float(pt['nilai_potongan_salma']):.0f}% × Rp {gaji_per_hari:,.0f}/hari"
                elif pt["tipe_potongan_salma"] == "nominal":
                    ket = pt["keterangan_salma"] or f"Nominal tetap Rp {float(pt['nilai_potongan_salma']):,.0f}"
                detail_potongan.append({
                    "nama":       pt["nama_potongan_salma"],
                    "keterangan": ket,
                    "nominal":    nominal
                })
                total_potongan_template += nominal
 
        total_potongan       = potongan_absensi + total_potongan_template
        detail_bonus_json    = json.dumps(detail_bonus,    ensure_ascii=False)
        detail_potongan_json = json.dumps(detail_potongan, ensure_ascii=False)
 
        if data_gaji:
            cursor.execute("""
                UPDATE gaji_salma SET
                    gaji_pokok_salma=%s, bonus_salma=%s, potongan_salma=%s,
                    detail_bonus_salma=%s, detail_potongan_salma=%s
                WHERE id_gaji_salma=%s
            """, (gaji_pokok, total_bonus, total_potongan,
                  detail_bonus_json, detail_potongan_json,
                  data_gaji["id_gaji_salma"]))
        else:
            cursor.execute("""
                INSERT INTO gaji_salma
                    (id_user_salma, tahun_gaji_salma, bulan_gaji_salma,
                     gaji_pokok_salma, bonus_salma, potongan_salma,
                     detail_bonus_salma, detail_potongan_salma)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (id_user, tahun, bulan, gaji_pokok, total_bonus, total_potongan,
                  detail_bonus_json, detail_potongan_json))
 
        conn.commit()
        cursor.close(); conn.close()
        flash("Gaji berhasil diproses!", "success")
        return redirect(url_for("proses_gaji", id_user=id_user, bulan=bulan, tahun=tahun))
 
    # ── PREVIEW NOMINAL BONUS & POTONGAN (GET) ────────────────────────────────
    for bt in bonus_templates:
        if bt["tipe_bonus_salma"] == "per_jam":
            bt["preview_nominal"] = float(bt["nilai_bonus_salma"])
        else:
            bt["preview_nominal"] = hitung_nilai_template(
                bt["tipe_bonus_salma"], bt["nilai_bonus_salma"],
                gaji_pokok, gaji_per_hari
            )
 
    for pt in potongan_templates:
        pt["preview_nominal"] = hitung_nilai_template(
            pt["tipe_potongan_salma"], pt["nilai_potongan_salma"],
            gaji_pokok, gaji_per_hari,
            menit_terlambat=total_menit_terlambat
        )
 
    # ── PERIODE ABSENSI ───────────────────────────────────────────────────────
    cursor.execute("""
        SELECT DISTINCT MONTH(tanggal_absensi_salma) AS bln,
                        YEAR(tanggal_absensi_salma)  AS thn
        FROM absensi_salma
        WHERE id_user_salma = %s
        ORDER BY thn DESC, bln DESC
    """, (id_user,))
    periode_absensi = cursor.fetchall()
 
    # ── RIWAYAT GAJI SEMUA BULAN ──────────────────────────────────────────────
    cursor.execute("""
        SELECT * FROM gaji_salma
        WHERE id_user_salma = %s
        ORDER BY tahun_gaji_salma DESC, bulan_gaji_salma DESC
    """, (id_user,))
    histori_gaji = cursor.fetchall()
 
    cursor.close()
    conn.close()
 
    return render_template("Salma_Proses_Gaji.html",
        karyawan=karyawan,
        absensi=absensi,
        total_hadir=total_hadir,
        total_sakit=total_sakit,
        total_izin=total_izin,
        total_alpha=total_alpha,
        total_hari=total_hari,
        gaji_pokok=gaji_pokok,
        tunjangan=tunjangan,
        gaji_per_hari=gaji_per_hari,
        bonus=float(data_gaji["bonus_salma"])       if data_gaji else 0,
        potongan=float(data_gaji["potongan_salma"]) if data_gaji else 0,
        bulan=bulan,
        tahun=tahun,
        potongan_terlambat=potongan_terlambat,
        nama_template_terlambat=nama_template_terlambat,
        persen_terlambat_aktif=persen_terlambat_aktif,
        potongan_absensi=potongan_absensi,
        potongan_alpha=potongan_alpha,
        potongan_sakit=potongan_sakit,
        potongan_izin=potongan_izin,
        persen_sakit=persen_sakit,
        persen_izin=persen_izin,
        total_menit_lembur=total_menit_lembur,
        total_menit_terlambat=total_menit_terlambat,
        label_lembur=label_lembur,
        label_terlambat=label_terlambat,
        bonus_templates=bonus_templates,
        potongan_templates=potongan_templates,
        dipilih_bonus=dipilih_bonus,
        dipilih_potongan=dipilih_potongan,
        periode_absensi=periode_absensi,
        histori_gaji=histori_gaji,
        now=datetime.now(),
        limit_sakit=limit_sakit,
        limit_izin=limit_izin,
        kelebihan_sakit=kelebihan_sakit,
        kelebihan_izin=kelebihan_izin)
    
# ================== DASHBOARD KARYAWAN ==================
@app.route("/karyawan/dashboard")
def karyawan_dashboard():
    if "user_id" not in session:
        return redirect(url_for("index"))
    id_user = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE u.id_user_salma=%s
    """, (id_user,))
    karyawan = cursor.fetchone()

    bulan = datetime.now().month
    tahun = datetime.now().year
    today = datetime.now().date()

    cursor.execute("""
        SELECT status_absensi_salma, COUNT(*) as jml FROM absensi_salma
        WHERE id_user_salma=%s AND MONTH(tanggal_absensi_salma)=%s AND YEAR(tanggal_absensi_salma)=%s
        GROUP BY status_absensi_salma
    """, (id_user, bulan, tahun))
    rekap = {r["status_absensi_salma"]: r["jml"] for r in cursor.fetchall()}
    total_hadir = rekap.get("hadir", 0)
    total_izin  = rekap.get("izin", 0) 
    total_sakit = rekap.get("sakit", 0)
    total_alpha = rekap.get("alpha", 0)

    cursor.execute("""
        SELECT status_absensi_salma, jam_pulang_salma FROM absensi_salma
        WHERE id_user_salma=%s AND tanggal_absensi_salma=%s LIMIT 1
    """, (id_user, today))
    row = cursor.fetchone()
    if row and row["status_absensi_salma"] == "hadir":
        if row["jam_pulang_salma"]:
           status_hari_ini = "pulang"
        else:
           status_hari_ini = "hadir"
    else:
        status_hari_ini = row["status_absensi_salma"] if row else None

    cursor.execute("""
        SELECT * FROM gaji_salma WHERE id_user_salma=%s
        ORDER BY tahun_gaji_salma DESC, bulan_gaji_salma DESC LIMIT 1
    """, (id_user,))
    gaji = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM surat_peringatan_salma
        WHERE id_user_salma = %s AND status_sp = 'dikirim'
        ORDER BY level_sp DESC LIMIT 1
    """, (id_user,))
    sp_aktif = cursor.fetchone()

    
    cursor.execute("""
        SELECT nama_salma FROM users_salma 
        WHERE role_salma = 'admin' AND status_user_salma = 'aktif'
        LIMIT 1
    """)
    row_admin = cursor.fetchone()
    nama_admin = row_admin["nama_salma"] if row_admin else "Admin"

    cursor.execute("""
        SELECT * FROM absensi_salma WHERE id_user_salma=%s
        ORDER BY tanggal_absensi_salma DESC LIMIT 5
    """, (id_user,))
    riwayat_absensi = cursor.fetchall()

    # ← moved BEFORE close
    cursor.execute("SELECT COUNT(*) as n FROM surat_peringatan_salma WHERE status_sp='menunggu_admin'")
    notif_sp = cursor.fetchone()["n"]

    cursor.execute("SELECT COUNT(*) as n FROM surat_peringatan_salma WHERE status_sp='dikirim'")
    notif_sp_dikirim = cursor.fetchone()["n"]

    cursor.execute("SELECT COUNT(*) as n FROM surat_peringatan_salma WHERE status_sp='tidak_direspon' AND level_sp=3")
    notif_sp3_nonaktif = cursor.fetchone()["n"]

    cursor.close(); conn.close()           # ← now closes after all queries

    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"

    return render_template("Salma_Dashboard_Karyawan.html",
        karyawan=karyawan, 
        notif_sp=notif_sp,
        notif_sp_dikirim=notif_sp_dikirim,
        notif_sp3_nonaktif=notif_sp3_nonaktif,
        total_hadir=total_hadir, 
        total_sakit=total_sakit,
        total_izin=total_izin, 
        total_alpha=total_alpha,
        status_hari_ini=status_hari_ini, 
        riwayat_absensi=riwayat_absensi,
        gaji=gaji, 
        sp_aktif=sp_aktif,
        tanggal_str=tanggal_str,
        nama_admin=nama_admin)


# ================== ABSEN MASUK / PULANG ==================
@app.route("/karyawan/absen_masuk", methods=["POST"])
def absen_masuk():
    if "user_id" not in session:
        return redirect(url_for("index"))
    id_user = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute("SELECT * FROM absensi_salma WHERE id_user_salma=%s AND tanggal_absensi_salma=%s", (id_user, today))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return "Anda sudah absen hari ini"
    cursor.execute("""
        INSERT INTO absensi_salma (id_user_salma, tanggal_absensi_salma, jam_masuk_salma, status_absensi_salma)
        VALUES (%s,%s,%s,'hadir')
    """, (id_user, today, datetime.now().time()))
    conn.commit()
    cursor.close(); conn.close()
    return redirect(url_for("karyawan_dashboard"))


@app.route("/karyawan/absen_pulang", methods=["POST"])
def absen_pulang():
    if "user_id" not in session:
        return redirect(url_for("index"))
    id_user = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE absensi_salma SET jam_pulang_salma=%s
        WHERE id_user_salma=%s AND tanggal_absensi_salma=%s
    """, (datetime.now().time(), id_user, datetime.now().date()))
    conn.commit()
    cursor.close(); conn.close()
    return redirect(url_for("karyawan_dashboard"))


# ====================== PROFIL ======================
@app.route("/karyawan/profil")
def profil():
    if "user_id" not in session:
        return redirect(url_for("index"))
    id_user = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE u.id_user_salma=%s
    """, (id_user,))
    karyawan = cursor.fetchone()
    cursor.close(); conn.close()
    return render_template("Salma_Profil.html", karyawan=karyawan)


@app.route("/profil/edit", methods=["GET", "POST"])
def edit_profil():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        nama      = request.form["nama"]
        email     = request.form["email"]
        nama_bank = request.form.get("nama_bank", "")
        no_rek    = request.form.get("no_rekening", "")
        atas_nama = request.form.get("atas_nama", "")
        hapus     = request.form.get("hapus_foto", "0")
        foto_baru = None

        cursor.execute("SELECT foto_profil_salma FROM users_salma WHERE id_user_salma=%s", (user_id,))
        row = cursor.fetchone()
        foto_lama = row["foto_profil_salma"] if row else None

        if hapus == "1":
            if foto_lama:
                path_lama = os.path.join(UPLOAD_FOLDER_FOTO, foto_lama)
                if os.path.exists(path_lama):
                    os.remove(path_lama)
            foto_baru = None
        elif "foto_profil" in request.files:
            file = request.files["foto_profil"]
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                nama_file = f"user_{user_id}_{int(datetime.now().timestamp())}.{ext}"
                os.makedirs(UPLOAD_FOLDER_FOTO, exist_ok=True)
                if foto_lama:
                    path_lama = os.path.join(UPLOAD_FOLDER_FOTO, foto_lama)
                    if os.path.exists(path_lama):
                        os.remove(path_lama)
                file.save(os.path.join(UPLOAD_FOLDER_FOTO, nama_file))
                foto_baru = nama_file
            else:
                foto_baru = foto_lama

        cursor.execute("""
            UPDATE users_salma
            SET nama_salma=%s, email_salma=%s,
                nama_bank_salma=%s, no_rekening_salma=%s, atas_nama_salma=%s,
                foto_profil_salma=%s
            WHERE id_user_salma=%s
        """, (nama, email, nama_bank, no_rek, atas_nama, foto_baru, user_id))
        conn.commit()
        flash("Profil berhasil diperbarui!", "success")
        return redirect(url_for("edit_profil"))

    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma
        FROM users_salma u
        JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.id_user_salma = %s
    """, (user_id,))
    karyawan = cursor.fetchone()
    cursor.close(); conn.close()
    return render_template("Salma_Edit_Profil.html", karyawan=karyawan)


# ================== RIWAYAT GAJI ==================
@app.route("/karyawan/gaji")
def riwayat_gaji():
    if "user_id" not in session:
        return redirect(url_for("index"))
    id_user = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE u.id_user_salma=%s
    """, (id_user,))
    karyawan = cursor.fetchone()
    cursor.execute("""
        SELECT * FROM gaji_salma WHERE id_user_salma=%s
        ORDER BY tahun_gaji_salma DESC, bulan_gaji_salma DESC
    """, (id_user,))
    semua_gaji = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template("Salma_Riwayat_Gaji.html", gaji_list=semua_gaji, karyawan=karyawan)


# ============================================================
# ADMIN — REKAP PEMBAYARAN GAJI
# ============================================================
@app.route("/admin/pembayaran")
@admin_required
def admin_pembayaran():
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now()
    default_dari   = now.replace(day=1).strftime("%Y-%m-%d")
    default_sampai = now.strftime("%Y-%m-%d")

    dari   = request.args.get("dari",   default_dari)
    sampai = request.args.get("sampai", default_sampai)

    dari_dt   = datetime.strptime(dari,   "%Y-%m-%d")
    sampai_dt = datetime.strptime(sampai, "%Y-%m-%d")

    cursor.execute("""
        SELECT g.*, u.nama_salma, u.nip_salma, u.email_salma, u.foto_profil_salma,
               u.nama_bank_salma, u.no_rekening_salma, u.atas_nama_salma, j.nama_jabatan_salma
        FROM gaji_salma g
        JOIN users_salma u ON g.id_user_salma = u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE STR_TO_DATE(CONCAT(g.tahun_gaji_salma, '-', LPAD(g.bulan_gaji_salma, 2, '0'), '-01'), '%%Y-%%m-%%d')
              BETWEEN %s AND %s
        ORDER BY g.status_gaji_salma, u.nama_salma
    """, (dari_dt.replace(day=1).date(), sampai_dt.date()))

    gaji_list = cursor.fetchall()

    total_belum         = sum(1 for g in gaji_list if g["status_gaji_salma"] == "belum_dibayar")
    total_sudah         = sum(1 for g in gaji_list if g["status_gaji_salma"] == "sudah_dibayar")
    total_nominal       = sum(g["total_gaji_salma"] for g in gaji_list if g["status_gaji_salma"] == "belum_dibayar")
    total_sudah_nominal = sum(g["total_gaji_salma"] for g in gaji_list if g["status_gaji_salma"] == "sudah_dibayar")
    grand_total         = sum(g["total_gaji_salma"] for g in gaji_list)

    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"

    cursor.close(); conn.close()
    return render_template("Salma_Admin_Pembayaran.html",
        gaji_list=gaji_list, dari=dari, sampai=sampai,
        bulan_nama=bulan_nama, tanggal_str=tanggal_str,
        total_belum=total_belum, total_sudah=total_sudah,
        total_nominal=total_nominal, total_sudah_nominal=total_sudah_nominal,
        grand_total=grand_total)


# ============================================================
# SLIP GAJI
# ============================================================
@app.route("/slip_gaji/<int:id_gaji>")
def slip_gaji(id_gaji):
    if "user_id" not in session:
        return redirect(url_for("index"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.*, u.nama_salma, u.nip_salma, u.email_salma,
               u.nama_bank_salma, u.no_rekening_salma, u.atas_nama_salma,
               j.nama_jabatan_salma, j.gaji_per_hari_salma, j.tunjangan_salma
        FROM gaji_salma g
        JOIN users_salma u ON g.id_user_salma=u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE g.id_gaji_salma=%s
    """, (id_gaji,))
    data = cursor.fetchone()
    cursor.close(); conn.close()
    if not data:
        return "Data tidak ditemukan", 404
    if session.get("role") == "karyawan" and data["id_user_salma"] != session["user_id"]:
        return "Akses ditolak", 403
 
    detail_bonus    = []
    detail_potongan = []
    try:
        if data.get("detail_bonus_salma"):
            detail_bonus = json.loads(data["detail_bonus_salma"])
    except (json.JSONDecodeError, TypeError):
        detail_bonus = []
    try:
        if data.get("detail_potongan_salma"):
            detail_potongan = json.loads(data["detail_potongan_salma"])
    except (json.JSONDecodeError, TypeError):
        detail_potongan = []
 
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    return render_template("Salma_Slip_Gaji.html",
        data=data,
        bulan_nama=bulan_nama,
        detail_bonus=detail_bonus,
        detail_potongan=detail_potongan,
        now=datetime.now()
    )

# ============================================================
# ADMIN — KELOLA ABSENSI
# ============================================================
@app.route("/admin/absensi")
@admin_required
def admin_absensi():
    conn = get_db_connection()
    cursor = conn.cursor()
    bulan   = int(request.args.get("bulan", datetime.now().month))
    tahun   = int(request.args.get("tahun", datetime.now().year))
    keyword = request.args.get("keyword", "")
    query = """
        SELECT a.*, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
        FROM absensi_salma a
        JOIN users_salma u ON a.id_user_salma=u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE MONTH(a.tanggal_absensi_salma)=%s AND YEAR(a.tanggal_absensi_salma)=%s
        AND u.role_salma='karyawan'
    """
    params = [bulan, tahun]
    if keyword:
        query += " AND (u.nama_salma LIKE %s OR u.nip_salma LIKE %s)"
        params += [f"%{keyword}%", f"%{keyword}%"]
    query += " ORDER BY a.tanggal_absensi_salma DESC, u.nama_salma"
    cursor.execute(query, params)
    absensi_list = cursor.fetchall()
 
    # ── ENRICHMENT TELAT & LEMBUR ─────────────────────────────
    for a in absensi_list:
        info = hitung_status_jam(
            a.get("jam_masuk_salma"),
            a.get("jam_pulang_salma")
        )
        a["_telat"]        = info["telat"]
        a["_menit_telat"]  = info["menit_telat"]
        a["_label_telat"]  = info["label_telat"]
        a["_lembur"]       = info["lembur"]
        a["_menit_lembur"] = info["menit_lembur"]
        a["_label_lembur"] = info["label_lembur"]
    # ─────────────────────────────────────────────────────────
 
    cursor.execute(
        "SELECT * FROM users_salma WHERE role_salma='karyawan' AND status_user_salma='aktif' ORDER BY nama_salma"
    )
    karyawan_list = cursor.fetchall()
 
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
    cursor.close(); conn.close()
    return render_template("Salma_Admin_Absensi.html",
        absensi_list=absensi_list, karyawan_list=karyawan_list,
        bulan=bulan, tahun=tahun, keyword=keyword,
        bulan_nama=bulan_nama, tanggal_str=tanggal_str)
 

@app.route("/admin/absensi/tambah", methods=["POST"])
@admin_required
def admin_tambah_absensi():
    conn = get_db_connection()
    cursor = conn.cursor()
    id_user    = request.form["id_user"]
    tanggal    = request.form["tanggal"]
    status     = request.form["status"]
    jam_masuk  = request.form.get("jam_masuk") or None
    jam_pulang = request.form.get("jam_pulang") or None
    cursor.execute("SELECT id_absensi_salma FROM absensi_salma WHERE id_user_salma=%s AND tanggal_absensi_salma=%s", (id_user, tanggal))
    if cursor.fetchone():
        cursor.execute("UPDATE absensi_salma SET status_absensi_salma=%s,jam_masuk_salma=%s,jam_pulang_salma=%s WHERE id_user_salma=%s AND tanggal_absensi_salma=%s",
            (status, jam_masuk, jam_pulang, id_user, tanggal))
    else:
        cursor.execute("INSERT INTO absensi_salma (id_user_salma,tanggal_absensi_salma,jam_masuk_salma,jam_pulang_salma,status_absensi_salma) VALUES (%s,%s,%s,%s,%s)",
            (id_user, tanggal, jam_masuk, jam_pulang, status))
    cek_dan_buat_sp(cursor, conn, id_user)
    conn.commit(); cursor.close(); conn.close()
    flash("Data absensi berhasil disimpan!", "success")
    return redirect(url_for("admin_absensi"))


@app.route("/admin/absensi/hapus/<int:id_absensi>")
@admin_required
def admin_hapus_absensi(id_absensi):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM absensi_salma WHERE id_absensi_salma=%s", (id_absensi,))
    conn.commit(); cursor.close(); conn.close()
    flash("Data absensi dihapus.", "success")
    return redirect(url_for("admin_absensi"))


# ============================================================
# ADMIN — KELOLA IZIN
# ============================================================
@app.route("/admin/izin")
@admin_required
def admin_izin():
    conn = get_db_connection()
    cursor = conn.cursor()
    status_filter = request.args.get("status", "pending")

    # ← UBAH BAGIAN QUERY INI
    if status_filter == "semua":
        cursor.execute("""
            SELECT i.*, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
            FROM izin_salma i
            JOIN users_salma u ON i.id_user_salma=u.id_user_salma
            LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
            ORDER BY i.created_at_salma DESC
        """)
    else:
        cursor.execute("""
            SELECT i.*, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
            FROM izin_salma i
            JOIN users_salma u ON i.id_user_salma=u.id_user_salma
            LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
            WHERE i.status_izin_salma=%s ORDER BY i.created_at_salma DESC
        """, (status_filter,))
    izin_list = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) as n FROM izin_salma WHERE status_izin_salma='pending'")
    pending_count = cursor.fetchone()["n"]
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
    cursor.close(); conn.close()
    return render_template("Salma_Admin_Izin.html",
        izin_list=izin_list, status_filter=status_filter,
        pending_count=pending_count, tanggal_str=tanggal_str)


@app.route("/admin/izin/setujui/<int:id_izin>", methods=["POST"])
@admin_required
def admin_setujui_izin(id_izin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE izin_salma SET status_izin_salma='disetujui' WHERE id_izin_salma=%s", (id_izin,))
    cursor.execute("SELECT * FROM izin_salma WHERE id_izin_salma=%s", (id_izin,))
    izin = cursor.fetchone()
    if izin:
        cur_date = izin["tanggal_mulai_salma"]
        while cur_date <= izin["tanggal_selesai_salma"]:
            cursor.execute("SELECT id_absensi_salma FROM absensi_salma WHERE id_user_salma=%s AND tanggal_absensi_salma=%s",
                (izin["id_user_salma"], cur_date))
            if cursor.fetchone():
                cursor.execute("UPDATE absensi_salma SET status_absensi_salma=%s WHERE id_user_salma=%s AND tanggal_absensi_salma=%s",
                    (izin["jenis_izin_salma"], izin["id_user_salma"], cur_date))
            else:
                cursor.execute("INSERT INTO absensi_salma (id_user_salma,tanggal_absensi_salma,status_absensi_salma) VALUES (%s,%s,%s)",
                    (izin["id_user_salma"], cur_date, izin["jenis_izin_salma"]))
            cur_date += timedelta(days=1)
    if izin:
        cek_dan_buat_sp(cursor, conn, izin["id_user_salma"])
    conn.commit(); cursor.close(); conn.close()
    flash("Pengajuan izin berhasil disetujui.", "success")
    return redirect(url_for("admin_izin"))


@app.route("/admin/izin/konfirmasi_tolak/<int:id_izin>", methods=["GET", "POST"])
@admin_required
def admin_konfirmasi_tolak(id_izin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
        FROM izin_salma i
        JOIN users_salma u ON i.id_user_salma=u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE i.id_izin_salma=%s
    """, (id_izin,))
    izin = cursor.fetchone()
    if not izin:
        cursor.close(); conn.close()
        flash("Data izin tidak ditemukan.", "error")
        return redirect(url_for("admin_izin"))
    if izin["status_izin_salma"] != "pending":
        cursor.close(); conn.close()
        flash("Pengajuan ini sudah diproses sebelumnya.", "error")
        return redirect(url_for("admin_izin"))
    error = None
    if request.method == "POST":
        alasan_tolak = request.form.get("alasan_tolak", "").strip()
        if not alasan_tolak:
            error = "Alasan penolakan wajib diisi agar karyawan mengerti."
        else:
            try:
                cursor.execute("""
                    UPDATE izin_salma SET status_izin_salma='ditolak', alasan_tolak_salma=%s
                    WHERE id_izin_salma=%s
                """, (alasan_tolak, id_izin))
            except Exception:
                cursor.execute("UPDATE izin_salma SET status_izin_salma='ditolak' WHERE id_izin_salma=%s", (id_izin,))
            conn.commit()
            cursor.close(); conn.close()
            flash(f"Pengajuan izin {izin['nama_salma']} berhasil ditolak.", "success")
            return redirect(url_for("admin_izin"))
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
    cursor.close(); conn.close()
    return render_template("Salma_Admin_Konfirmasi_Tolak.html",
        izin=izin, error=error, tanggal_str=tanggal_str)


# ============================================================
# ADMIN — KELOLA JABATAN
# ============================================================
@app.route("/admin/jabatan")
@admin_required
def admin_jabatan():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jabatan_salma ORDER BY nama_jabatan_salma")
    jabatan_list = cursor.fetchall()
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
    cursor.close(); conn.close()
    return render_template("Salma_Admin_Jabatan.html", jabatan_list=jabatan_list, tanggal_str=tanggal_str)


@app.route("/admin/jabatan/tambah", methods=["POST"])
@admin_required
def admin_tambah_jabatan():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jabatan_salma
            (nama_jabatan_salma, gaji_per_hari_salma, tunjangan_salma,
             limit_izin_salma, limit_sakit_salma, limit_cuti_salma)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        request.form["nama"],
        request.form["gaji_per_hari"],
        request.form["tunjangan"],
        int(request.form.get("limit_izin",  2)),
        int(request.form.get("limit_sakit", 3)),
        int(request.form.get("limit_cuti",  12)),
    ))
    conn.commit(); cursor.close(); conn.close()
    flash("Jabatan berhasil ditambahkan!", "success")
    return redirect(url_for("admin_jabatan"))


@app.route("/admin/jabatan/edit/<int:id_jabatan>", methods=["POST"])
@admin_required
def admin_edit_jabatan(id_jabatan):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jabatan_salma
        SET nama_jabatan_salma  = %s,
            gaji_per_hari_salma = %s,
            tunjangan_salma     = %s,
            limit_izin_salma    = %s,
            limit_sakit_salma   = %s,
            limit_cuti_salma    = %s
        WHERE id_jabatan_salma  = %s
    """, (
        request.form["nama"],
        request.form["gaji_per_hari"],
        request.form["tunjangan"],
        int(request.form.get("limit_izin",  2)),
        int(request.form.get("limit_sakit", 3)),
        int(request.form.get("limit_cuti",  12)),
        id_jabatan,
    ))
    conn.commit(); cursor.close(); conn.close()
    flash("Jabatan berhasil diperbarui!", "success")
    return redirect(url_for("admin_jabatan"))


@app.route("/admin/jabatan/hapus/<int:id_jabatan>")
@admin_required
def admin_hapus_jabatan(id_jabatan):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jabatan_salma WHERE id_jabatan_salma=%s", (id_jabatan,))
    conn.commit(); cursor.close(); conn.close()
    flash("Jabatan dihapus.", "success")
    return redirect(url_for("admin_jabatan"))


# ============================================================
# ADMIN — KELOLA BONUS & POTONGAN
# ============================================================


@app.route("/admin/bonus")
@admin_required
def admin_bonus():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bonus_template_salma ORDER BY aktif_salma DESC, nama_bonus_salma")
    bonus_list = cursor.fetchall()
    
    hari_nama = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
    
    cursor.close()
    conn.close()
    return render_template("Salma_Admin_Bonus.html",
        bonus_list=bonus_list, tanggal_str=tanggal_str)


@app.route("/admin/bonus/tambah", methods=["POST"])
@admin_required
def admin_tambah_bonus():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    nama = request.form.get("nama", "").strip()
    tipe = request.form.get("tipe")
    nilai = request.form.get("nilai", 0)
    keterangan = request.form.get("keterangan", "")
    aktif = int(request.form.get("aktif", 1))
    
    if not nama:
        flash("Nama bonus wajib diisi!", "error")
        return redirect(url_for("admin_bonus"))
    
    try:
        cursor.execute("""
            INSERT INTO bonus_template_salma 
            (nama_bonus_salma, tipe_bonus_salma, nilai_bonus_salma, 
             keterangan_salma, aktif_salma)
            VALUES (%s, %s, %s, %s, %s)
        """, (nama, tipe, nilai, keterangan, aktif))
        conn.commit()
        flash(f"Bonus '{nama}' berhasil ditambahkan!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal menambahkan bonus: {str(e)}", "error")
    
    cursor.close()
    conn.close()
    return redirect(url_for("admin_bonus"))


@app.route("/admin/bonus/edit/<int:id_tpl>", methods=["POST"])
@admin_required
def admin_edit_bonus(id_tpl):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    nama = request.form.get("nama", "").strip()
    tipe = request.form.get("tipe")
    nilai = request.form.get("nilai", 0)
    keterangan = request.form.get("keterangan", "")
    aktif = int(request.form.get("aktif", 1))
    
    if not nama:
        flash("Nama bonus wajib diisi!", "error")
        return redirect(url_for("admin_bonus"))
    
    try:
        cursor.execute("""
            UPDATE bonus_template_salma
            SET nama_bonus_salma = %s,
                tipe_bonus_salma = %s,
                nilai_bonus_salma = %s,
                keterangan_salma = %s,
                aktif_salma = %s
            WHERE id_bonus_template = %s
        """, (nama, tipe, nilai, keterangan, aktif, id_tpl))
        conn.commit()
        flash(f"Bonus '{nama}' berhasil diperbarui!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal memperbarui bonus: {str(e)}", "error")
    
    cursor.close()
    conn.close()
    return redirect(url_for("admin_bonus"))


@app.route("/admin/bonus/hapus/<int:id_tpl>", methods=["POST"])
@admin_required
def admin_hapus_bonus(id_tpl):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT nama_bonus_salma FROM bonus_template_salma WHERE id_bonus_template = %s", (id_tpl,))
        bonus = cursor.fetchone()
        nama = bonus["nama_bonus_salma"] if bonus else "Bonus"
        
        cursor.execute("DELETE FROM bonus_template_salma WHERE id_bonus_template = %s", (id_tpl,))
        conn.commit()
        flash(f"Bonus '{nama}' berhasil dihapus!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal menghapus bonus: {str(e)}", "error")
    
    cursor.close()
    conn.close()
    return redirect(url_for("admin_bonus"))


@app.route("/admin/potongan")
@admin_required
def admin_potongan():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM potongan_template_salma ORDER BY aktif_salma DESC, nama_potongan_salma")
    potongan_list = cursor.fetchall()
    
    hari_nama = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
    
    cursor.close()
    conn.close()
    return render_template("Salma_Admin_Potongan.html",
        potongan_list=potongan_list, tanggal_str=tanggal_str)


@app.route("/admin/potongan/tambah", methods=["POST"])
@admin_required
def admin_tambah_potongan():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    nama = request.form.get("nama", "").strip()
    tipe = request.form.get("tipe")
    nilai = request.form.get("nilai", 0)
    keterangan = request.form.get("keterangan", "")
    aktif = int(request.form.get("aktif", 1))
    
    if not nama:
        flash("Nama potongan wajib diisi!", "error")
        return redirect(url_for("admin_potongan"))
    
    try:
        cursor.execute("""
            INSERT INTO potongan_template_salma 
            (nama_potongan_salma, tipe_potongan_salma, nilai_potongan_salma, 
             keterangan_salma, aktif_salma)
            VALUES (%s, %s, %s, %s, %s)
        """, (nama, tipe, nilai, keterangan, aktif))
        conn.commit()
        flash(f"Potongan '{nama}' berhasil ditambahkan!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal menambahkan potongan: {str(e)}", "error")
    
    cursor.close()
    conn.close()
    return redirect(url_for("admin_potongan"))


@app.route("/admin/potongan/edit/<int:id_tpl>", methods=["POST"])
@admin_required
def admin_edit_potongan(id_tpl):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    nama = request.form.get("nama", "").strip()
    tipe = request.form.get("tipe")
    nilai = request.form.get("nilai", 0)
    keterangan = request.form.get("keterangan", "")
    aktif = int(request.form.get("aktif", 1))
    
    if not nama:
        flash("Nama potongan wajib diisi!", "error")
        return redirect(url_for("admin_potongan"))
    
    try:
        cursor.execute("""
            UPDATE potongan_template_salma
            SET nama_potongan_salma = %s,
                tipe_potongan_salma = %s,
                nilai_potongan_salma = %s,
                keterangan_salma = %s,
                aktif_salma = %s
            WHERE id_potongan_template = %s
        """, (nama, tipe, nilai, keterangan, aktif, id_tpl))
        conn.commit()
        flash(f"Potongan '{nama}' berhasil diperbarui!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal memperbarui potongan: {str(e)}", "error")
    
    cursor.close()
    conn.close()
    return redirect(url_for("admin_potongan"))


@app.route("/admin/potongan/hapus/<int:id_tpl>", methods=["POST"])
@admin_required
def admin_hapus_potongan(id_tpl):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT nama_potongan_salma FROM potongan_template_salma WHERE id_potongan_template = %s", (id_tpl,))
        potongan = cursor.fetchone()
        nama = potongan["nama_potongan_salma"] if potongan else "Potongan"
        
        cursor.execute("DELETE FROM potongan_template_salma WHERE id_potongan_template = %s", (id_tpl,))
        conn.commit()
        flash(f"Potongan '{nama}' berhasil dihapus!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal menghapus potongan: {str(e)}", "error")
    
    cursor.close()
    conn.close()
    return redirect(url_for("admin_potongan"))

# ============================================================
# ADMIN — TANDAI GAJI DIBAYAR
# ============================================================
@app.route("/admin/gaji/bayar/<int:id_gaji>")
@admin_required
def admin_bayar_gaji(id_gaji):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_user_salma FROM gaji_salma WHERE id_gaji_salma=%s", (id_gaji,))
    row = cursor.fetchone()
    cursor.execute("UPDATE gaji_salma SET status_gaji_salma='sudah_dibayar',tanggal_pembayaran_salma=%s WHERE id_gaji_salma=%s",
        (datetime.now().date(), id_gaji))
    conn.commit(); cursor.close(); conn.close()
    flash("Gaji berhasil ditandai sudah dibayar!", "success")
    if row:
        return redirect(url_for("proses_gaji", id_user=row["id_user_salma"]))
    return redirect(url_for("admin_dashboard"))


# ============================================================
# ADMIN — TOGGLE STATUS KARYAWAN
# ============================================================
@app.route("/admin/karyawan/toggle/<id_user>")
@admin_required
def admin_toggle_karyawan(id_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status_user_salma FROM users_salma WHERE id_user_salma=%s", (id_user,))
    row = cursor.fetchone()
    if row:
        new_status = "nonaktif" if row["status_user_salma"] == "aktif" else "aktif"
        cursor.execute("UPDATE users_salma SET status_user_salma=%s WHERE id_user_salma=%s", (new_status, id_user))
        conn.commit()
        flash(f"Status karyawan diubah menjadi {new_status}.", "success")
    cursor.close(); conn.close()
    return redirect(url_for("admin_dashboard"))




@app.route("/karyawan/izin", methods=["GET", "POST"])
def karyawan_izin():
    if "user_id" not in session:
        return redirect(url_for("index"))

    id_user = session["user_id"]
    os.makedirs(UPLOAD_FOLDER_IZIN, exist_ok=True)
    conn   = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        form_type       = request.form.get("form_type", "normal")  # "normal" atau "khusus"
        jenis           = request.form["jenis"]
        tanggal_mulai   = request.form["tanggal_mulai"]
        tanggal_selesai = request.form["tanggal_selesai"]
        alasan          = request.form["alasan"]

        tgl_mulai_dt   = datetime.strptime(tanggal_mulai,   "%Y-%m-%d").date()
        tgl_selesai_dt = datetime.strptime(tanggal_selesai, "%Y-%m-%d").date()

        if tgl_selesai_dt < tgl_mulai_dt:
            flash("Tanggal selesai tidak boleh sebelum tanggal mulai.", "error")
            cursor.close(); conn.close()
            return redirect(url_for("karyawan_izin"))

        # ── Validasi khusus untuk Sakit (berlaku untuk form normal & khusus) ──
        if jenis == 'sakit':
            today = date.today()
            if tgl_mulai_dt != today:
                flash("Tidak bisa mengajukan izin sakit untuk hari lain di hari ini. Silahkan ajukan di hari tersebut.", "error")
                cursor.close()
                conn.close()
                return redirect(url_for("karyawan_izin"))
            now_time = datetime.now().time()
            if now_time >= time(12, 0):
                flash("Pengajuan sakit hanya bisa dilakukan sebelum jam 12:00.", "error")
                cursor.close()
                conn.close()
                return redirect(url_for("karyawan_izin"))

        # Upload foto/bukti
        foto_filename = None
        foto = request.files.get("foto_bukti")
        if foto and foto.filename:
            allowed = {"jpg", "jpeg", "png", "pdf"}
            ext = foto.filename.rsplit(".", 1)[-1].lower() if "." in foto.filename else ""
            if ext in allowed:
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                foto_filename = f"{id_user}_{ts}.{ext}"
                foto.save(os.path.join(UPLOAD_FOLDER_IZIN, foto_filename))

        # ── PENGAJUAN KHUSUS ──────────────────────────────────────────────────
        if form_type == "khusus":
            alasan_khusus = request.form.get("alasan_khusus", "").strip()
            if not alasan_khusus:
                flash("Alasan khusus/darurat wajib diisi untuk pengajuan khusus.", "error")
                cursor.close(); conn.close()
                return redirect(url_for("karyawan_izin"))

            try:
                cursor.execute("""
                    INSERT INTO pengajuan_khusus_salma
                        (id_user_salma, jenis_izin_salma, tanggal_mulai_salma,
                         tanggal_selesai_salma, alasan_izin_salma, alasan_khusus_salma,
                         foto_bukti_salma, status_khusus)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'pending')
                """, (id_user, jenis, tanggal_mulai, tanggal_selesai,
                      alasan, alasan_khusus, foto_filename))
                conn.commit()
                flash(
                    "Pengajuan khusus berhasil dikirim! Admin akan mempertimbangkan kondisi darurat kamu.",
                    "success"
                )
            except Exception as e:
                conn.rollback()
                flash(f"Gagal mengirim pengajuan khusus: {str(e)}", "error")

            cursor.close(); conn.close()
            return redirect(url_for("karyawan_izin") + "#khusus")

        # ── PENGAJUAN NORMAL ──────────────────────────────────────────────────
        durasi_baru = (tgl_selesai_dt - tgl_mulai_dt).days + 1
        limits      = get_limit_izin(cursor, id_user)
        limit_jenis = limits.get(jenis, 0)
        sudah_pakai = hitung_hari_terpakai(cursor, id_user, jenis, tgl_mulai_dt)
        melebihi    = (sudah_pakai + durasi_baru) > limit_jenis
        satuan      = "tahun" if jenis == "cuti" else "bulan"

        if melebihi:
            # Untuk izin dan sakit yang melebihi limit → arahkan ke pengajuan khusus
            # Cuti tidak masuk pengajuan khusus
            if jenis in ("izin", "sakit"):
                flash(
                    f"Kuota {jenis} {satuan} ini sudah habis (limit {limit_jenis} hari, terpakai {sudah_pakai} hari). "
                    f"Silakan gunakan form Pengajuan Khusus di bawah jika kondisimu mendesak.",
                    "warning"
                )
                cursor.close(); conn.close()
                return redirect(url_for("karyawan_izin") + "#form-khusus")
            else:
                # Cuti tetap otomatis ditolak seperti semula
                status_awal  = "ditolak"
                alasan_tolak = (
                    f"Otomatis ditolak: kuota {jenis} {satuan} ini sudah habis "
                    f"(limit {limit_jenis} hari, sudah terpakai {sudah_pakai} hari)."
                )
        else:
            status_awal  = "pending"
            alasan_tolak = None

        try:
            cursor.execute("""
                INSERT INTO izin_salma
                    (id_user_salma, tanggal_mulai_salma, tanggal_selesai_salma,
                     jenis_izin_salma, alasan_izin_salma, foto_bukti_salma,
                     status_izin_salma, alasan_tolak_salma)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (id_user, tanggal_mulai, tanggal_selesai,
                  jenis, alasan, foto_filename,
                  status_awal, alasan_tolak))
            conn.commit()

            if melebihi:
                flash(
                    f"Pengajuan {jenis} otomatis ditolak karena kuota sudah habis.",
                    "error"
                )
            else:
                flash("Pengajuan izin berhasil dikirim!", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Gagal mengirim pengajuan: {str(e)}", "error")

        cursor.close(); conn.close()
        return redirect(url_for("karyawan_izin"))

    # ── GET ───────────────────────────────────────────────────────────────────
    cursor.execute(
        "SELECT * FROM izin_salma WHERE id_user_salma=%s ORDER BY created_at_salma DESC",
        (id_user,)
    )
    izin_list = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM pengajuan_khusus_salma WHERE id_user_salma=%s ORDER BY created_at_salma DESC",
        (id_user,)
    )
    khusus_list = cursor.fetchall()

    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma,
               j.limit_izin_salma, j.limit_sakit_salma, j.limit_cuti_salma
        FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.id_user_salma = %s
    """, (id_user,))
    karyawan = cursor.fetchone()

    today = date.today()
    kuota = {}
    for jenis in ("izin", "sakit", "cuti"):
        default = {"izin": 2, "sakit": 3, "cuti": 12}
        limit    = int((karyawan or {}).get(f"limit_{jenis}_salma") or default[jenis])
        terpakai = hitung_hari_terpakai(cursor, id_user, jenis, today)
        kuota[jenis] = {
            "limit":    limit,
            "terpakai": terpakai,
            "sisa":     max(0, limit - terpakai)
        }

    cursor.close(); conn.close()
    return render_template(
        "Salma_Karyawan_Izin.html",
        izin_list=izin_list,
        khusus_list=khusus_list,
        karyawan=karyawan,
        kuota=kuota
    )
# ============================================================
# ADMIN — KELOLA IZIN KHUSUS (halaman baru)
# ============================================================

@app.route("/admin/izin_khusus")
@admin_required
def admin_izin_khusus():
    conn = get_db_connection()
    cursor = conn.cursor()
    status_filter = request.args.get("status", "pending")

    if status_filter == "semua":
        cursor.execute("""
            SELECT k.*, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
            FROM pengajuan_khusus_salma k
            JOIN users_salma u ON k.id_user_salma = u.id_user_salma
            LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
            ORDER BY k.created_at_salma DESC
        """)
    else:
        cursor.execute("""
            SELECT k.*, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
            FROM pengajuan_khusus_salma k
            JOIN users_salma u ON k.id_user_salma = u.id_user_salma
            LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
            WHERE k.status_khusus = %s
            ORDER BY k.created_at_salma DESC
        """, (status_filter,))
    khusus_list = cursor.fetchall()

    # Stats per status
    cursor.execute("""
        SELECT status_khusus, COUNT(*) as n
        FROM pengajuan_khusus_salma
        GROUP BY status_khusus
    """)
    stats_raw = {r["status_khusus"]: r["n"] for r in cursor.fetchall()}
    stats = {
        "pending":   stats_raw.get("pending",   0),
        "disetujui": stats_raw.get("disetujui", 0),
        "ditolak":   stats_raw.get("ditolak",   0),
    }
    pending_count = stats["pending"]

    # Notif izin normal untuk sidebar
    cursor.execute("SELECT COUNT(*) as n FROM izin_salma WHERE status_izin_salma='pending'")
    pending_izin_count = cursor.fetchone()["n"]

    bulan_nama = ['','Januari','Februari','Maret','April','Mei','Juni',
                  'Juli','Agustus','September','Oktober','November','Desember']
    hari_nama  = ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"

    cursor.close(); conn.close()
    return render_template("Salma_Admin_Izin_Khusus.html",
        khusus_list=khusus_list,
        status_filter=status_filter,
        stats=stats,
        pending_count=pending_count,
        pending_izin_count=pending_izin_count,
        tanggal_str=tanggal_str
    )


@app.route("/admin/izin_khusus/setujui/<int:id_khusus>", methods=["POST"])
@admin_required
def admin_setujui_izin_khusus(id_khusus):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE pengajuan_khusus_salma SET status_khusus='disetujui' WHERE id_khusus=%s",
        (id_khusus,)
    )
    # Setelah disetujui, update absensi seperti izin normal
    cursor.execute("SELECT * FROM pengajuan_khusus_salma WHERE id_khusus=%s", (id_khusus,))
    khusus = cursor.fetchone()
    if khusus:
        cur_date = khusus["tanggal_mulai_salma"]
        while cur_date <= khusus["tanggal_selesai_salma"]:
            cursor.execute(
                "SELECT id_absensi_salma FROM absensi_salma WHERE id_user_salma=%s AND tanggal_absensi_salma=%s",
                (khusus["id_user_salma"], cur_date)
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE absensi_salma SET status_absensi_salma=%s WHERE id_user_salma=%s AND tanggal_absensi_salma=%s",
                    (khusus["jenis_izin_salma"], khusus["id_user_salma"], cur_date)
                )
            else:
                cursor.execute(
                    "INSERT INTO absensi_salma (id_user_salma, tanggal_absensi_salma, status_absensi_salma) VALUES (%s,%s,%s)",
                    (khusus["id_user_salma"], cur_date, khusus["jenis_izin_salma"])
                )
            cur_date += timedelta(days=1)

    if khusus:
        cek_dan_buat_sp(cursor, conn, khusus["id_user_salma"])
    conn.commit()
    cursor.close(); conn.close()
    flash("Pengajuan khusus berhasil disetujui dan absensi telah diupdate.", "success")
    return redirect(url_for("admin_izin_khusus"))


@app.route("/admin/izin_khusus/tolak/<int:id_khusus>", methods=["GET", "POST"])
@admin_required
def admin_tolak_izin_khusus(id_khusus):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT k.*, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
        FROM pengajuan_khusus_salma k
        JOIN users_salma u ON k.id_user_salma = u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE k.id_khusus = %s
    """, (id_khusus,))
    khusus = cursor.fetchone()

    if not khusus:
        cursor.close(); conn.close()
        flash("Data pengajuan khusus tidak ditemukan.", "error")
        return redirect(url_for("admin_izin_khusus"))

    if khusus["status_khusus"] != "pending":
        cursor.close(); conn.close()
        flash("Pengajuan ini sudah diproses.", "error")
        return redirect(url_for("admin_izin_khusus"))

    error = None
    if request.method == "POST":
        alasan_tolak = request.form.get("alasan_tolak", "").strip()
        if not alasan_tolak:
            error = "Alasan penolakan wajib diisi."
        else:
            cursor.execute("""
                UPDATE pengajuan_khusus_salma
                SET status_khusus='ditolak', alasan_tolak_salma=%s
                WHERE id_khusus=%s
            """, (alasan_tolak, id_khusus))
            conn.commit()
            cursor.close(); conn.close()
            flash(f"Pengajuan khusus {khusus['nama_salma']} berhasil ditolak.", "success")
            return redirect(url_for("admin_izin_khusus"))

    bulan_nama = ['','Januari','Februari','Maret','April','Mei','Juni',
                  'Juli','Agustus','September','Oktober','November','Desember']
    hari_nama  = ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"

    cursor.close(); conn.close()
    return render_template("Salma_Admin_Konfirmasi_Tolak_Khusus.html",
        khusus=khusus, error=error, tanggal_str=tanggal_str
    )

# ============================================================
# KARYAWAN — GANTI PASSWORD
# ============================================================
@app.route("/karyawan/ganti_password", methods=["GET", "POST"])
def ganti_password():
    if "user_id" not in session:
        return redirect(url_for("index"))
    id_user = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    error = None
    if request.method == "POST":
        pw_lama    = request.form["password_lama"]
        pw_baru    = request.form["password_baru"]
        pw_konfirm = request.form["password_konfirm"]
        cursor.execute("SELECT password_salma FROM users_salma WHERE id_user_salma=%s", (id_user,))
        row = cursor.fetchone()
        if row["password_salma"] != pw_lama:
            error = "Password lama tidak sesuai."
        elif pw_baru != pw_konfirm:
            error = "Konfirmasi password baru tidak cocok."
        elif len(pw_baru) < 6:
            error = "Password baru minimal 6 karakter."
        else:
            cursor.execute("UPDATE users_salma SET password_salma=%s WHERE id_user_salma=%s", (pw_baru, id_user))
            conn.commit(); cursor.close(); conn.close()
            flash("Password berhasil diubah!", "success")
            return redirect(url_for("ganti_password"))
    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE u.id_user_salma=%s
    """, (id_user,))
    karyawan = cursor.fetchone()
    cursor.close(); conn.close()
    return render_template("Salma_Ganti_Password.html", karyawan=karyawan, error=error)


# ============================================================
# ADMIN — LAPORAN KARYAWAN (per individu)
# ============================================================
@app.route("/admin/laporan/karyawan/<id_user>")
@admin_required
def admin_laporan_karyawan(id_user):
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now()
    default_dari   = now.replace(day=1).strftime("%Y-%m-%d")
    default_sampai = now.strftime("%Y-%m-%d")

    dari   = request.args.get("dari",   default_dari)
    sampai = request.args.get("sampai", default_sampai)

    dt    = datetime.strptime(dari, "%Y-%m-%d")
    bulan = dt.month
    tahun = dt.year

    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma, j.gaji_per_hari_salma
        FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE u.id_user_salma=%s
    """, (id_user,))
    karyawan = cursor.fetchone()

    if not karyawan:
        return "Karyawan tidak ditemukan", 404

    cursor.execute("""
        SELECT * FROM absensi_salma
        WHERE id_user_salma=%s
        AND tanggal_absensi_salma BETWEEN %s AND %s
        ORDER BY tanggal_absensi_salma ASC
    """, (id_user, dari, sampai))
    absensi = cursor.fetchall()

    hadir = sum(1 for a in absensi if a["status_absensi_salma"] == "hadir")
    izin  = sum(1 for a in absensi if a["status_absensi_salma"] == "izin")
    sakit  = sum(1 for a in absensi if a["status_absensi_salma"] == "sakit")
    alpha = sum(1 for a in absensi if a["status_absensi_salma"] == "alpha")

    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    cursor.close(); conn.close()
    return render_template(
        "Salma_Laporan_Karyawan.html",
        karyawan=karyawan, absensi=absensi,
        dari=dari, sampai=sampai,
        bulan=bulan, tahun=tahun,
        bulan_nama=bulan_nama,
        total_hadir=hadir, total_izin=izin, total_alpha=alpha, total_sakit=sakit,
        now=datetime.now()
    )


# ============================================================
# ADMIN — LAPORAN REKAP SEMUA KARYAWAN
# ============================================================
@app.route("/admin/laporan")
@admin_required
def admin_laporan():
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now()
    default_dari   = now.replace(day=1).strftime("%Y-%m-%d")
    default_sampai = now.strftime("%Y-%m-%d")

    dari   = request.args.get("dari",   default_dari)
    sampai = request.args.get("sampai", default_sampai)

    cursor.execute("""
        SELECT
            u.id_user_salma, u.nama_salma, u.nip_salma, u.foto_profil_salma,
            j.nama_jabatan_salma,
            SUM(CASE WHEN a.status_absensi_salma = 'hadir'            THEN 1 ELSE 0 END) AS hadir,
            SUM(CASE WHEN a.status_absensi_salma ='izin'              THEN 1 ELSE 0 END) AS izin,
            SUM(CASE WHEN a.status_absensi_salma ='sakit'             THEN 1 ELSE 0 END) AS sakit,
            SUM(CASE WHEN a.status_absensi_salma = 'alpha'            THEN 1 ELSE 0 END) AS alpha,
            COUNT(a.id_absensi_salma) AS total
        FROM users_salma u
        LEFT JOIN absensi_salma a
            ON u.id_user_salma = a.id_user_salma
            AND a.tanggal_absensi_salma BETWEEN %s AND %s
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.role_salma = 'karyawan'
        GROUP BY u.id_user_salma, u.nama_salma, u.nip_salma, u.foto_profil_salma, j.nama_jabatan_salma
        ORDER BY u.nama_salma
    """, (dari, sampai))
    rekap = cursor.fetchall()

    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"

    cursor.close(); conn.close()
    return render_template("Salma_Admin_Laporan.html",
        rekap=rekap, dari=dari, sampai=sampai,
        bulan_nama=bulan_nama, tanggal_str=tanggal_str)


# ========================================= ===================
# ADMIN — RESET PASSWORD KARYAWAN
# ============================================================
@app.route("/admin/reset_password/<id_user>", methods=["POST"])
@admin_required
def admin_reset_password(id_user):
    pw_baru = request.form.get("password_baru", "").strip()
    if len(pw_baru) < 6:
        flash("Password baru minimal 6 karakter!", "error")
        return redirect(url_for("admin_dashboard"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users_salma SET password_salma=%s WHERE id_user_salma=%s", (pw_baru, id_user))
    conn.commit()
    cursor.execute("SELECT nama_salma FROM users_salma WHERE id_user_salma=%s", (id_user,))
    nama = cursor.fetchone()["nama_salma"]
    cursor.close(); conn.close()
    flash(f"Password {nama} berhasil direset!", "success")
    return redirect(url_for("admin_dashboard"))


# ============================================================
# ADMIN — KELOLA HARI LIBUR
# ============================================================
@app.route("/admin/hari_libur")
@admin_required
def admin_hari_libur():
    conn = get_db_connection()
    cursor = conn.cursor()
    tahun = int(request.args.get("tahun", datetime.now().year))
    cursor.execute("SELECT * FROM hari_libur_salma WHERE YEAR(tanggal_libur_salma)=%s ORDER BY tanggal_libur_salma", (tahun,))
    libur_list = cursor.fetchall()
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
    cursor.close(); conn.close()
    return render_template("Salma_Admin_HariLibur.html",
        libur_list=libur_list, tahun=tahun,
        bulan_nama=bulan_nama, tanggal_str=tanggal_str)


@app.route("/admin/hari_libur/tambah", methods=["POST"])
@admin_required
def admin_tambah_libur():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO hari_libur_salma (tanggal_libur_salma,keterangan_libur_salma) VALUES (%s,%s)",
            (request.form["tanggal"], request.form["keterangan"]))
        conn.commit()
        flash("Hari libur berhasil ditambahkan!", "success")
    except Exception:
        flash("Tanggal sudah ada atau terjadi kesalahan.", "error")
    cursor.close(); conn.close()
    return redirect(url_for("admin_hari_libur"))


@app.route("/admin/hari_libur/hapus/<int:id_libur>")
@admin_required
def admin_hapus_libur(id_libur):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hari_libur_salma WHERE id_libur_salma=%s", (id_libur,))
    conn.commit(); cursor.close(); conn.close()
    flash("Hari libur dihapus.", "success")
    return redirect(url_for("admin_hari_libur"))


# ============================================================
# KARYAWAN — RIWAYAT ABSENSI
# ============================================================
@app.route("/karyawan/absensi")
def karyawan_absensi():
    if "user_id" not in session:
        return redirect(url_for("index"))
    id_user = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    bulan = int(request.args.get("bulan", datetime.now().month))
    tahun = int(request.args.get("tahun", datetime.now().year))
    cursor.execute("""
        SELECT * FROM absensi_salma
        WHERE id_user_salma=%s AND MONTH(tanggal_absensi_salma)=%s AND YEAR(tanggal_absensi_salma)=%s
        ORDER BY tanggal_absensi_salma DESC
    """, (id_user, bulan, tahun))
    absensi_list = cursor.fetchall()
    hadir = sum(1 for a in absensi_list if a["status_absensi_salma"] == "hadir")
    izin  = sum(1 for a in absensi_list if a["status_absensi_salma"] == "izin")
    sakit = sum(1 for a in absensi_list if a["status_absensi_salma"] == "sakit")
    alpha = sum(1 for a in absensi_list if a["status_absensi_salma"] == "alpha")
    cursor.execute("""
        SELECT u.*, j.nama_jabatan_salma FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma=j.id_jabatan_salma
        WHERE u.id_user_salma=%s
    """, (id_user,))
    karyawan = cursor.fetchone()
    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    cursor.close(); conn.close()
    return render_template("Salma_Karyawan_Absensi.html",
        karyawan=karyawan, absensi_list=absensi_list, bulan=bulan, tahun=tahun,
        bulan_nama=bulan_nama, total_hadir=hadir, total_izin=izin,total_sakit=sakit, total_alpha=alpha)


@app.route("/lupa_password")
def lupa_password():
    return render_template("Salma_Lupa_Password.html")


# ============================================================
# RFID — ABSEN VIA KARTU
# ============================================================
@app.route('/rfid/absen', methods=['POST'])
def rfid_absen():
    try:
        print("🔥 RFID KE TRIGGER")
        data = request.get_json()
        print("DATA:", data)

        if not data or 'id_kartu' not in data:
            return jsonify({"status": "ERROR", "pesan": "ID kartu tidak ada"}), 400

        id_kartu = data['id_kartu']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id_user_salma, u.nama_salma, u.status_user_salma
            FROM rfid_kartu_salma k
            JOIN users_salma u ON k.id_user_salma = u.id_user_salma
            WHERE k.id_kartu = %s
        """, (id_kartu,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"status": "TIDAK_DIKENAL"})

        if user['status_user_salma'] != 'aktif':
            return jsonify({"status": "NONAKTIF", "nama": user['nama_salma']})

        id_user = user['id_user_salma']
        nama    = user['nama_salma']

        sekarang = datetime.now()
        tanggal  = sekarang.date()
        jam      = sekarang.time()

        cursor.execute("""
            SELECT * FROM absensi_salma
            WHERE id_user_salma=%s AND tanggal_absensi_salma=%s
        """, (id_user, tanggal))
        absen = cursor.fetchone()

        if not absen:
            cursor.execute("""
                INSERT INTO absensi_salma
                (id_user_salma, tanggal_absensi_salma, jam_masuk_salma, status_absensi_salma)
                VALUES (%s, %s, %s, 'hadir')
            """, (id_user, tanggal, jam))
            conn.commit()
            return jsonify({"status": "MASUK", "nama": nama, "jam": sekarang.strftime("%H:%M:%S")})

        elif absen['jam_pulang_salma'] is None:
            cursor.execute("""
                UPDATE absensi_salma SET jam_pulang_salma=%s
                WHERE id_user_salma=%s AND tanggal_absensi_salma=%s
            """, (jam, id_user, tanggal))
            conn.commit()
            return jsonify({"status": "PULANG", "nama": nama, "jam": sekarang.strftime("%H:%M:%S")})

        else:
            return jsonify({"status": "SUDAH_LENGKAP", "nama": nama})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"status": "ERROR", "pesan": str(e)}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


# ============================================================
# ADMIN — KELOLA KARTU RFID
# ============================================================
@app.route('/admin/rfid')
@admin_required
def admin_rfid():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT k.id_kartu, k.keterangan,
               u.id_user_salma, u.nama_salma, u.foto_profil_salma,
               j.nama_jabatan_salma
        FROM rfid_kartu_salma k
        JOIN users_salma u ON k.id_user_salma = u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        ORDER BY u.nama_salma
    """)
    kartu_list = cursor.fetchall()

    cursor.execute("""
        SELECT u.id_user_salma, u.nama_salma, j.nama_jabatan_salma
        FROM users_salma u
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.role_salma = 'karyawan' AND u.status_user_salma = 'aktif'
          AND u.id_user_salma NOT IN (SELECT id_user_salma FROM rfid_kartu_salma)
        ORDER BY u.nama_salma
    """)
    karyawan_belum_kartu = cursor.fetchall()

    cursor.execute("""
        SELECT u.id_user_salma, u.nama_salma
        FROM users_salma u
        WHERE u.role_salma = 'karyawan' AND u.status_user_salma = 'aktif'
        ORDER BY u.nama_salma
    """)
    semua_karyawan = cursor.fetchall()

    cursor.execute("""
        SELECT a.*, u.nama_salma, u.foto_profil_salma, j.nama_jabatan_salma
        FROM absensi_salma a
        JOIN users_salma u ON a.id_user_salma = u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE DATE(a.tanggal_absensi_salma) = CURDATE()
          AND u.id_user_salma IN (SELECT id_user_salma FROM rfid_kartu_salma)
        ORDER BY a.jam_masuk_salma DESC
    """)
    log_hari_ini = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as n FROM izin_salma WHERE status_izin_salma='pending'")
    notif_izin = cursor.fetchone()['n']

    cursor.execute("""
        SELECT COUNT(*) as n FROM gaji_salma
        WHERE bulan_gaji_salma=%s AND tahun_gaji_salma=%s AND status_gaji_salma='belum_dibayar'
    """, (datetime.now().month, datetime.now().year))
    notif_gaji = cursor.fetchone()['n']

    bulan_nama = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    hari_nama  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"

    cursor.close(); conn.close()
    return render_template(
        'Salma_Admin_RFID.html',
        kartu_list=kartu_list,
        karyawan_belum_kartu=karyawan_belum_kartu,
        semua_karyawan=semua_karyawan,
        log_hari_ini=log_hari_ini,
        tanggal_str=tanggal_str,
        notif_izin=notif_izin,
        notif_gaji=notif_gaji
    )


@app.route('/admin/rfid/daftar', methods=['POST'])
@admin_required
def admin_rfid_daftar():
    id_kartu   = request.form.get('id_kartu',   '').strip()
    id_user    = request.form.get('id_user',    '').strip()
    keterangan = request.form.get('keterangan', '').strip()

    if not id_kartu or not id_user:
        flash("ID kartu dan karyawan wajib diisi!", "error")
        return redirect(url_for('admin_rfid'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM rfid_kartu_salma WHERE id_user_salma=%s", (id_user,))
        cursor .execute("""
            INSERT INTO rfid_kartu_salma (id_kartu, id_user_salma, keterangan)
            VALUES (%s, %s, %s)
        """, (id_kartu, id_user, keterangan))
        conn.commit()
        flash("Kartu RFID berhasil didaftarkan!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal mendaftarkan kartu: {str(e)}", "error")
    cursor.close(); conn.close()
    return redirect(url_for('admin_rfid'))


@app.route('/admin/rfid/hapus/<id_kartu>')
@admin_required
def admin_rfid_hapus(id_kartu):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM rfid_kartu_salma WHERE id_kartu=%s", (id_kartu,))
        conn.commit()
        flash("Kartu RFID berhasil dihapus.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Gagal hapus kartu: {str(e)}", "error")
    cursor.close(); conn.close()
    return redirect(url_for('admin_rfid'))


# ============================================================
# HALAMAN HUBUNGI ADMIN 
# ============================================================
@app.route("/karyawan/hubungi_admin")
def hubungi_admin():
    return render_template("Salma_Hubungi_Admin.html")


# ============================================================
# KIRIM REQUEST 
# ============================================================
@app.route("/karyawan/kirim_request", methods=["POST"])
def kirim_request():
    nama                = request.form.get("nama", "").strip()
    jabatan             = request.form.get("jabatan", "").strip()
    jenis               = request.form.get("jenis", "belum_akun")
    username_akun       = request.form.get("username", "").strip() or None
    pesan_tambahan      = request.form.get("pesan_tambahan", "").strip() or None
    nama_bank           = request.form.get("nama_bank", "").strip() or None        
    no_rekening         = request.form.get("no_rekening", "").strip() or None      
    atas_nama_rekening  = request.form.get("atas_nama_rekening", "").strip() or None  

    if not nama or not jabatan:
        flash("Nama dan jabatan wajib diisi!", "error")
        return redirect(url_for("hubungi_admin"))

    kode = generate_kode_tiket()
    conn   = get_db_connection()
    cursor = conn.cursor()

    while True:
        cursor.execute("SELECT id_request FROM request_admin_salma WHERE kode_tiket=%s", (kode,))
        if not cursor.fetchone():
            break
        kode = generate_kode_tiket()

    try:
        cursor.execute("""
            INSERT INTO request_admin_salma
                (kode_tiket, nama, jabatan, jenis_request, username_akun,
                 pesan_tambahan, status_request,
                 nama_bank, no_rekening, atas_nama_rekening)
            VALUES (%s, %s, %s, %s, %s, %s, 'menunggu', %s, %s, %s)
        """, (kode, nama, jabatan, jenis, username_akun,
              pesan_tambahan, nama_bank, no_rekening, atas_nama_rekening))
        conn.commit()
        flash(
            f"Permintaan berhasil dikirim! Kode tiket kamu: {kode} — simpan kode ini untuk cek status.",
            "success"
        )
    except Exception as e:
        conn.rollback()
        flash(f"Gagal mengirim permintaan: {str(e)}", "error")

    cursor.close()
    conn.close()
    return redirect(url_for("hubungi_admin"))

@app.route("/admin/cetak_semua_gaji_pdf")
@admin_required
def cetak_semua_gaji_pdf_route():
    """Cetak PDF semua data penggajian seluruh karyawan."""
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    # ── Ambil filter rentang (opsional, default semua data) ──────────────────
    dari   = request.args.get("dari",   "")
    sampai = request.args.get("sampai", "")
 
    query = """
        SELECT g.*, u.nama_salma, u.nip_salma,
               j.nama_jabatan_salma
        FROM gaji_salma g
        JOIN users_salma u ON g.id_user_salma = u.id_user_salma
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
    """
    params = []
    if dari and sampai:
        query += """
            WHERE STR_TO_DATE(CONCAT(g.tahun_gaji_salma,'-',
                  LPAD(g.bulan_gaji_salma,2,'0'),'-01'),'%%Y-%%m-%%d')
                  BETWEEN %s AND %s
        """
        params = [dari, sampai]
 
    query += " ORDER BY g.tahun_gaji_salma DESC, g.bulan_gaji_salma DESC, u.nama_salma"
    cursor.execute(query, params)
    gaji_list = cursor.fetchall()
 
    # ── Ambil nama admin yang sedang login ───────────────────────────────────
    cursor.execute("SELECT nama_salma FROM users_salma WHERE id_user_salma=%s",
                   (session["user_id"],))
    row       = cursor.fetchone()
    nama_admin = row["nama_salma"] if row else "Admin"
 
    cursor.close(); conn.close()
 
    # ── Generate PDF ─────────────────────────────────────────────────────────
    pdf_bytes = cetak_semua_gaji_pdf(gaji_list, nama_admin, dari, sampai)
 
    from io import BytesIO
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False,
        download_name="Rekap_Gaji_Semua.pdf"
    )
 
# ============================================================
# CEK STATUS TIKET (tanpa login)
# ============================================================
@app.route("/cek_status_request")
def cek_status_request():
    kode         = request.args.get("kode", "").strip().upper()
    request_data = None
 
    if kode:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM request_admin_salma WHERE kode_tiket=%s",
            (kode,)
        )
        request_data = cursor.fetchone()
        cursor.close()
        conn.close()
 
    return render_template(
        "Salma_Cek_Status_Request.html",
        kode=kode,
        request_data=request_data
    )
 
 
# ============================================================
# ADMIN — HALAMAN KELOLA REQUEST
# ============================================================
@app.route("/admin/request")
@admin_required
def admin_request():
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    status_filter = request.args.get("status", "menunggu")
 
    # Query list
    if status_filter == "semua":
        cursor.execute("""
            SELECT * FROM request_admin_salma
            ORDER BY
                FIELD(status_request,'menunggu','dibuka','diproses','selesai'),
                created_at DESC
        """)
    else:
        cursor.execute("""
            SELECT * FROM request_admin_salma
            WHERE status_request = %s
            ORDER BY created_at DESC
        """, (status_filter,))
    request_list = cursor.fetchall()
 
    # Stats per status
    cursor.execute("""
        SELECT status_request, COUNT(*) as n
        FROM request_admin_salma
        GROUP BY status_request
    """)
    stats_raw = {r["status_request"]: r["n"] for r in cursor.fetchall()}
    stats = {
        "menunggu": stats_raw.get("menunggu", 0),
        "dibuka":   stats_raw.get("dibuka",   0),
        "diproses": stats_raw.get("diproses", 0),
        "selesai":  stats_raw.get("selesai",  0),
    }
    menunggu_count = stats["menunggu"]
 
    # Notif izin untuk sidebar
    cursor.execute("SELECT COUNT(*) as n FROM izin_salma WHERE status_izin_salma='pending'")
    pending_izin = cursor.fetchone()["n"]
 
    # Tanggal
    bulan_nama = ['','Januari','Februari','Maret','April','Mei','Juni',
                  'Juli','Agustus','September','Oktober','November','Desember']
    hari_nama  = ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
 
    cursor.close()
    conn.close()
 
    return render_template(
        "Salma_Admin_Request.html",
        request_list=request_list,
        status_filter=status_filter,
        stats=stats,
        menunggu_count=menunggu_count,
        pending_izin=pending_izin,
        tanggal_str=tanggal_str
    )
 
 
# ============================================================
# ADMIN — UPDATE STATUS REQUEST
# ============================================================
@app.route("/admin/request/update", methods=["POST"])
@admin_required
def admin_update_request():
    id_request      = request.form.get("id_request")
    status_baru     = request.form.get("status_request", "menunggu")
    catatan_admin   = request.form.get("catatan_admin", "").strip() or None
    redirect_status = request.form.get("redirect_status", "menunggu")
 
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        UPDATE request_admin_salma
        SET status_request  = %s,
            catatan_admin   = COALESCE(%s, catatan_admin),
            updated_at      = NOW()
        WHERE id_request = %s
    """, (status_baru, catatan_admin, id_request))
    conn.commit()
 
    cursor.close()
    conn.close()
 
    label = {
        "menunggu": "Menunggu",
        "dibuka":   "Dibuka",
        "diproses": "Diproses",
        "selesai":  "Selesai",
    }.get(status_baru, status_baru)
 
    flash(f"Status permintaan berhasil diubah menjadi '{label}'.", "success")
    return redirect(url_for("admin_request", status=redirect_status))
 
 
# ============================================================
# ROUTE TAMBAHAN — CETAK SEMUA ABSENSI (PDF via fpdf2)
# ============================================================
@app.route("/admin/cetak_semua_absensi_pdf")
@admin_required
def cetak_semua_absensi_pdf_route():
    """Cetak PDF rekap absensi semua karyawan, bisa difilter rentang tanggal."""
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    now            = datetime.now()
    default_dari   = now.replace(day=1).strftime("%Y-%m-%d")
    default_sampai = now.strftime("%Y-%m-%d")
 
    dari   = request.args.get("dari",   default_dari)
    sampai = request.args.get("sampai", default_sampai)
 
    cursor.execute("""
        SELECT
            u.id_user_salma, u.nama_salma, u.nip_salma, u.foto_profil_salma,
            j.nama_jabatan_salma,
            SUM(CASE WHEN a.status_absensi_salma = 'hadir'           THEN 1 ELSE 0 END) AS hadir,
            SUM(CASE WHEN a.status_absensi_salma = ('izin')          THEN 1 ELSE 0 END) AS izin,
            SUM(CASE WHEN a.status_absensi_salma = ('sakit')         THEN 1 ELSE 0 END) AS sakit,
            SUM(CASE WHEN a.status_absensi_salma = 'alpha'           THEN 1 ELSE 0 END) AS alpha,
            COUNT(a.id_absensi_salma) AS total
        FROM users_salma u
        LEFT JOIN absensi_salma a
            ON u.id_user_salma = a.id_user_salma
            AND a.tanggal_absensi_salma BETWEEN %s AND %s
        LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
        WHERE u.role_salma = 'karyawan'
        GROUP BY u.id_user_salma, u.nama_salma, u.nip_salma,
                 u.foto_profil_salma, j.nama_jabatan_salma
        ORDER BY u.nama_salma
    """, (dari, sampai))
    rekap_list = cursor.fetchall()
 
    # ── Nama admin ───────────────────────────────────────────────────────────
    cursor.execute("SELECT nama_salma FROM users_salma WHERE id_user_salma=%s",
                   (session["user_id"],))
    row        = cursor.fetchone()
    nama_admin = row["nama_salma"] if row else "Admin"
 
    cursor.close(); conn.close()
 
    # ── Generate PDF ─────────────────────────────────────────────────────────
    pdf_bytes = cetak_semua_absensi_pdf(rekap_list, dari, sampai, nama_admin)
 
    from io import BytesIO
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"Rekap_Absensi_{dari}_{sampai}.pdf"
    )
 

# ============================================================
# AUTO ALPHA — APScheduler
# ============================================================
def job_auto_alpha():
    """Dijalankan otomatis setiap hari jam 09:00"""
    with app.app_context():
        today = datetime.now().date()
        conn   = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT u.id_user_salma FROM users_salma u
                WHERE u.role_salma = 'karyawan'
                  AND u.status_user_salma = 'aktif'
                  AND u.id_user_salma NOT IN (
                      SELECT id_user_salma FROM absensi_salma
                      WHERE tanggal_absensi_salma = %s
                  )
                  AND u.id_user_salma NOT IN (
                      SELECT id_user_salma FROM izin_salma
                      WHERE status_izin_salma = 'disetujui'
                        AND %s BETWEEN tanggal_mulai_salma AND tanggal_selesai_salma
                  )
            """, (today, today))
            belum_absen = cursor.fetchall()

            jumlah = 0
            for row in belum_absen:
                cursor.execute("""
                    INSERT INTO absensi_salma
                        (id_user_salma, tanggal_absensi_salma, status_absensi_salma)
                    VALUES (%s, %s, 'alpha')
                """, (row["id_user_salma"], today))
                jumlah += 1

            conn.commit()
            print(f"[AUTO ALPHA] {datetime.now()} — {jumlah} karyawan ditandai alpha.")

        except Exception as e:
            conn.rollback()
            print(f"[AUTO ALPHA] ERROR: {e}")

        finally:
            cursor.close()
            conn.close()


# ── Start scheduler ──────────────────────────────────────────
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=job_auto_alpha,
    trigger=CronTrigger(hour=10, minute=10),  
    id="auto_alpha",
    name="Auto Alpha Karyawan",
    replace_existing=True
)
scheduler.start()


atexit.register(lambda: scheduler.shutdown())

@app.route("/admin/surat_peringatan")
@admin_required
def admin_surat_peringatan():
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    status_filter = request.args.get("status", "menunggu_admin")
 
    if status_filter == "semua":
        cursor.execute("""
            SELECT sp.*, u.nama_salma, u.nip_salma, u.foto_profil_salma,
                   j.nama_jabatan_salma
            FROM surat_peringatan_salma sp
            JOIN users_salma u ON sp.id_user_salma = u.id_user_salma
            LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
            ORDER BY sp.created_at DESC
        """)
    else:
        cursor.execute("""
            SELECT sp.*, u.nama_salma, u.nip_salma, u.foto_profil_salma,
                   j.nama_jabatan_salma
            FROM surat_peringatan_salma sp
            JOIN users_salma u ON sp.id_user_salma = u.id_user_salma
            LEFT JOIN jabatan_salma j ON u.id_jabatan_salma = j.id_jabatan_salma
            WHERE sp.status_sp = %s
            ORDER BY sp.created_at DESC
        """, (status_filter,))
    sp_list = cursor.fetchall()
 
    # Stats per status untuk badge/tab
    cursor.execute("""
        SELECT status_sp, COUNT(*) as n
        FROM surat_peringatan_salma
        GROUP BY status_sp
    """)
    stats_raw = {r["status_sp"]: r["n"] for r in cursor.fetchall()}
    stats = {
        "menunggu_admin" : stats_raw.get("menunggu_admin",  0),
        "dikirim"        : stats_raw.get("dikirim",         0),
        "direspon"       : stats_raw.get("direspon",        0),
        "tidak_direspon" : stats_raw.get("tidak_direspon",  0),
    }
 
    # Notif sidebar
    cursor.execute("SELECT COUNT(*) as n FROM izin_salma WHERE status_izin_salma='pending'")
    notif_izin = cursor.fetchone()["n"]
 
    cursor.execute("""
        SELECT COUNT(*) as n FROM gaji_salma
        WHERE bulan_gaji_salma=%s AND tahun_gaji_salma=%s
          AND status_gaji_salma='belum_dibayar'
    """, (datetime.now().month, datetime.now().year))
    notif_gaji = cursor.fetchone()["n"]
 
    bulan_nama = ['','Januari','Februari','Maret','April','Mei','Juni',
                  'Juli','Agustus','September','Oktober','November','Desember']
    hari_nama  = ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu']
    now = datetime.now()
    tanggal_str = f"{hari_nama[now.weekday()]}, {now.day} {bulan_nama[now.month]} {now.year}"
 
    cursor.close(); conn.close()
    return render_template(
        "Salma_Admin_Surat_Peringatan.html",
        sp_list=sp_list,
        status_filter=status_filter,
        stats=stats,
        notif_izin=notif_izin,
        notif_gaji=notif_gaji,
        tanggal_str=tanggal_str
    )
 
@app.route("/admin/sp/kirim/<int:id_sp>", methods=["POST"])
@admin_required
def admin_kirim_sp(id_sp):
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT sp.*, u.nama_salma
        FROM surat_peringatan_salma sp
        JOIN users_salma u ON sp.id_user_salma = u.id_user_salma
        WHERE sp.id_sp = %s
    """, (id_sp,))
    sp = cursor.fetchone()
 
    if not sp:
        flash("Data SP tidak ditemukan.", "error")
        cursor.close(); conn.close()
        return redirect(url_for("admin_surat_peringatan"))
 
    if sp["status_sp"] != "menunggu_admin":
        flash("SP ini sudah pernah dikirim.", "error")
        cursor.close(); conn.close()
        return redirect(url_for("admin_surat_peringatan"))
 
    cursor.execute("""
        UPDATE surat_peringatan_salma
        SET status_sp = 'dikirim', dikirim_at = NOW()
        WHERE id_sp = %s
    """, (id_sp,))
    conn.commit()
 
    flash(f"SP{sp['level_sp']} untuk {sp['nama_salma']} berhasil dikirim!", "success")
    cursor.close(); conn.close()
    return redirect(url_for("admin_surat_peringatan"))
 
@app.route("/admin/sp/tidak_direspon/<int:id_sp>", methods=["POST"])
@admin_required
def admin_sp_tidak_direspon(id_sp):
    """
    Admin manual menandai SP3 sudah melewati batas waktu
    dan karyawan tidak merespon.
    """
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT sp.*, u.nama_salma
        FROM surat_peringatan_salma sp
        JOIN users_salma u ON sp.id_user_salma = u.id_user_salma
        WHERE sp.id_sp = %s
    """, (id_sp,))
    sp = cursor.fetchone()
 
    if not sp:
        flash("Data SP tidak ditemukan.", "error")
        cursor.close(); conn.close()
        return redirect(url_for("admin_surat_peringatan"))
 
    if sp["level_sp"] != 3:
        flash("Fitur ini hanya untuk SP3.", "error")
        cursor.close(); conn.close()
        return redirect(url_for("admin_surat_peringatan"))
 
    cursor.execute("""
        UPDATE surat_peringatan_salma
        SET status_sp = 'tidak_direspon'
        WHERE id_sp = %s
    """, (id_sp,))
    conn.commit()
 
    flash(
        f"SP3 {sp['nama_salma']} ditandai tidak direspon. "
        f"Kamu bisa nonaktifkan karyawan ini sekarang.",
        "warning"
    )
    cursor.close(); conn.close()
    return redirect(url_for("admin_surat_peringatan"))

@app.route("/admin/sp/nonaktifkan/<id_user>", methods=["POST"])
@admin_required
def admin_sp_nonaktifkan(id_user):
    """
    Nonaktifkan karyawan yang tidak merespon SP3.
    Dipanggil dari halaman surat_peringatan.
    """
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    # Validasi: pastikan memang ada SP3 tidak_direspon
    cursor.execute("""
        SELECT sp.id_sp, u.nama_salma
        FROM surat_peringatan_salma sp
        JOIN users_salma u ON sp.id_user_salma = u.id_user_salma
        WHERE sp.id_user_salma = %s
          AND sp.level_sp = 3
          AND sp.status_sp = 'tidak_direspon'
        LIMIT 1
    """, (id_user,))
    row = cursor.fetchone()
 
    if not row:
        flash("Tidak ada SP3 tidak direspon untuk karyawan ini.", "error")
        cursor.close(); conn.close()
        return redirect(url_for("admin_surat_peringatan"))
 
    cursor.execute("""
        UPDATE users_salma SET status_user_salma = 'nonaktif'
        WHERE id_user_salma = %s
    """, (id_user,))
    conn.commit()
 
    flash(f"{row['nama_salma']} berhasil dinonaktifkan.", "success")
    cursor.close(); conn.close()
    return redirect(url_for("admin_surat_peringatan"))

@app.route("/karyawan/sp/respon/<int:id_sp>", methods=["POST"])
def karyawan_respon_sp(id_sp):
    if "user_id" not in session:
        return redirect(url_for("index"))
 
    id_user = session["user_id"]
    conn    = get_db_connection()
    cursor  = conn.cursor()
 
    cursor.execute("""
        SELECT * FROM surat_peringatan_salma
        WHERE id_sp = %s AND id_user_salma = %s
          AND level_sp = 3 AND status_sp = 'dikirim'
    """, (id_sp, id_user))
    sp = cursor.fetchone()
 
    if not sp:
        flash("SP tidak ditemukan atau tidak bisa direspon.", "error")
        cursor.close(); conn.close()
        return redirect(url_for("karyawan_dashboard"))
 
    foto_filename = None
    foto = request.files.get("foto_bukti_sp")
    if foto and foto.filename:
        ext = foto.filename.rsplit(".", 1)[-1].lower() if "." in foto.filename else ""
        if ext in {"jpg", "jpeg", "png", "pdf"}:
            ts            = datetime.now().strftime("%Y%m%d%H%M%S")
            foto_filename = f"sp3_{id_user}_{ts}.{ext}"
            foto.save(os.path.join(UPLOAD_FOLDER_SP, foto_filename))
        else:
            flash("Format file tidak didukung. Gunakan JPG, PNG, atau PDF.", "error")
            cursor.close(); conn.close()
            return redirect(url_for("karyawan_dashboard"))
    else:
        flash("Foto bukti wajib diunggah untuk merespon SP3.", "error")
        cursor.close(); conn.close()
        return redirect(url_for("karyawan_dashboard"))
 
    cursor.execute("""
        UPDATE surat_peringatan_salma
        SET status_sp      = 'direspon',
            foto_bukti_sp  = %s,
            tanggal_respon = NOW()
        WHERE id_sp = %s
    """, (foto_filename, id_sp))
    conn.commit()
 
    flash("Respon SP3 berhasil dikirim. Admin akan menindaklanjuti.", "success")
    cursor.close(); conn.close()
    return redirect(url_for("karyawan_dashboard"))

@app.route("/uploads/sp/<filename>")
def serve_foto_sp(filename):
    if "user_id" not in session:
        return redirect(url_for("index"))
    return send_from_directory(UPLOAD_FOLDER_SP, filename)

# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_user"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)