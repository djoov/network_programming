"""Diagram tambahan: susunan aliran Mini-FTP dan skenario pembatalan transfer."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager as fm

NAVY = "#000000"; TEAL = "#000000"; TINT = "#F2F2F2"; SLATE = "#555555"; AMBER = "#444444"; RED = "#000000"; GREEN = "#000000"
fams = {f.name for f in fm.fontManager.ttflist}
plt.rcParams["font.family"] = "Liberation Serif" if "Liberation Serif" in fams else "DejaVu Serif"
MONO = "DejaVu Sans Mono"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagram")


def box(ax, x, y, w, h, fc, ec, text, fs=7.4, color="white", mono=True, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color,
            family=MONO if mono else None, fontweight="bold" if bold else "normal")


def aliran():
    fig, ax = plt.subplots(figsize=(6.3, 4.1))
    ax.set_xlim(0, 12.6); ax.set_ylim(0, 8.1); ax.axis("off")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99)
    ax.text(6.3, 7.85, "Satu koneksi TCP, dua arah aliran byte", ha="center", va="top", fontsize=12, fontweight="bold", color=NAVY)
    ax.text(6.3, 7.35, "Contoh: GET halo.txt (53 byte) lalu LIST (7 file, 160 byte). Semuanya lewat socket yang sama.",
            ha="center", va="top", fontsize=8.2, color=SLATE, style="italic")
    # arah client -> server
    ax.text(0.2, 6.35, "Client  →  Server", fontsize=9, fontweight="bold", color=NAVY, va="center")
    box(ax, 0.2, 5.4, 3.2, 0.62, "#F2F2F2", AMBER, "GET halo.txt\\n", color=NAVY)
    box(ax, 3.55, 5.4, 1.5, 0.62, "#F2F2F2", AMBER, "LIST\\n", color=NAVY)
    ax.text(1.8, 5.2, "perintah 1 (satu baris)", ha="center", va="top", fontsize=7.2, color=AMBER)
    ax.text(4.3, 5.2, "perintah 2", ha="center", va="top", fontsize=7.2, color=AMBER)
    # arah server -> client
    ax.text(0.2, 4.15, "Server  →  Client", fontsize=9, fontweight="bold", color=NAVY, va="center")
    segs = [("OK 53 mengirim file\\n", 3.0, TINT, TEAL, NAVY, "header: baca sampai \\n"),
            ("53 byte isi halo.txt", 3.4, TEAL, TEAL, "white", "body: baca TEPAT 53 byte"),
            ("OK 160 7 file\\n", 2.3, TINT, TEAL, NAVY, "header"),
            ("160 byte daftar", 2.9, TEAL, TEAL, "white", "body: TEPAT 160 byte")]
    x = 0.2
    for teks, w, fc, ec, col, ket in segs:
        box(ax, x, 3.2, w, 0.62, fc, ec, teks.replace("\\n", "↵"), color=col, fs=7.0)
        ax.text(x + w / 2, 3.0, ket, ha="center", va="top", fontsize=6.8, color=SLATE)
        x += w
    # pembaca client
    ax.annotate("", xy=(0.2, 2.2), xytext=(12.4, 2.2), arrowprops=dict(arrowstyle="-", color="#999999", lw=0.8, ls=(0, (4, 3))))
    ax.text(0.2, 2.0, "Cara client membaca (satu objek pembaca, rfile):", fontsize=8.2, fontweight="bold", color=NAVY, va="top")
    langkah = ["rfile.readline()  →  'OK 53 mengirim file'  (tahu: body 53 byte)",
               "rfile.read(53)    →  isi file persis 53 byte",
               "rfile.readline()  →  'OK 160 7 file'  (tahu: body 160 byte)",
               "rfile.read(160)   →  daftar file persis 160 byte"]
    for i, t in enumerate(langkah):
        ax.text(0.4, 1.55 - i * 0.37, t, fontsize=7.6, family=MONO, color=NAVY, va="center")
    fig.savefig(os.path.join(OUT, "m1_aliran_satu_koneksi.png"), dpi=200, facecolor="white")
    plt.close(fig)


def seq(fname, title, subtitle, xs, heads, groups, steps, bawah, tinggi):
    fig, ax = plt.subplots(figsize=(6.3, tinggi))
    H = tinggi * 2
    ax.set_xlim(0, 12.6); ax.set_ylim(0, H); ax.axis("off")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99)
    top = H - 0.4
    ax.text(6.3, top, title, ha="center", va="top", fontsize=12, fontweight="bold", color=NAVY)
    ax.text(6.3, top - 0.55, subtitle, ha="center", va="top", fontsize=8.3, color=SLATE, style="italic")
    yb = top - 1.25
    for x0, x1, lab, col in groups:
        ax.add_patch(FancyBboxPatch((x0, yb - 0.05), x1 - x0, 0.5, boxstyle="round,pad=0,rounding_size=0.08", fc=col, ec=col))
        ax.text((x0 + x1) / 2, yb + 0.2, lab, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    yh = yb - 0.75
    for x, lab in zip(xs, heads):
        ax.add_patch(FancyBboxPatch((x - 1.15, yh - 0.35), 2.3, 0.7, boxstyle="round,pad=0,rounding_size=0.06", fc=TINT, ec=SLATE, lw=0.8))
        ax.text(x, yh, lab, ha="center", va="center", fontsize=7.4, color=NAVY, linespacing=1.15)
    ybot = 1.2
    for x in xs:
        ax.plot([x, x], [ybot, yh - 0.35], color="#999999", lw=1, ls=(0, (4, 3)), zorder=0)
    y = yh - 0.95
    gap = (y - ybot - 0.2) / len(steps)
    estil = {"ctl": (NAVY, 1.6, "-"), "data": (TEAL, 3.0, "-"), "conn": (AMBER, 1.8, (0, (5, 3))),
             "close": (RED, 1.8, (0, (2, 2))), "ok": (GREEN, 1.6, "-")}
    for i, st in enumerate(steps, 1):
        kind, a, b, label = st
        if kind == "note":
            x = min(max(xs[a], 1.9), 10.6)
            ax.add_patch(FancyBboxPatch((x - 1.9, y - 0.27), 3.8, 0.54, boxstyle="round,pad=0,rounding_size=0.05", fc="#F2F2F2", ec=AMBER, lw=0.8))
            ax.text(x, y, label, ha="center", va="center", fontsize=7, color=NAVY)
        elif kind == "bad":
            x = min(max(xs[a], 1.9), 10.6)
            ax.add_patch(FancyBboxPatch((x - 1.9, y - 0.27), 3.8, 0.54, boxstyle="round,pad=0,rounding_size=0.05", fc="#DDDDDD", ec=RED, lw=0.9))
            ax.text(x, y, label, ha="center", va="center", fontsize=7, color=RED)
        else:
            col, lw, ls = estil[kind]
            ax.add_patch(FancyArrowPatch((xs[a], y), (xs[b], y), arrowstyle="-|>", mutation_scale=11, color=col, lw=lw, linestyle=ls))
            ax.text((xs[a] + xs[b]) / 2, y + 0.1, label, ha="center", va="bottom", fontsize=7.4,
                    color=col if kind != "data" else "#000000", family=MONO if kind == "ctl" else None,
                    fontweight="bold" if kind in ("conn", "data", "close") else "normal",
                    bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
        ax.text(0.05, y, str(i), ha="left", va="center", fontsize=7, color=SLATE)
        y -= gap
    ax.text(6.3, 0.75, bawah, ha="center", va="top", fontsize=7.6, color=RED, style="italic")
    fig.savefig(os.path.join(OUT, fname), dpi=200, facecolor="white")
    plt.close(fig)


aliran()

seq("m2_batal_mini_ftp.png", "Membatalkan GET di Mini-FTP (satu koneksi)",
    "Tidak ada saluran lain: satu-satunya cara berhenti adalah menutup koneksi itu sendiri",
    [2.6, 10.0], ["port client\n(ephemeral)", "port server\n(2121)"],
    [(0.9, 4.3, "CLIENT", "#595959"), (8.3, 11.7, "SERVER", NAVY)],
    [("ctl", 0, 1, "GET besar.bin"),
     ("ctl", 1, 0, "OK 20971520 mengirim file"),
     ("data", 1, 0, "isi file mengalir (20 MB)"),
     ("note", 0, 0, "pengguna menekan Ctrl+C"),
     ("close", 0, 1, "close(): FIN / RST"),
     ("bad", 1, 1, "sendall() gagal: ConnectionReset"),
     ("note", 1, 1, "log: TRANSFER_FAIL, SESSION_END"),
     ("conn", 0, 1, "connect() baru = SESI BARU")],
    "Perintah lain tidak bisa disisipkan: koneksi yang sama sedang penuh dengan data file.", 4.9)

seq("m3_batal_ftp_standar.png", "Membatalkan RETR di FTP standar (dua koneksi)",
    "Control connection tetap bebas, jadi ABOR bisa dikirim sementara data masih mengalir",
    [1.3, 4.1, 8.5, 11.3], ["port kontrol\n(client)", "port data\n(client)", "port data\n(server)", "port 21\n(kontrol)"],
    [(0.15, 5.35, "CLIENT", "#595959"), (7.25, 12.45, "SERVER", NAVY)],
    [("ctl", 0, 3, "RETR besar.bin"),
     ("ctl", 3, 0, "150 Opening data connection"),
     ("data", 2, 1, "isi file mengalir (data connection)"),
     ("note", 0, 0, "pengguna membatalkan"),
     ("ctl", 0, 3, "ABOR  (lewat control connection)"),
     ("close", 2, 1, "server menutup data connection"),
     ("ctl", 3, 0, "426 Transfer aborted"),
     ("ctl", 3, 0, "226 Abort successful"),
     ("ctl", 0, 3, "LIST / RETR lain  (sesi sama)")],
    "Sesi login, direktori kerja, dan pengaturan TYPE tetap hidup. Hanya data connection yang berakhir.", 5.4)
print("ok")
