from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
   SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
   HRFlowable, KeepTogether
)

# ── Warna (hitam putih / grayscale) ───────────────────────────────────────────
BLACK        = colors.HexColor("#1E293B")
WHITE        = colors.white
GRAY_HDR     = colors.HexColor("#F1F5F9")
GRAY_LINE    = colors.HexColor("#CCCCCC")
GRAY_TEXT    = colors.HexColor("#64748B")
GRAY_DARK    = colors.HexColor("#333333")
GRAY_LIGHT   = colors.HexColor("#F5F5F5")
GRAY_MED     = colors.HexColor("#999999")
GRAY_BORDER  = colors.HexColor("#AAAAAA")
GRAY_BG_ROW  = colors.HexColor("#F8F8F8")

BULAN_NAMA = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

W_PAGE, H_PAGE = A4
MARGIN_L = 1.8 * cm
MARGIN_R = 1.8 * cm
MARGIN_T = 1.5 * cm
MARGIN_B = 2.0 * cm
CONTENT_W = W_PAGE - MARGIN_L - MARGIN_R


def fmt_rp(value):
   try:
       n = float(value or 0)
       return f"Rp {n:,.0f}".replace(",", ".")
   except Exception:
       return "Rp 0"


def fmt_date(d):
   try:
       return datetime.strptime(d, "%Y-%m-%d").strftime("%d %B %Y")
   except Exception:
       return str(d)


# ── Styles ─────────────────────────────────────────────────────────────────────
def S(name, **kw):
   defaults = dict(fontName="Helvetica", fontSize=9, textColor=BLACK,
                   leading=13, spaceAfter=0, spaceBefore=0)
   defaults.update(kw)
   return ParagraphStyle(name, **defaults)


STYLES = {
   "doc_title":    S("doc_title",   fontSize=15, fontName="Helvetica-Bold",
                      textColor=BLACK, alignment=TA_CENTER, leading=20, spaceAfter=2),
   "doc_sub":      S("doc_sub",     fontSize=9,  textColor=GRAY_TEXT, alignment=TA_CENTER),
   "doc_period":   S("doc_period",  fontSize=9,  textColor=GRAY_TEXT, alignment=TA_CENTER),
   "footer":       S("footer",      fontSize=7.5, textColor=GRAY_TEXT, alignment=TA_CENTER),
   "sec_hdr":      S("sec_hdr",     fontSize=9, fontName="Helvetica-Bold", textColor=BLACK),
   "item":         S("item",        fontSize=9, textColor=BLACK),
   "bullet":       S("bullet",      fontSize=9, textColor=BLACK, leftIndent=12),
   "val_rp":       S("val_rp",      fontSize=8, textColor=GRAY_TEXT, alignment=TA_CENTER),
   "val_num":      S("val_num",     fontSize=9, textColor=BLACK, alignment=TA_RIGHT),
   "val_num_bold": S("val_num_bold",fontSize=9, fontName="Helvetica-Bold", textColor=BLACK, alignment=TA_RIGHT),
   "val_total":    S("val_total",   fontSize=9, fontName="Helvetica-Bold", textColor=BLACK, alignment=TA_RIGHT),
   "total_label":  S("total_label", fontSize=9, fontName="Helvetica-Bold", textColor=BLACK),
   "grand_label":  S("grand_label", fontSize=10, fontName="Helvetica-Bold", textColor=BLACK),
   "paid":         S("paid",        fontSize=8, fontName="Helvetica-Bold",
                      textColor=GRAY_DARK, alignment=TA_CENTER),
   "unpaid":       S("unpaid",      fontSize=8, fontName="Helvetica-Bold",
                      textColor=GRAY_TEXT, alignment=TA_CENTER),
   "hadir_s":      S("hadir_s",     fontSize=9, fontName="Helvetica-Bold",
                      textColor=GRAY_DARK, alignment=TA_CENTER),
   "alpha_s":      S("alpha_s",     fontSize=9, fontName="Helvetica-Bold",
                      textColor=GRAY_TEXT, alignment=TA_CENTER),
   "center":       S("center",      fontSize=9, alignment=TA_CENTER),
   "bold":         S("bold",        fontSize=9, fontName="Helvetica-Bold"),
   "small_gray":   S("small_gray",  fontSize=7, textColor=GRAY_TEXT, alignment=TA_CENTER),
   "th":           S("th", fontSize=8, fontName="Helvetica-Bold",
                      textColor=WHITE, alignment=TA_CENTER, leading=11),
   "th_left":      S("th_left", fontSize=8, fontName="Helvetica-Bold",
                      textColor=WHITE, alignment=TA_LEFT, leading=11),
}


