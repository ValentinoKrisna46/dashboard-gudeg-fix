from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import olah

st.set_page_config(page_title="Dashboard Gudeg Sekar Arum", page_icon="🍛", layout="wide",
                   initial_sidebar_state="collapsed")

ORG, BLU = "#D9822B", "#4A7FA7"            # sama dengan gambar D3 di laporan: oranye = wisatawan, biru = lokal
GRY, BRN = "#A7ADB5", "#8C4A12"            # abu-abu netral, cokelat = libur nasional (G7)
SL1, SL2, SL3 = "#2F3E52", "#7C8CA3", "#C5CCD6"   # abu-biru netral untuk kanal
INK, MUTE, GRID = "#1B2430", "#6B7686", "#EDF0F4"
DATA_BAWAAN = Path(__file__).parent / "D2_data_transformasi.csv"


# ---------------------------------------------------------------- format angka (gaya Indonesia)
def nf(x):
    return f"{x:,.0f}".replace(",", ".")


def dec(x, n=1):
    return f"{x:,.{n}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def rp(x):
    a = abs(x)
    if a >= 1e9:
        return f"Rp{dec(x / 1e9, 2)} miliar"
    if a >= 1e6:
        return f"Rp{dec(x / 1e6, 1)} juta"
    return f"Rp{nf(x)}"


def p1(x):
    return dec(x, 1) + "%"


def p0(x):
    return f"{x:.0f}%"


# ---------------------------------------------------------------- data
@st.cache_data(show_spinner=False)
def baca_bawaan():
    return olah.muat(DATA_BAWAAN)


@st.cache_data(show_spinner=False)
def baca_unggahan(isi: bytes, nama: str):
    import io
    b = io.BytesIO(isi)
    b.name = nama
    return olah.muat(b)


