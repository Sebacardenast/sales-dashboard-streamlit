import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------- CONFIG ----------------
st.set_page_config(page_title="B2B Dashboard (Demo)", layout="wide")

# ------------- AUTOGENERAR DATA (sin subprocess) -------------
import os

DATA_PATH = "data/b2b_talca_ficticio.csv"
os.makedirs("data", exist_ok=True)

def generate_fake_data(path: str):
    rng = np.random.default_rng(7)

    sucursales = ["TALCA","CURICO","LINARES","PARRAL"]
    segmentos = ["TRADICIONAL","MAYORISTA","OTROS"]
    canales = ["MODERNO","KKAA","HORECA","TT_RESTO"]
    meses = pd.date_range("2024-01-01","2025-05-31",freq="M").strftime("%Y-%m")

    rows=[]
    for mes in meses:
        for suc in sucursales:
            for seg in segmentos:
                n = rng.integers(80, 160)
                habilitados = rng.choice([0,1], size=n, p=[0.4,0.6])
                total = rng.normal(240000, 90000, size=n).clip(0)
                factb = []
                for h,t in zip(habilitados,total):
                    pct = rng.uniform(0.2,0.6) if h else rng.uniform(0,0.15)
                    factb.append(t*pct)
                for i in range(n):
                    rows.append({
                        "Sucursal": suc,
                        "Segmento": seg,
                        "Canal": rng.choice(canales),
                        "Mes": mes,
                        "$ TOTAL": round(float(total[i]),2),
                        "Habilitado B2B": int(habilitados[i]),
                        "$ FACT B2B": round(float(factb[i]),2)
                    })
    df_gen = pd.DataFrame(rows)
    df_gen.to_csv(path, index=False)

if not os.path.exists(DATA_PATH):
    generate_fake_data(DATA_PATH)


# ------------- LOAD DATA (cache) -------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["Mes"] = pd.to_datetime(df["Mes"])
    return df

def format_money(x: float) -> str:
    return f"${x:,.0f}"

def safe_pct_change(curr, prev):
    if prev is None or np.isnan(prev) or prev == 0:
        return 0.0
    return (curr - prev) / prev * 100.0

df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Filtros")

sucursales = sorted(df["Sucursal"].unique())
segmentos = sorted(df["Segmento"].unique())
canales = sorted(df["Canal"].unique())

suc = st.sidebar.selectbox(
    "Sucursal",
    sucursales,
    index=sucursales.index("TALCA") if "TALCA" in sucursales else 0
)
seg = st.sidebar.multiselect("Segmento", segmentos, default=["TRADICIONAL"])
can = st.sidebar.multiselect("Canal", canales, default=canales)

# ---- Slider con tipos nativos (date) ----
min_m_ts = df["Mes"].min()
max_m_ts = df["Mes"].max()
min_m = min_m_ts.to_pydatetime().date()
max_m = max_m_ts.to_pydatetime().date()

# por defecto últimos ~6 meses
start_default_ts = (max_m_ts.replace(day=1) - pd.offsets.MonthBegin(5))
start_default = start_default_ts.to_pydatetime().date()

rango = st.sidebar.slider(
    "Rango de meses",
    min_value=min_m,
    max_value=max_m,
    value=(start_default, max_m),
    format="YYYY-MM",
)

# Convertir rango (date) -> Timestamps para filtrar
r0 = pd.to_datetime(rango[0])
r1 = pd.to_datetime(rango[1])

# ---------------- FILTRO ----------------
mask = (
    (df["Sucursal"] == suc) &
    (df["Segmento"].isin(seg)) &
    (df["Canal"].isin(can)) &
    (df["Mes"].between(r0, r1))
)
f = df.loc[mask].copy()

st.title(f"Informe B2B — {suc} (Demo)")
st.caption("Datos 100% simulados para fines demostrativos.")

if f.empty:
    st.warning("No hay datos para los filtros seleccionados. Ajusta el rango o las opciones.")
    st.stop()

# --------- PERIODO ACTUAL vs ANTERIOR (para deltas) ----------
# tamaño de ventana en meses
window = (r1.to_period("M") - r0.to_period("M")).n + 1
prev_end = (r0 - pd.offsets.MonthEnd(1))
prev_start = (prev_end - pd.offsets.MonthBegin(window - 1))

mask_prev = (
    (df["Sucursal"] == suc) &
    (df["Segmento"].isin(seg)) &
    (df["Canal"].isin(can)) &
    (df["Mes"].between(prev_start, prev_end))
)
f_prev = df.loc[mask_prev].copy()

# KPIs actuales
kpi_total = f["$ TOTAL"].sum()
kpi_hab = f["Habilitado B2B"].mean() * 100
kpi_b2b_pct = (f["$ FACT B2B"].sum() / f["$ TOTAL"].sum()) * 100 if f["$ TOTAL"].sum() > 0 else 0