# ── Kop perusahaan ────────────────────────────────────────────────────────────
PERUSAHAAN = {
   "nama":    "PT. SALMA ABADI SEJAHTERA",
   "alamat":  "Jl. Merdeka No. 123, Jakarta Pusat, DKI Jakarta 10110",
   "telp":    "(021) 1234-5678",
   "email":   "info@salmaabadi.co.id",
   "website": "www.salmaabadi.co.id",
}


def _kop_perusahaan():
   story = []
   kop_inner = [
       [Paragraph(PERUSAHAAN["nama"],
                  S("kop_nama", fontSize=14, fontName="Helvetica-Bold",
                    textColor=BLACK, alignment=TA_CENTER, leading=18))],
       [Paragraph(PERUSAHAAN["alamat"],
                  S("kop_alamat", fontSize=8, textColor=GRAY_TEXT,
                    alignment=TA_CENTER, leading=11))],
       [Paragraph(
           f"Telp: {PERUSAHAAN['telp']}  •  Email: {PERUSAHAAN['email']}  •  {PERUSAHAAN['website']}",
           S("kop_kontak", fontSize=8, textColor=GRAY_TEXT,
             alignment=TA_CENTER, leading=11)
       )],
   ]
   kop_tbl = Table(kop_inner, colWidths=[CONTENT_W])
   kop_tbl.setStyle(TableStyle([
       ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
       ("TOPPADDING",    (0, 0), (-1, -1), 10),
       ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
       ("BOTTOMPADDING", (0, 0), (-1, -2), 3),
       ("TOPPADDING",    (0, 1), (-1, -1), 3),
       ("LEFTPADDING",   (0, 0), (-1, -1), 16),
       ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
       ("BOX",           (0, 0), (-1, -1), 1, GRAY_BORDER),
   ]))
   story.append(kop_tbl)
   story.append(Spacer(1, 14))
   return story


# ── Header dokumen ──────────────────────────────────────────────────────────────
def _doc_header(title, badge_text, periode, kota="Jakarta", tgl_cetak=""):
   story = []
   story += _kop_perusahaan()
   story.append(HRFlowable(width=CONTENT_W, thickness=1.5, color=GRAY_BORDER))
   story.append(Spacer(1, 12))

   # Judul
   story.append(Paragraph(title, STYLES["doc_title"]))
   story.append(Spacer(1, 6))

   # Pill badge
   pill = Table(
       [[Paragraph(badge_text, S("pill_txt", fontSize=9, fontName="Helvetica-Bold",
                               textColor=BLACK, alignment=TA_CENTER))]],
       colWidths=[5 * cm]
   )
   pill.setStyle(TableStyle([
       ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
       ("BOX",           (0, 0), (-1, -1), 0.8, GRAY_BORDER),
       ("TOPPADDING",    (0, 0), (-1, -1), 5),
       ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
       ("LEFTPADDING",   (0, 0), (-1, -1), 12),
       ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
   ]))
   pill_row = Table([[pill]], colWidths=[CONTENT_W])
   pill_row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
   story.append(pill_row)
   story.append(Spacer(1, 6))

   # ── PERUBAHAN: tampilkan periode saja, hapus kota + tanggal cetak ──
   story.append(Paragraph(
       f"Periode: <b>{periode}</b>",
       S("doc_periode_filter", fontSize=9, textColor=GRAY_TEXT, alignment=TA_CENTER)
   ))

   story.append(Spacer(1, 16))
   story.append(HRFlowable(width=CONTENT_W, thickness=0.8, color=GRAY_LINE))
   story.append(Spacer(1, 14))
   return story


# ── Footer ─────────────────────────────────────────────────────────────────────
def _doc_footer(nama_admin, tgl_cetak, extra=""):
   story = []
   story.append(Spacer(1, 18))
   story.append(HRFlowable(width=CONTENT_W, thickness=0.5, color=GRAY_LINE))
   story.append(Spacer(1, 6))
   footer_txt = "Dokumen digenerate otomatis oleh SistemGaji"
   if extra:
       footer_txt += f"  •  {extra}"
   footer_txt += f"  •  Dicetak: <b>{tgl_cetak}</b>  •  Oleh: <b>{nama_admin}</b>"
   story.append(Paragraph(footer_txt, STYLES["footer"]))
   return story