# ---------------------------------------------------------------- gaya
st.markdown(
    f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input {{font-family:'Source Sans 3',system-ui,sans-serif}}
header[data-testid="stHeader"]{{background:transparent}}
.block-container{{padding-top:1.6rem;max-width:1240px}}
div[class*="st-key-card"]{{background:#fff;border:1px solid #E3E7EC;border-radius:12px;padding:18px 20px 10px;
  box-shadow:0 1px 2px rgba(27,36,48,.04)}}
.pill{{display:inline-block;background:#DDF3EE;color:#0F6B5C;border-radius:999px;padding:3px 12px;font-size:11px;
  font-weight:700;letter-spacing:.07em;text-transform:uppercase}}
.top{{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}}
.per{{text-align:right;font-size:13px;color:{MUTE}}} .per b{{display:block;color:{INK};font-size:15px}}
h1.ttl{{font-size:clamp(28px,4vw,40px);font-weight:800;margin:10px 0 2px;padding:0;color:{INK};letter-spacing:-.01em}}
.sb{{color:{MUTE};font-size:15px;margin-bottom:14px}}
.help{{font-size:13px;color:{MUTE};margin-top:2px}}
.kc{{background:#fff;border:1px solid #E3E7EC;border-radius:12px;padding:14px 16px;height:100%}}
.kc.hl{{border-color:{ORG};box-shadow:0 0 0 1px {ORG}}}
.kc .l{{font-size:13px;color:{MUTE}}}
.kc .v{{font-size:28px;font-weight:800;margin-top:2px;line-height:1.15;color:{INK};overflow-wrap:anywhere}}
.kc.hl .v{{color:{ORG}}}
.kc .s{{font-size:12px;color:{MUTE};margin-top:3px}}
.ct{{font-size:18px;font-weight:700;line-height:1.25;color:{INK};margin:0 0 2px}}
.cs{{font-size:13px;color:{MUTE};margin:0 0 6px}}
label[data-testid="stWidgetLabel"] p{{font-size:13px;color:{MUTE}}}
.gtag{{display:inline-block;font-size:11px;font-weight:700;color:{BLU};background:#EAF1F7;border-radius:6px;padding:1px 8px;margin-bottom:6px}}
</style>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Sumber data")
    unggah = st.file_uploader("Ganti sumber data (opsional)", type=["csv", "xlsx"],
                              help="CSV hasil transformasi, atau XLSX dengan sheet Data_Penjualan.")
try:
    data = baca_unggahan(unggah.getvalue(), unggah.name) if unggah else baca_bawaan()
except Exception as e:  # noqa: BLE001
    st.error(f"Data tidak dapat dibaca: {e}")
    st.stop()

tmin, tmax = data.Tanggal.min().date(), data.Tanggal.max().date()

# ---------------------------------------------------------------- kepala halaman
st.markdown(
    f"""<div class="top"><div><span class="pill">Dashboard interaktif · 2025</span>
<h1 class="ttl">Dashboard Pelanggan Wisatawan dan Lokal</h1>
<div class="sb">Gudeg Sekar Arum · Fokus audiens: Tim Pemasaran · Kapan wisatawan mendominasi dan kapan pelanggan lokal menjadi andalan?</div></div>
<div class="per"><b>Periode data</b>{tmin:%d-%m-%Y} s.d. {tmax:%d-%m-%Y}</div></div>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- filter (dropdown satu baris)
with st.container(key="card_filter"):
    f1, f2, f3, f4 = st.columns(4)
    s_out = f1.selectbox("Outlet", ["Semua outlet"] + olah.OUTLET)
    s_kan = f2.selectbox("Kanal penjualan", ["Semua kanal"] + olah.KANAL)
    s_bln = f3.selectbox("Bulan", ["Semua bulan"] + olah.BULAN)
    s_jen = f4.selectbox("Jenis hari", ["Semua jenis hari"] + olah.JENIS_HARI)
    st.markdown('<div class="help">Pilih filter di atas; semua kartu dan grafik ikut berubah. Grafik tren '
                '(G1 dan G8) dan heatmap G9 selalu menampilkan 12 bulan, jadi tidak terpengaruh filter Bulan. '
                'Label “Gambar 2.x · G#” merujuk ke Bab Portofolio Grafik di laporan.</div>',
                unsafe_allow_html=True)

f_out = olah.OUTLET if s_out.startswith("Semua") else [s_out]
f_kan = olah.KANAL if s_kan.startswith("Semua") else [s_kan]
f_jen = olah.JENIS_HARI if s_jen.startswith("Semua") else [s_jen]

d_tahun = olah.saring(data, f_out, f_kan, f_jen, tmin, tmax)          # untuk grafik tren (12 bulan)
df = d_tahun if s_bln.startswith("Semua") else d_tahun[d_tahun.Bulan_No == olah.BULAN.index(s_bln) + 1]

st.write("")
if df.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini. Pilih “Semua” pada salah satu filter.")
    st.stop()

K, K0 = olah.ringkas(df), olah.ringkas(data)

# ---------------------------------------------------------------- KPI
def kpi(label, nilai, sub, hl=False):
    return f'<div class="kc{" hl" if hl else ""}"><div class="l">{label}</div><div class="v">{nilai}</div><div class="s">{sub}</div></div>'


k = st.columns(5)
k[0].markdown(kpi("Omzet bersih", rp(K["omzet"]), "omzet gudeg + oleh-oleh − diskon"), unsafe_allow_html=True)
k[1].markdown(kpi("Jumlah transaksi", nf(K["trx"]), f"{nf(K['trx'] / K['hari'])} per hari"), unsafe_allow_html=True)
k[2].markdown(kpi("Rata-rata nilai transaksi", "Rp" + nf(K["avg"]), "omzet bersih ÷ jumlah transaksi"), unsafe_allow_html=True)
k[3].markdown(kpi("Rating berbobot", f"{dec(K['rating'], 2)} / 5" if K["rating"] else "–",
                  f"dari {nf(K['ulasan'])} ulasan"), unsafe_allow_html=True)
selisih = K["pangsa"] - K0["pangsa"]
k[4].markdown(kpi("Pangsa wisatawan", p1(K["pangsa"]),
                  (f"{selisih:+.1f} poin vs seluruh usaha ({p1(K0['pangsa'])})".replace(".", ",")
                   if abs(selisih) >= 0.05 else "Σ wisatawan ÷ Σ transaksi"), hl=True), unsafe_allow_html=True)
st.write("")


# ---------------------------------------------------------------- pembantu
ANGKA = {1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima", 6: "enam", 7: "tujuh", 8: "delapan",
         9: "sembilan", 10: "sepuluh", 11: "sebelas", 12: "dua belas"}
_n = [0]


def kartu(judul, sub, tag):
    _n[0] += 1
    c = st.container(key=f"card_{_n[0]}")
    with c:
        st.markdown(f'<span class="gtag">{tag}</span><div class="ct">{judul}</div><div class="cs">{sub}</div>',
                    unsafe_allow_html=True)
    return c


def gabung(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " dan " + xs[-1] if len(xs) > 2 else " dan ".join(xs)


def rapi(fig, tinggi, **kw):
    fig.update_layout(height=tinggi, margin=dict(l=6, r=16, t=22, b=8), paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(family="Source Sans 3, sans-serif", size=13, color=INK),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                      **kw)
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#C9D0D9")
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def tumpuk(nama, pangsa, wis, lok, tinggi):
    """Stacked bar 100% horizontal (G4, G5, G6): persen ditulis di dalam batang."""
    fig = go.Figure()
    fig.add_bar(y=nama, x=pangsa, orientation="h", name="Wisatawan", marker_color=ORG,
                text=[p1(v) for v in pangsa], textposition="inside", insidetextanchor="middle",
                textfont=dict(color="white", size=14), customdata=[nf(v) for v in wis],
                hovertemplate="Wisatawan: %{x:.1f}% (%{customdata} transaksi)<extra></extra>")
    fig.add_bar(y=nama, x=[100 - v for v in pangsa], orientation="h", name="Lokal", marker_color=BLU,
                text=[p1(100 - v) for v in pangsa], textposition="inside", insidetextanchor="middle",
                textfont=dict(color="white", size=14), customdata=[nf(v) for v in lok],
                hovertemplate="Lokal: %{x:.1f}% (%{customdata} transaksi)<extra></extra>")
    fig.update_layout(barmode="stack")
    fig.update_xaxes(range=[0, 100], dtick=20, title="Persen dari jumlah transaksi (%)")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return rapi(fig, tinggi)


def urut(g):
    return g.dropna(subset=["pangsa"]).sort_values("pangsa", ascending=False)


M = olah.agregat(d_tahun, "Bulan_No").reindex(range(1, 13))     # 12 bulan, filter Bulan tidak berlaku
xb = olah.BULAN_S
DEFAULT = (s_out.startswith("Semua") and s_kan.startswith("Semua") and s_jen.startswith("Semua"))

# ================================================================ BARIS 1: tren  (G1, G8)
a, b = st.columns([1.2, 1])
with a:
    unggul = [m for m in range(1, 13) if pd.notna(M.wis[m]) and M.wis[m] > M.lokal[m]]
    if M.wis.notna().sum() == 0:
        judul = "Transaksi wisatawan dan pelanggan lokal per bulan"
    elif not unggul:
        judul = "Pelanggan lokal unggul atas wisatawan di semua bulan"
    elif len(unggul) == 12:
        judul = "Wisatawan unggul atas pelanggan lokal di semua bulan"
    else:
        judul = (f"Wisatawan melampaui pelanggan lokal {'hanya ' if len(unggul) <= 6 else ''}pada {ANGKA[len(unggul)]} bulan: "
                 + gabung([olah.BULAN[m - 1] for m in unggul]))
    c = kartu(judul, "Jumlah transaksi wisatawan dan pelanggan lokal per bulan (12 bulan, tanpa filter Bulan).",
              "Gambar 2.1 · G1")
    hi = M.wis.idxmax() if M.wis.notna().any() else None
    lo = M.wis.idxmin() if M.wis.notna().any() else None
    teks = [nf(v) if (m in (hi, lo)) else "" for m, v in zip(M.index, M.wis.fillna(0))]
    fig = go.Figure()
    fig.add_bar(x=xb, y=M.wis, name="Wisatawan", marker_color=ORG, text=teks, textposition="outside",
                hovertemplate="Wisatawan: %{y:,} transaksi<extra></extra>")
    fig.add_bar(x=xb, y=M.lokal, name="Lokal", marker_color=BLU,
                hovertemplate="Lokal: %{y:,} transaksi<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.2)
    fig.update_yaxes(title="Jumlah transaksi per bulan", rangemode="tozero", tickformat=",d")
    with c:
        st.plotly_chart(rapi(fig, 340), use_container_width=True)
with b:
    valid = M.pangsa.dropna()
    if len(valid) >= 2:
        lo, hi = int(valid.idxmin()), int(valid.idxmax())
        if lo < hi:
            judul = f"Pangsa wisatawan naik dari {p0(valid[lo])} pada {olah.BULAN[lo - 1]} menjadi {p0(valid[hi])} pada {olah.BULAN[hi - 1]}"
        else:
            judul = f"Pangsa wisatawan turun dari {p0(valid[hi])} pada {olah.BULAN[hi - 1]} menjadi {p0(valid[lo])} pada {olah.BULAN[lo - 1]}"
        if DEFAULT:
            judul += ", dengan puncak tambahan pada April dan Juni–Juli"
    else:
        judul = "Pangsa wisatawan sepanjang 2025"
    c = kartu(judul, "Rata-rata bergerak 7 hari dari persen transaksi wisatawan. Garis putus-putus: rata-rata tahun.",
              "Gambar 2.8 · G8")
    kal = pd.date_range(tmin, tmax)
    dh = d_tahun.groupby("Tanggal")[["Jumlah_Transaksi", "Transaksi_Wisatawan"]].sum().reindex(kal, fill_value=0)
    rt = dh.Jumlah_Transaksi.rolling(7, min_periods=7).sum()
    rw = dh.Transaksi_Wisatawan.rolling(7, min_periods=7).sum()
    ma = (rw / rt * 100).where(rt > 0)
    rata = olah.ringkas(d_tahun)["pangsa"] if len(d_tahun) else 0
    fig = go.Figure(go.Scatter(x=ma.index, y=ma, mode="lines", line=dict(color=ORG, width=2.5),
                               hovertemplate="%{x|%d-%m-%Y}: %{y:.1f}% wisatawan<extra></extra>"))
    fig.add_hline(y=rata, line_dash="dash", line_color="#8A94A3")
    mv = ma.dropna()
    if len(mv):
        for ts, tx, ay in [(mv.idxmax(), "Puncak", -28), (mv.idxmin(), "Lembah", 28)]:
            fig.add_annotation(x=ts, y=mv[ts], text=f"{tx}: {ts.day} {olah.BULAN_S[ts.month - 1]}, {p1(mv[ts])}",
                               showarrow=True, arrowhead=0, ay=ay, font=dict(size=12, color=ORG))
    fig.update_xaxes(tickvals=list(pd.date_range(tmin, tmax, freq="MS")),
                     ticktext=[olah.BULAN_S[m.month - 1] for m in pd.date_range(tmin, tmax, freq="MS")])
    fig.update_yaxes(range=[30, 75], ticksuffix="%", title="Persen transaksi dari wisatawan")
    with c:
        st.plotly_chart(rapi(fig, 340, showlegend=False), use_container_width=True)
st.write("")

# ================================================================ BARIS 2: perbandingan  (G4 outlet, G5 kanal)
a, b = st.columns(2)
with a:
    GO_ = urut(olah.agregat(df, "Outlet"))
    hiW = [o for o in GO_.index if GO_.pangsa[o] > 50]
    loW = [o for o in GO_.index if GO_.pangsa[o] <= 50]
    if hiW and loW:
        judul = f"{gabung(hiW)} bergantung pada wisatawan, sedangkan {gabung(loW)} pada pelanggan lokal"
    elif hiW:
        judul = f"{gabung(hiW)} lebih banyak melayani wisatawan daripada pelanggan lokal"
    else:
        judul = f"{gabung(loW)} lebih banyak melayani pelanggan lokal daripada wisatawan"
    c = kartu(judul, "Pangsa wisatawan = Σ transaksi wisatawan ÷ Σ jumlah transaksi per outlet, diurutkan dari terbesar.",
              "Gambar 2.4 · G4")
    with c:
        st.plotly_chart(tumpuk(list(GO_.index), list(GO_.pangsa), list(GO_.wis), list(GO_.lokal), 110 + 62 * len(GO_)),
                        use_container_width=True)
with b:
    GK = urut(olah.agregat(df, "Kanal_Penjualan"))
    if len(GK) >= 2:
        h_, l_ = GK.index[0], GK.index[-1]
        if GK.pangsa.iloc[-1] < 15:
            judul = f"{h_} paling banyak dipakai wisatawan, sedangkan {l_.lower()} hampir seluruhnya lokal"
        else:
            judul = f"{h_} paling banyak dipakai wisatawan ({p0(GK.pangsa.iloc[0])}), {l_.lower()} paling lokal ({p0(GK.pangsa.iloc[-1])} wisatawan)"
    else:
        judul = f"Pangsa wisatawan pada kanal {GK.index[0].lower()}: {p1(GK.pangsa.iloc[0])}"
    c = kartu(judul, "Pangsa wisatawan = Σ transaksi wisatawan ÷ Σ jumlah transaksi per kanal, diurutkan dari terbesar.",
              "Gambar 2.5 · G5")
    with c:
        st.plotly_chart(tumpuk(list(GK.index), list(GK.pangsa), list(GK.wis), list(GK.lokal), 110 + 62 * len(GK)),
                        use_container_width=True, key="g5")
st.write("")

# ================================================================ BARIS 3: jenis hari  (G6 komposisi, G2 rata-rata per hari)
a, b = st.columns(2)
JD = olah.per_hari(df, "Jenis_Hari").reindex([j for j in olah.JENIS_HARI if j in df.Jenis_Hari.unique()])
with a:
    if len(JD) >= 2:
        f_, l_ = JD.index[0], JD.index[-1]
        arah = "naik" if JD.pangsa.iloc[-1] >= JD.pangsa.iloc[0] else "turun"
        judul = f"Pangsa wisatawan {arah} dari {p0(JD.pangsa.iloc[0])} pada {f_.lower()} menjadi {p0(JD.pangsa.iloc[-1])} pada {l_.lower()}"
    else:
        judul = f"Pangsa wisatawan pada {JD.index[0].lower()}: {p1(JD.pangsa.iloc[0])}"
    c = kartu(judul, "Komposisi transaksi menurut jenis hari, diurutkan dari hari kerja ke libur nasional. Libur nasional bersifat perkiraan.",
              "Gambar 2.6 · G6")
    with c:
        st.plotly_chart(tumpuk(list(JD.index), list(JD.pangsa), list(JD.wis), list(JD.lokal), 110 + 62 * len(JD)),
                        use_container_width=True, key="g6")
with b:
    judul = "Rata-rata transaksi per hari menurut jenis hari"
    if "Hari kerja" in JD.index and len(JD) > 1 and JD.wis_hari["Hari kerja"] > 0 and JD.lokal_hari["Hari kerja"] > 0:
        wn = (JD.wis_hari / JD.wis_hari["Hari kerja"] - 1).drop("Hari kerja").max()
        ln = (JD.lokal_hari / JD.lokal_hari["Hari kerja"] - 1).drop("Hari kerja").max()
        if wn >= 0.5 and ln <= 0.25:
            judul = "Akhir pekan dan libur nasional hampir melipatgandakan wisatawan, tetapi hampir tidak mengubah pelanggan lokal"
        else:
            judul = f"Wisatawan naik hingga {p0(wn * 100)} pada hari libur dan akhir pekan, pelanggan lokal naik {p0(ln * 100)}"
    c = kartu(judul, "Σ transaksi ÷ jumlah hari pada jenis hari itu (adil karena jumlah hari tiap jenis berbeda).",
              "Gambar 2.2 · G2")
    lab = [f"{j} ({int(h)} hari)" for j, h in zip(JD.index, JD.hari)]
    fig = go.Figure()
    fig.add_bar(x=lab, y=JD.wis_hari, name="Wisatawan", marker_color=ORG, text=[nf(v) for v in JD.wis_hari],
                textposition="outside", hovertemplate="Wisatawan: %{y:.0f} transaksi/hari<extra></extra>")
    fig.add_bar(x=lab, y=JD.lokal_hari, name="Lokal", marker_color=BLU, text=[nf(v) for v in JD.lokal_hari],
                textposition="outside", hovertemplate="Lokal: %{y:.0f} transaksi/hari<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.25)
    fig.update_yaxes(title="Rata-rata transaksi per hari", rangemode="tozero")
    with c:
        st.plotly_chart(rapi(fig, 110 + 62 * max(len(JD), 3)), use_container_width=True)
st.write("")

# ================================================================ BARIS 4: heatmap G9 + boxplot G3
a, b = st.columns([1.25, 1])
with a:
    uo2 = [o for o in olah.OUTLET if o in d_tahun.Outlet.unique()]
    A = olah.agregat(d_tahun, ["Outlet", "Bulan_No"]).reset_index()
    z, tips = [], []
    rentang = {}
    for o in uo2:
        zr, tr = [], []
        for m in range(1, 13):
            r = A[(A.Outlet == o) & (A.Bulan_No == m)]
            if len(r) and r.trx.iloc[0] > 0:
                v = float(r.pangsa.iloc[0])
                zr.append(v)
                tr.append(f"{o}, {olah.BULAN[m - 1]}: {p1(v)} wisatawan ({nf(r.wis.iloc[0])} dari {nf(r.trx.iloc[0])} transaksi)")
            else:
                zr.append(None)
                tr.append(f"{o}, {olah.BULAN[m - 1]}: tidak ada data")
        z.append(zr)
        tips.append(tr)
        vv = [v for v in zr if v is not None]
        if vv:
            rentang[o] = (min(vv), max(vv))
    tinggi_o = [o for o in rentang if rentang[o][0] >= 50]
    rendah_o = [o for o in rentang if rentang[o][1] < 50]
    if tinggi_o and rendah_o and len(rentang) >= 2:
        judul = (f"Pola musiman serupa di semua outlet, tetapi tingkatnya berbeda: {gabung(tinggi_o)} "
                 f"{min(rentang[o][0] for o in tinggi_o):.0f}–{max(rentang[o][1] for o in tinggi_o):.0f}%, "
                 f"{gabung(rendah_o)} di bawah {max(rentang[o][1] for o in rendah_o):.0f}%")
    else:
        judul = "Pangsa wisatawan per outlet dan bulan"
    c = kartu(judul, "Persen wisatawan (Σ ÷ Σ) per outlet dan bulan, skala 0–100%. Makin gelap, makin banyak wisatawan.",
              "Gambar 2.9 · G9")
    fig = go.Figure(go.Heatmap(z=z, x=xb, y=uo2, zmin=0, zmax=100, xgap=3, ygap=3, showscale=True,
                               colorscale=[[0, "#FBEFE3"], [1, "#8A4A0C"]], customdata=tips,
                               colorbar=dict(title="%", ticksuffix="%", len=0.9, thickness=12),
                               hovertemplate="%{customdata}<extra></extra>"))
    for i, o in enumerate(uo2):
        for j, mn in enumerate(xb):
            v = z[i][j]
            fig.add_annotation(x=mn, y=o, showarrow=False, text="–" if v is None else f"{v:.0f}",
                               font=dict(size=13, color="white" if (v is not None and v > 52) else INK))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    with c:
        st.plotly_chart(rapi(fig, 110 + 62 * len(uo2)), use_container_width=True)
with b:
    hh = df.groupby(["Outlet", "Tanggal"], observed=True).agg(t=("Jumlah_Transaksi", "sum"),
                                                              w=("Transaksi_Wisatawan", "sum")).reset_index()
    hh = hh[hh.t > 0].assign(p=lambda x: x.w / x.t * 100)
    med = hh.groupby("Outlet").p.median().sort_values(ascending=False)
    if len(med) >= 4:
        judul = f"Pangsa wisatawan harian di {gabung(list(med.index[:2]))} berada jauh di atas {gabung(list(med.index[-2:]))}"
    elif len(med) >= 2:
        judul = f"Pangsa wisatawan harian tertinggi di {med.index[0]}, terendah di {med.index[-1]}"
    else:
        judul = f"Sebaran pangsa wisatawan harian di {med.index[0]}"
    c = kartu(judul, "Boxplot persen wisatawan per hari (semua kanal terpilih), diurutkan dari median tertinggi. Angka = median.",
              "Gambar 2.3 · G3")
    fig = go.Figure()
    for o in med.index:
        warna = ORG if med[o] > 50 else BLU
        fig.add_box(y=hh[hh.Outlet == o].p, name=o, marker_color=warna, line_color=warna, boxpoints="outliers",
                    hovertemplate="%{y:.1f}% wisatawan<extra></extra>")
        fig.add_annotation(x=o, y=med[o], text=f"<b>{p1(med[o])}</b>", showarrow=False, xanchor="left", xshift=34,
                           font=dict(size=12, color=INK))
    fig.update_yaxes(range=[0, 100], dtick=20, ticksuffix="%", title="Persen wisatawan per hari")
    with c:
        st.plotly_chart(rapi(fig, 110 + 62 * max(len(uo2), 4), showlegend=False), use_container_width=True)
st.write("")

# ================================================================ BARIS 5: scatter G7 + dot plot G10
a, b = st.columns(2)
with a:
    dg = df.groupby("Tanggal").agg(t=("Jumlah_Transaksi", "sum"), w=("Transaksi_Wisatawan", "sum"),
                                   om=("Omzet_Bersih_Rp", "sum"), j=("Jenis_Hari", "first")).reset_index()
    dg = dg[dg.t > 0].assign(p=lambda x: x.w / x.t * 100)
    r = None
    if len(dg) >= 3 and dg.p.std() > 0 and dg.om.std() > 0:
        r = float(dg.p.corr(dg.om))
    if r is None:
        judul = "Hubungan pangsa wisatawan harian dengan omzet harian"
    elif r >= 0.5:
        judul = "Semakin tinggi pangsa wisatawan pada suatu hari, semakin besar omzet hari itu"
    elif r <= -0.5:
        judul = "Semakin tinggi pangsa wisatawan pada suatu hari, semakin kecil omzet hari itu"
    else:
        judul = "Pangsa wisatawan harian hanya berhubungan lemah dengan omzet harian"
    c = kartu(judul, "Tiap titik = satu hari. Hari kerja diredam menjadi abu-abu. Ini hubungan, bukan bukti sebab-akibat.",
              "Gambar 2.7 · G7")
    fig = go.Figure()
    for jn, wr in [("Hari kerja", GRY), ("Akhir pekan", ORG), ("Libur nasional", BRN)]:
        sub_ = dg[dg.j == jn]
        if len(sub_):
            fig.add_scatter(x=sub_.p, y=sub_.om / 1e6, mode="markers", name=jn,
                            marker=dict(color=wr, size=7, opacity=0.8 if jn != "Hari kerja" else 0.6),
                            customdata=sub_.Tanggal.dt.strftime("%d-%m-%Y"),
                            hovertemplate="%{customdata}: %{x:.1f}% wisatawan, Rp%{y:.1f} juta<extra>" + jn + "</extra>")
    if r is not None:
        fig.add_annotation(xref="paper", yref="paper", x=0.02, y=0.98, showarrow=False, xanchor="left", yanchor="top",
                           text=f"<b>r = {dec(r, 2)}</b>", font=dict(size=15, color=INK))
    fig.update_xaxes(ticksuffix="%", title="Persen wisatawan harian", showgrid=False)
    fig.update_yaxes(title="Omzet bersih harian (Rp juta)", rangemode="tozero")
    with c:
        st.plotly_chart(rapi(fig, 340), use_container_width=True)
with b:
    RT = olah.agregat(df, "Outlet").dropna(subset=["rating"]).sort_values("rating")
    bk = df[df.Jumlah_Ulasan > 0]
    kor = None
    if len(bk) >= 3 and bk.Jumlah_Transaksi.std() > 0 and bk.Rating_Rata_rata.std() > 0:
        kor = float(bk.Jumlah_Transaksi.corr(bk.Rating_Rata_rata))
    if len(RT) >= 2:
        low = RT.index[0]
        top_dep = olah.agregat(df, "Outlet").pangsa.idxmax()
        judul = (f"{low}, outlet yang paling bergantung pada wisatawan, memiliki rating berbobot terendah"
                 if low == top_dep else f"{low} memiliki rating berbobot terendah ({dec(RT.rating.iloc[0], 2)})")
    elif len(RT) == 1:
        judul = f"Rating berbobot {RT.index[0]}: {dec(RT.rating.iloc[0], 2)}"
    else:
        judul = "Rating berbobot per outlet"
    sub = "Rating berbobot per outlet; sumbu tidak dimulai dari nol. Garis putus-putus: rata-rata pada filter ini."
    if kor is not None:
        sub += f" Korelasi jumlah transaksi–rating (baris berulasan): {dec(kor, 2)}."
    c = kartu(judul, sub, "Gambar 2.10 · G10")
    if len(RT) == 0:
        with c:
            st.info("Tidak ada ulasan pada filter ini.")
    else:
        lo_v, hi_v = RT.rating.min(), RT.rating.max()
        fig = go.Figure(go.Scatter(x=RT.rating, y=list(RT.index), mode="markers+text", text=[dec(v, 2) for v in RT.rating],
                                   textposition="middle right",
                                   marker=dict(size=15, color=[ORG if (i == 0 and len(RT) > 1) else GRY for i in range(len(RT))]),
                                   hovertemplate="%{y}: rating berbobot %{x:.2f} (%{customdata} ulasan)<extra></extra>",
                                   customdata=[nf(v) for v in RT.ulasan]))
        if K["rating"]:
            fig.add_vline(x=K["rating"], line_dash="dash", line_color="#8A94A3",
                          annotation_text=f"Rata-rata {dec(K['rating'], 2)}", annotation_position="top")
        fig.update_xaxes(range=[min(lo_v, K["rating"] or lo_v) - 0.15, max(hi_v, K["rating"] or hi_v) + 0.2],
                         title="Rating berbobot (sumbu tidak dimulai dari nol)", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(autorange="reversed", showgrid=False)
        with c:
            st.plotly_chart(rapi(fig, 110 + 62 * max(len(RT), 4), showlegend=False), use_container_width=True)
st.write("")

# ================================================================ catatan bawah
with st.expander("Panduan singkat penggunaan"):
    st.markdown(
        "1. Pilih Outlet, Kanal penjualan, Bulan, dan Jenis hari pada dropdown di atas. Kartu angka dan grafik ikut berubah.\n"
        "2. Baca kartu angka paling atas, lalu setiap judul grafik; judulnya adalah temuan pada filter yang dipilih.\n"
        "3. Warna oranye berarti wisatawan, biru berarti pelanggan lokal, abu-abu berarti netral. Label “Gambar 2.x · G#” "
        "menunjukkan grafik yang sama di laporan D3.\n"
        "4. G1, G8, dan G9 selalu menampilkan 12 bulan, sehingga tidak terpengaruh filter Bulan.\n"
        "5. Arahkan kursor atau sentuh titik, batang, dan sel untuk melihat angka tepat.\n"
        "6. Untuk mengganti sumber data, buka panel kiri (tanda panah di kiri atas).\n"
        "7. Bila muncul “Tidak ada data”, pilih “Semua” pada salah satu filter."
    )
with st.expander("Data hasil filter dan unduhan"):
    tampil = df.drop(columns=["Rating_x_Ulasan"]).copy()
    tampil["Tanggal"] = tampil.Tanggal.dt.strftime("%Y-%m-%d")
    tampil["Pekan"] = tampil.Pekan.dt.strftime("%Y-%m-%d")
    st.dataframe(tampil, use_container_width=True, height=280)
    st.download_button("Unduh CSV hasil filter", tampil.to_csv(index=False).encode("utf-8"),
                       file_name="data_hasil_filter.csv", mime="text/csv")
st.markdown(
    "**Rumus.** Rasio dihitung dari jumlah pembilang dan penyebut, bukan rata-rata rasio harian. "
    "Pangsa wisatawan = Σ Transaksi_Wisatawan ÷ Σ Jumlah_Transaksi. "
    "Rating berbobot = Σ(Rating × Jumlah_Ulasan) ÷ Σ Jumlah_Ulasan. "
    "Omzet bersih = omzet gudeg + omzet oleh-oleh − diskon.\n\n"
    "**Sumber dan batasan.** Data Simulasi Penjualan Gudeg Sekar Arum, Yogyakarta, 2025 (fiktif, hasil simulasi komputer). "
    "Tanggal libur nasional berupa perkiraan. Tidak ada data biaya, sehingga laba dan efektivitas kampanye tidak dapat dihitung. "
    "Korelasi pada G7 dan G10 tidak membuktikan sebab-akibat."
)
st.caption("Kelompok A · Visualisasi Data · Universitas Atma Jaya Yogyakarta · Semester Gasal 2026/2027")