# KPIs previos (para delta)
kpi_total_prev = f_prev["$ TOTAL"].sum() if not f_prev.empty else np.nan
kpi_hab_prev = (f_prev["Habilitado B2B"].mean() * 100) if not f_prev.empty else np.nan
kpi_b2b_pct_prev = (f_prev["$ FACT B2B"].sum() / f_prev["$ TOTAL"].sum() * 100) if (not f_prev.empty and f_prev["$ TOTAL"].sum() > 0) else np.nan

# ---------------- KPI CARDS ----------------
c1, c2, c3 = st.columns(3)
c1.metric("Ventas (periodo)", format_money(kpi_total), f"{safe_pct_change(kpi_total, kpi_total_prev):+.1f}%")
c2.metric("% Habilitados", f"{kpi_hab:,.1f}%", f"{safe_pct_change(kpi_hab, kpi_hab_prev):+.1f}%")
c3.metric("% Facturación B2B", f"{kpi_b2b_pct:,.1f}%", f"{safe_pct_change(kpi_b2b_pct, kpi_b2b_pct_prev):+.1f}%")

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📈 Overview", "🧩 Segmento/Canal", "📥 Exportar / Tabla"])

# ----- TAB 1: OVERVIEW -----
with tab1:
    serie = (f.groupby("Mes")
               .agg(total=("$ TOTAL", "sum"),
                    fact_b2b=("$ FACT B2B", "sum"),
                    hab=("Habilitado B2B", "mean"))
               .reset_index()
               .sort_values("Mes"))
    serie["pct_b2b"] = np.where(serie["total"] > 0, serie["fact_b2b"] / serie["total"] * 100, 0)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Ventas mensuales (CLP)")
        fig = plt.figure()
        plt.plot(serie["Mes"], serie["total"])
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

    with col_b:
        st.subheader("% B2B vs % Habilitados (mensual)")
        fig2 = plt.figure()
        plt.plot(serie["Mes"], serie["pct_b2b"], label="% B2B")
        plt.plot(serie["Mes"], serie["hab"] * 100, label="% Habilitados")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)

# ----- TAB 2: SEGMENTO / CANAL -----
with tab2:
    col1, col2 = st.columns(2)

    # Por Segmento
    total_periodo = f["$ TOTAL"].sum()
    by_seg = (f.groupby("Segmento")
                .agg(total=("$ TOTAL", "sum"),
                     pct_b2b=("$ FACT B2B", lambda s: 100 * s.sum() / total_periodo if total_periodo else 0),
                     hab=("Habilitado B2B", "mean"))
                .reset_index()
                .sort_values("total", ascending=False))

    with col1:
        st.subheader("Ventas por Segmento")
        fig3 = plt.figure()
        plt.bar(by_seg["Segmento"], by_seg["total"])
        plt.xticks(rotation=20)
        plt.tight_layout()
        st.pyplot(fig3)

        df_seg_show = by_seg.rename(columns={"total": "Ventas", "pct_b2b": "% B2B", "hab": "% Habilitados"})\
                             .assign(**{"% Habilitados": lambda x: (x["% Habilitados"] * 100).round(1),
                                        "% B2B": lambda x: x["% B2B"].round(1)})
        st.dataframe(df_seg_show.style.format({"Ventas": "{:,.0f}"}), use_container_width=True)

    # Por Canal
    by_can = (f.groupby("Canal")
                .agg(total=("$ TOTAL", "sum"),
                     pct_b2b=("$ FACT B2B", lambda s: 100 * s.sum() / total_periodo if total_periodo else 0))
                .reset_index()
                .sort_values("total", ascending=False))

    with col2:
        st.subheader("Ventas por Canal")
        fig4 = plt.figure()
        plt.bar(by_can["Canal"], by_can["total"])
        plt.xticks(rotation=20)
        plt.tight_layout()
        st.pyplot(fig4)

        df_can_show = by_can.rename(columns={"total": "Ventas", "pct_b2b": "% B2B"})\
                             .assign(**{"% B2B": lambda x: x["% B2B"].round(1)})
        st.dataframe(df_can_show.style.format({"Ventas": "{:,.0f}"}), use_container_width=True)

# ----- TAB 3: EXPORT / TABLA -----
with tab3:
    st.subheader("Tabla filtrada")
    st.dataframe(f.sort_values("Mes", ascending=False).head(2000), use_container_width=True)

    resumen = (f.groupby(["Mes", "Segmento", "Canal"])
                 .agg(total=("$ TOTAL", "sum"),
                      fact_b2b=("$ FACT B2B", "sum"),
                      hab=("Habilitado B2B", "mean"))
                 .reset_index()
                 .assign(pct_b2b=lambda x: np.where(x["total"] > 0, x["fact_b2b"] / x["total"] * 100, 0),
                         pct_hab=lambda x: x["hab"] * 100))

    csv_full = f.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar datos filtrados (CSV)", data=csv_full,
                       file_name="b2b_filtrado.csv", mime="text/csv")

    csv_res = resumen.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar resumen (CSV)", data=csv_res,
                       file_name="b2b_resumen.csv", mime="text/csv")