# ── Tanda Tangan ──────────────────────────────────────────────────────────────
# PERUBAHAN: urutan kolom → Direktur | Supervisor | Admin
def _tanda_tangan(nama_admin: str, nama_supervisor: str = "", nama_direktur: str = "", kota: str = "Jakarta"):
    story = []
    now = datetime.now()
    tgl_str = now.strftime("%d %B %Y")

    story.append(Spacer(1, 28))
    story.append(HRFlowable(width=CONTENT_W, thickness=0.5, color=GRAY_LINE))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f"{kota}, {tgl_str}",
        S("ttd_kota", fontSize=9, textColor=GRAY_TEXT, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Mengetahui,",
        S("ttd_mengetahui", fontSize=9, textColor=GRAY_TEXT, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 4))

    COL = CONTENT_W / 3

    # ── Judul jabatan: Direktur | Supervisor | Admin ──
    header_row = Table(
        [[
            Paragraph("Direktur",   S("ttd_h1", fontSize=9, textColor=GRAY_TEXT, alignment=TA_CENTER)),
            Paragraph("Supervisor", S("ttd_h2", fontSize=9, textColor=GRAY_TEXT, alignment=TA_CENTER)),
            Paragraph("Admin",      S("ttd_h3", fontSize=9, textColor=GRAY_TEXT, alignment=TA_CENTER)),
        ]],
        colWidths=[COL, COL, COL]
    )
    header_row.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(header_row)

    # ── Ruang tanda tangan ──
    story.append(Spacer(1, 50))

    # ── Garis tanda tangan ──
    LINE_W = COL * 0.6
    line_row = Table(
        [[
            HRFlowable(width=LINE_W, thickness=0.8, color=BLACK),
            HRFlowable(width=LINE_W, thickness=0.8, color=BLACK),
            HRFlowable(width=LINE_W, thickness=0.8, color=BLACK),
        ]],
        colWidths=[COL, COL, COL]
    )
    line_row.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(line_row)

    direktur_label   = f"<b>{nama_direktur}</b>"   if nama_direktur   else "<b>( _________________ )</b>"
    supervisor_label = f"<b>{nama_supervisor}</b>"  if nama_supervisor  else "<b>( _________________ )</b>"
    admin_label      = f"<b>{nama_admin}</b>"

    # ── Nama: Direktur | Supervisor | Admin ──
    nama_row = Table(
        [[
            Paragraph(direktur_label,   S("ttd_nama1", fontSize=9, alignment=TA_CENTER)),
            Paragraph(supervisor_label, S("ttd_nama2", fontSize=9, alignment=TA_CENTER)),
            Paragraph(admin_label,      S("ttd_nama3", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        ]],
        colWidths=[COL, COL, COL]
    )
    nama_row.setStyle(TableStyle([
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(nama_row)

    return story


# ─────────────────────────────────────────────────────────────────────────────
# 1. CETAK SEMUA GAJI PDF
# ─────────────────────────────────────────────────────────────────────────────
def cetak_semua_gaji_pdf(
    gaji_list: list,
    nama_admin: str,
    dari: str = "dari",
    sampai: str = "sampai",
    nama_supervisor: str = "",
    nama_direktur: str = "",
    kota: str = "Jakarta",
) -> bytes:
   buf = BytesIO()
   doc = SimpleDocTemplate(
       buf, pagesize=A4,
       rightMargin=MARGIN_R, leftMargin=MARGIN_L,
       topMargin=MARGIN_T, bottomMargin=MARGIN_B,
   )

   now = datetime.now()
   tgl_cetak = now.strftime("%d %B %Y")

   if dari and sampai:
       periode_str = f"{fmt_date(dari)} – {fmt_date(sampai)}"
   else:
       periode_str = tgl_cetak

   story = []
   story += _doc_header(
       "LAPORAN PENGGAJIAN KARYAWAN",
       "Detail Penggajian",
       periode_str,
       kota=kota,
       tgl_cetak=tgl_cetak,
   )

   # ── Tabel data gaji ──
   cw = [0.7*cm, 3.0*cm, 2.3*cm, 1.5*cm, 2.4*cm, 2.0*cm, 1.9*cm, 2.2*cm, 1.7*cm]

   rows = [[
       Paragraph("No",       STYLES["th"]),
       Paragraph("Nama",     STYLES["th_left"]),
       Paragraph("Jabatan",  STYLES["th_left"]),
       Paragraph("Bln/Thn", STYLES["th"]),
       Paragraph("Gaji Pokok", STYLES["th"]),
       Paragraph("Bonus",    STYLES["th"]),
       Paragraph("Potongan", STYLES["th"]),
       Paragraph("Total",    STYLES["th"]),
       Paragraph("Status",   STYLES["th"]),
   ]]

   for idx, g in enumerate(gaji_list):
       bulan_i = int(g.get("bulan_gaji_salma", 1) or 1)
       bln_str = f"{BULAN_NAMA[bulan_i][:3]}\n{g.get('tahun_gaji_salma', '')}"

       status = g.get("status_gaji_salma", "")
       if status == "sudah_dibayar":
           st_cell = Table(
               [[Paragraph("Lunas", S("sp", fontSize=7.5, fontName="Helvetica-Bold",
                                        textColor=BLACK, alignment=TA_CENTER))]],
               colWidths=[1.5*cm]
           )
           st_cell.setStyle(TableStyle([
               ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
               ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_BORDER),
               ("TOPPADDING",    (0, 0), (-1, -1), 3),
               ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
           ]))
       else:
           st_cell = Table(
               [[Paragraph("o Belum", S("su", fontSize=7.5, fontName="Helvetica-Bold",
                                         textColor=GRAY_TEXT, alignment=TA_CENTER))]],
               colWidths=[1.5*cm]
           )
           st_cell.setStyle(TableStyle([
               ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG_ROW),
               ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_MED),
               ("TOPPADDING",    (0, 0), (-1, -1), 3),
               ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
           ]))

       rows.append([
           Paragraph(str(idx + 1),
                     S("rno", fontSize=8.5, fontName="Helvetica-Bold",
                       alignment=TA_CENTER, textColor=GRAY_TEXT)),
           Paragraph(g.get("nama_salma", "-"),
                     S("rn", fontSize=8.5, fontName="Helvetica-Bold", textColor=BLACK)),
           Paragraph(g.get("nama_jabatan_salma", "-"),
                     S("rj", fontSize=7.5, textColor=GRAY_TEXT)),
           Paragraph(bln_str,
                     S("rb", fontSize=7.5, alignment=TA_CENTER, textColor=GRAY_TEXT)),
           Paragraph(fmt_rp(g.get("gaji_pokok_salma")),
                     S("rg", fontSize=7.5, alignment=TA_RIGHT, textColor=BLACK)),
           Paragraph(fmt_rp(g.get("bonus_salma")),
                     S("rbo", fontSize=7.5, alignment=TA_RIGHT, textColor=GRAY_DARK)),
           Paragraph(fmt_rp(g.get("potongan_salma")),
                     S("rp",   fontSize=7.5, alignment=TA_RIGHT, textColor=GRAY_TEXT)),
           Paragraph(fmt_rp(g.get("total_gaji_salma")),
                     S("rt", fontSize=7.5, fontName="Helvetica-Bold", alignment=TA_RIGHT,
                       textColor=BLACK)),
           st_cell,
       ])

   tbl = Table(rows, colWidths=cw, repeatRows=1)
   tbl.setStyle(TableStyle([
       ("BACKGROUND",    (0, 0), (-1, 0),  GRAY_DARK),
       ("LINEBELOW",     (0, 0), (-1, 0),  1, BLACK),
       ("TOPPADDING",    (0, 0), (-1, 0),  8),
       ("BOTTOMPADDING", (0, 0), (-1, 0),  8),
       ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_BG_ROW]),
       ("TOPPADDING",    (0, 1), (-1, -1), 7),
       ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
       ("LEFTPADDING",   (0, 0), (-1, -1), 7),
       ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
       ("GRID",          (0, 1), (-1, -1), 0.3, GRAY_LINE),
       ("LINEBELOW",     (0, 0), (-1, -2), 0.3, GRAY_LINE),
       ("BOX",           (0, 0), (-1, -1), 0.8, GRAY_BORDER),
       ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
       ("ALIGN",         (8, 1), (8, -1),  "CENTER"),
   ]))

   story.append(tbl)
   story.append(Spacer(1, 14))

   # ── Box Total Transfer ──
   total_transfer = sum(float(g.get("total_gaji_salma") or 0) for g in gaji_list)

   COL_LBL = CONTENT_W * 0.55
   COL_VAL = CONTENT_W * 0.45

   grand_tbl = Table(
       [[
           Paragraph("TOTAL GAJI DIBAYARKAN",
                     S("gt_lbl", fontSize=11, fontName="Helvetica-Bold", textColor=BLACK)),
           Paragraph(fmt_rp(total_transfer),
                     S("gt_val", fontSize=12, fontName="Helvetica-Bold",
                       textColor=BLACK, alignment=TA_RIGHT)),
       ]],
       colWidths=[COL_LBL, COL_VAL]
   )
   grand_tbl.setStyle(TableStyle([
       ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
       ("BOX",           (0, 0), (-1, -1), 1.2, GRAY_BORDER),
       ("TOPPADDING",    (0, 0), (-1, -1), 10),
       ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
       ("LEFTPADDING",   (0, 0), (-1, -1), 12),
       ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
       ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
   ]))
   story.append(grand_tbl)

   # ── Tanda Tangan ──
   story += _tanda_tangan(nama_admin, nama_supervisor, nama_direktur, kota)

   # ── Footer ──
   story += _doc_footer(
       nama_admin, tgl_cetak,
       extra=f"Periode: {periode_str}" if dari and sampai else ""
   )

   doc.build(story)
   return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 2. CETAK SEMUA ABSENSI PDF
