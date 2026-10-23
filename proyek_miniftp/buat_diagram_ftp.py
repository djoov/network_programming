"""Diagram urutan FTP standar (RFC 959): LIST dan RETR, mode aktif dan pasif."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager as fm

NAVY = "#000000"; TEAL = "#000000"; TINT = "#F2F2F2"; SLATE = "#555555"; BLUE = "#000000"
AMBER = "#444444"; RED = "#000000"; WHITE = "#FFFFFF"
fams = {f.name for f in fm.fontManager.ttflist}
plt.rcParams["font.family"] = "Liberation Serif" if "Liberation Serif" in fams else "DejaVu Serif"
MONO = "DejaVu Sans Mono"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagram")
os.makedirs(OUT, exist_ok=True)

XS = [1.3, 4.1, 8.5, 11.3]   # client kontrol, client data, server data, server kontrol
STYLE = {
    "ctl": dict(color=NAVY, lw=1.6, ls="-"),
    "data": dict(color=TEAL, lw=3.0, ls="-"),
    "conn": dict(color=AMBER, lw=1.8, ls=(0, (5, 3))),
    "cconn": dict(color=NAVY, lw=1.4, ls=(0, (5, 3))),
    "close": dict(color=SLATE, lw=1.4, ls=(0, (2, 2))),
}


def draw(fname, title, subtitle, heads, steps, notes=(), height=None):
    n = len(steps)
    h = height or (2.5 + n * 0.44)
    fig, ax = plt.subplots(figsize=(6.3, h))
    ax.set_xlim(0, 12.6); ax.set_ylim(0, h * 2); ax.axis("off")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99)
    top = h * 2 - 0.4
    ax.text(6.3, top, title, ha="center", va="top", fontsize=12, fontweight="bold", color=NAVY)
    ax.text(6.3, top - 0.55, subtitle, ha="center", va="top", fontsize=8.5, color=SLATE, style="italic")
    # kelompok client / server
    yb = top - 1.25
    for x0, x1, lab, col in ((0.15, 5.35, "CLIENT", "#595959"), (7.25, 12.45, "SERVER", NAVY)):
        ax.add_patch(FancyBboxPatch((x0, yb - 0.05), x1 - x0, 0.5, boxstyle="round,pad=0,rounding_size=0.08", fc=col, ec=col))
        ax.text((x0 + x1) / 2, yb + 0.2, lab, ha="center", va="center", color=WHITE, fontsize=10, fontweight="bold")
    yh = yb - 0.75
    for x, lab in zip(XS, heads):
        ax.add_patch(FancyBboxPatch((x - 1.15, yh - 0.35), 2.3, 0.7, boxstyle="round,pad=0,rounding_size=0.06", fc=TINT, ec=SLATE, lw=0.8))
        ax.text(x, yh, lab, ha="center", va="center", fontsize=7.4, color=NAVY, linespacing=1.15)
    ybot = 1.55
    for x in XS:
        ax.plot([x, x], [ybot, yh - 0.35], color="#999999", lw=1, ls=(0, (4, 3)), zorder=0)
    # langkah
    y = yh - 0.95
    gap = (y - ybot - 0.3) / max(n, 1)
    for i, st in enumerate(steps, 1):
        kind, a, b, label = st[:4]
        if kind == "note":
            x = XS[a]
            ax.add_patch(FancyBboxPatch((x - 1.2, y - 0.27), 2.4, 0.54, boxstyle="round,pad=0,rounding_size=0.05", fc="#F2F2F2", ec=AMBER, lw=0.8))
            ax.text(x, y, label, ha="center", va="center", fontsize=7, color=NAVY)
        else:
            s = STYLE[kind]
            x1, x2 = XS[a], XS[b]
            ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=11, color=s["color"], lw=s["lw"], linestyle=s["ls"]))
            mx = (x1 + x2) / 2
            ax.text(mx, y + 0.1, label, ha="center", va="bottom", fontsize=7.4, color=s["color"] if kind != "data" else "#000000",
                    family=MONO if kind == "ctl" else None, fontweight="bold" if kind in ("conn", "data") else "normal",
                    bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
        ax.text(0.05, y, str(i), ha="left", va="center", fontsize=7, color=SLATE)
        y -= gap
    # legenda
    items = [("cconn", "buka control connection", 0.3, 0.7), ("ctl", "perintah/respons (control)", 4.5, 0.7),
             ("data", "isi data (data connection)", 8.7, 0.7), ("conn", "buka data connection", 0.3, 0.25),
             ("close", "tutup data connection", 4.5, 0.25)]
    for k, t, lx, ly in items:
        s = STYLE[k]
        ax.plot([lx, lx + 0.7], [ly, ly], color=s["color"], lw=s["lw"], ls=s["ls"])
        ax.text(lx + 0.8, ly, t, va="center", fontsize=7.2, color=NAVY)
    for j, t in enumerate(notes):
        ax.text(6.3, ybot - 0.12, t, ha="center", va="top", fontsize=7.6, color=RED, style="italic")
    fig.savefig(os.path.join(OUT, fname), dpi=200, facecolor="white")
    plt.close(fig)


LOGIN = [
    ("cconn", 0, 3, "TCP connect ke port 21 (control connection)"),
    ("ctl", 3, 0, "220 Service ready"),
    ("ctl", 0, 3, "USER van / PASS ****"),
    ("ctl", 3, 0, "331 ... lalu 230 Login OK"),
]

HEAD_ACT = ["port kontrol\n(ephemeral N)", "port data P\n(client LISTEN)", "port data 20\n(server)", "port 21\n(kontrol)"]
HEAD_PAS = ["port kontrol\n(ephemeral N)", "port data\n(ephemeral)", "port data P\n(server LISTEN)", "port 21\n(kontrol)"]

draw("ftp_list_aktif.png", "LIST pada mode aktif",
     "Server yang MEMBUKA koneksi data ke client (dari port 20 ke port P milik client)", HEAD_ACT,
     LOGIN + [
         ("note", 1, 1, "client listen di port P"),
         ("ctl", 0, 3, "PORT h1,h2,h3,h4,p1,p2"),
         ("ctl", 3, 0, "200 PORT command OK"),
         ("ctl", 0, 3, "LIST"),
         ("ctl", 3, 0, "150 Opening data connection"),
         ("conn", 2, 1, "server connect: 20 -> P"),
         ("data", 2, 1, "daftar direktori (teks)"),
         ("close", 2, 1, "server menutup koneksi data (FIN)"),
         ("ctl", 3, 0, "226 Transfer complete"),
     ], notes=["Akhir daftar ditandai dengan DITUTUPNYA koneksi data, bukan dengan penanda di dalam data."])

draw("ftp_list_pasif.png", "LIST pada mode pasif",
     "Client yang MEMBUKA koneksi data ke server (ke port P yang diumumkan server)", HEAD_PAS,
     LOGIN + [
         ("ctl", 0, 3, "PASV"),
         ("note", 2, 2, "server listen di port P"),
         ("ctl", 3, 0, "227 Entering Passive Mode (h1,..,p1,p2)"),
         ("conn", 1, 2, "client connect -> P"),
         ("ctl", 0, 3, "LIST"),
         ("ctl", 3, 0, "150 Here comes the listing"),
         ("data", 2, 1, "daftar direktori (teks)"),
         ("close", 2, 1, "server menutup koneksi data (FIN)"),
         ("ctl", 3, 0, "226 Transfer complete"),
     ], notes=["Arah data tetap dari server ke client. Yang berubah adalah SIAPA yang memulai koneksi data."])

draw("ftp_retr_aktif.png", "RETR (GET) pada mode aktif",
     "Unduh file: perintah lewat port 21, isi file lewat koneksi data baru dari port 20", HEAD_ACT,
     LOGIN + [
         ("ctl", 0, 3, "TYPE I"),
         ("ctl", 3, 0, "200 Type set to I (binary)"),
         ("note", 1, 1, "client listen di port P"),
         ("ctl", 0, 3, "PORT h1,h2,h3,h4,p1,p2"),
         ("ctl", 3, 0, "200 PORT command OK"),
         ("ctl", 0, 3, "RETR laporan.pdf"),
         ("ctl", 3, 0, "150 Opening BINARY data connection"),
         ("conn", 2, 1, "server connect: 20 -> P"),
         ("data", 2, 1, "isi file laporan.pdf (byte)"),
         ("close", 2, 1, "server menutup koneksi data (FIN)"),
         ("ctl", 3, 0, "226 Transfer complete"),
     ], notes=["Selama isi file mengalir, port 21 tetap bebas: client bisa mengirim ABOR."])

draw("ftp_retr_pasif.png", "RETR (GET) pada mode pasif",
     "Unduh file: client membuka koneksi data ke port P milik server", HEAD_PAS,
     LOGIN + [
         ("ctl", 0, 3, "TYPE I"),
         ("ctl", 3, 0, "200 Type set to I (binary)"),
         ("ctl", 0, 3, "PASV"),
         ("note", 2, 2, "server listen di port P"),
         ("ctl", 3, 0, "227 Entering Passive Mode (h1,..,p1,p2)"),
         ("conn", 1, 2, "client connect -> P"),
         ("ctl", 0, 3, "RETR laporan.pdf"),
         ("ctl", 3, 0, "150 Opening BINARY data connection"),
         ("data", 2, 1, "isi file laporan.pdf (byte)"),
         ("close", 2, 1, "server menutup koneksi data (FIN)"),
         ("ctl", 3, 0, "226 Transfer complete"),
     ], notes=["Mode pasif lebih ramah NAT dan firewall di sisi client, karena client tidak perlu menerima koneksi masuk."])
print("ok")