# ─────────────────────────────────────────────────────────────────────────────
def cetak_semua_absensi_pdf(
    rekap_list: list,
    dari: str,
    sampai: str,
    nama_admin: str,
    nama_supervisor: str = "",
    nama_direktur: str = "",
    kota: str = "Jakarta",
) -> bytes:
   buf = BytesIO()
   doc = SimpleDocTemplate(
       buf, pagesize=A4,
       rightMargin=MARGIN_R, leftMargin=MARGIN_L,
       topMargin=MARGIN_T, bottomMargin=MARGIN_B,
   )

   now = datetime.now()
   tgl_cetak = now.strftime("%d %B %Y")
   periode_str = f"{fmt_date(dari)} – {fmt_date(sampai)}"

   story = []
   story += _doc_header(
       "DATA ABSENSI KARYAWAN",
       "Detail Kehadiran",
       periode_str,
       kota=kota,
       tgl_cetak=tgl_cetak,
   )

   # ── Tabel data absensi ──
   cw = [0.8*cm, 4.2*cm, 3.5*cm, 1.7*cm, 1.7*cm, 1.7*cm, 1.7*cm, 2.1*cm]

   rows = [[
       Paragraph("No",      STYLES["th"]),
       Paragraph("Nama",    STYLES["th_left"]),
       Paragraph("Jabatan", STYLES["th_left"]),
       Paragraph("Hadir",   STYLES["th"]),
       Paragraph("Izin",    STYLES["th"]),
       Paragraph("Sakit",   STYLES["th"]),
       Paragraph("Alpha",   STYLES["th"]),
       Paragraph("Total",   STYLES["th"]),
   ]]

   for i, r in enumerate(rekap_list):
       h  = int(r.get("hadir", 0) or 0)
       iz = int(r.get("izin",  0) or 0)
       sa = int(r.get("sakit", 0) or 0)
       al = int(r.get("alpha", 0) or 0)
       tt = int(r.get("total", 0) or 0)

       if h > 0:
           hadir_cell = Table(
               [[Paragraph(str(h), S("hc", fontSize=8.5, fontName="Helvetica-Bold",
                                      textColor=BLACK, alignment=TA_CENTER))]],
               colWidths=[1.3*cm]
           )
           hadir_cell.setStyle(TableStyle([
               ("BACKGROUND",     (0, 0), (-1, -1), GRAY_LIGHT),
               ("BOX",            (0, 0), (-1, -1), 0.5, GRAY_BORDER),
               ("TOPPADDING",     (0, 0), (-1, -1), 3),
               ("BOTTOMPADDING",  (0, 0), (-1, -1), 3),
           ]))
       else:
           hadir_cell = Paragraph("0", STYLES["center"])

       if al > 0:
           alpha_cell = Table(
               [[Paragraph(str(al), S("ac", fontSize=8.5, fontName="Helvetica-Bold",
                                       textColor=GRAY_TEXT, alignment=TA_CENTER))]],
               colWidths=[1.3*cm]
           )
           alpha_cell.setStyle(TableStyle([
               ("BACKGROUND",     (0, 0), (-1, -1), GRAY_BG_ROW),
               ("BOX",            (0, 0), (-1, -1), 0.5, GRAY_MED),
               ("TOPPADDING",     (0, 0), (-1, -1), 3),
               ("BOTTOMPADDING",  (0, 0), (-1, -1), 3),
           ]))
       else:
           alpha_cell = Paragraph("0", STYLES["center"])

       rows.append([
           Paragraph(str(i + 1), STYLES["center"]),
           Paragraph(r.get("nama_salma", "-"),
                     S("rn", fontSize=8.5, fontName="Helvetica-Bold", textColor=BLACK)),
           Paragraph(r.get("nama_jabatan_salma", "-"),
                     S("rj", fontSize=8, textColor=GRAY_TEXT)),
           hadir_cell,
           Paragraph(str(iz), STYLES["center"]),
           Paragraph(str(sa), STYLES["center"]),
           alpha_cell,
           Paragraph(str(tt),
                     S("tt", fontSize=9, fontName="Helvetica-Bold",
                       alignment=TA_CENTER, textColor=BLACK)),
       ])

   tbl = Table(rows, colWidths=cw, repeatRows=1)
   tbl.setStyle(TableStyle([
       ("BACKGROUND",     (0, 0), (-1, 0),  GRAY_DARK),
       ("LINEBELOW",      (0, 0), (-1, 0),  1, BLACK),
       ("TOPPADDING",     (0, 0), (-1, 0),  8),
       ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
       ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_BG_ROW]),
       ("TOPPADDING",     (0, 1), (-1, -1), 7),
       ("BOTTOMPADDING",  (0, 1), (-1, -1), 7),
       ("LEFTPADDING",    (0, 0), (-1, -1), 5),
       ("RIGHTPADDING",   (0, 0), (-1, -1), 5),
       ("GRID",           (0, 1), (-1, -1), 0.3, GRAY_LINE),
       ("BOX",            (0, 0), (-1, -1), 0.8, GRAY_BORDER),
       ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
       ("ALIGN",          (3, 1), (7, -1),  "CENTER"),
   ]))

   story.append(tbl)

   # ── Keterangan ──
   story.append(Spacer(1, 10))

   def _ket_pill(label, warna_teks, warna_bg, warna_border):
       t = Table(
           [[Paragraph(label, S(f"kp_{label}", fontSize=7, fontName="Helvetica-Bold",
                                 textColor=warna_teks, alignment=TA_CENTER))]],
           colWidths=[1.4*cm]
       )
       t.setStyle(TableStyle([
           ("BACKGROUND",     (0, 0), (-1, -1), warna_bg),
           ("BOX",            (0, 0), (-1, -1), 0.5, warna_border),
           ("TOPPADDING",     (0, 0), (-1, -1), 2),
           ("BOTTOMPADDING",  (0, 0), (-1, -1), 2),
       ]))
       return t

   ket_items = [
       ("Hadir",  BLACK,     GRAY_LIGHT,   GRAY_BORDER, "Hari kerja hadir"),
       ("Izin",   GRAY_DARK, GRAY_BG_ROW,  GRAY_BORDER, "Izin disetujui"),
       ("Sakit",  GRAY_DARK, GRAY_BG_ROW,  GRAY_BORDER, "Sakit disetujui"),
       ("Alpha",  GRAY_TEXT, GRAY_BG_ROW,  GRAY_MED,    "Tanpa keterangan"),
       ("Total",  GRAY_TEXT, GRAY_LIGHT,   GRAY_LINE,   "Jumlah hari kerja"),
   ]

   ket_row_cells = []
   ket_col_widths = []
   for label, warna_teks, warna_bg, warna_border, desc in ket_items:
       ket_row_cells.append(_ket_pill(label, warna_teks, warna_bg, warna_border))
       ket_row_cells.append(
           Paragraph(desc, S(f"kd_{label}", fontSize=7, textColor=GRAY_TEXT))
       )
       ket_col_widths.append(1.5 * cm)
       ket_col_widths.append(1.98 * cm)

   ket_tbl = Table([ket_row_cells], colWidths=ket_col_widths)
   ket_tbl.setStyle(TableStyle([
       ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
       ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_BORDER),
       ("TOPPADDING",    (0, 0), (-1, -1), 7),
       ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
       ("LEFTPADDING",   (0, 0), (-1, -1), 6),
       ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
       ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
   ]))
   story.append(ket_tbl)

   # ── Tanda Tangan ──
   story += _tanda_tangan(nama_admin, nama_supervisor, nama_direktur,  kota)

   # ── Footer ──
   story += _doc_footer(
       nama_admin, tgl_cetak,
       extra=f"Periode: {periode_str}"
   )

   doc.build(story)
   return buf.getvalue()