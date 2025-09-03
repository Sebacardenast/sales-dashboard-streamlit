import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="B2B Dashboard (Demo)", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("data/b2b_talca_ficticio.csv")

st.title("Informe de Ventas - Embonor Planta Talca (Demo)")

# Cargar datos
df = load_data()
df["Mes"] = pd.to_datetime(df["Mes"])

# Filtros
col1, col2, col3 = st.columns(3)
suc = col1.selectbox("Sucursal", sorted(df["Sucursal"].unique()),
                     index=sorted(df["Sucursal"].unique()).index("TALCA") if "TALCA" in set(df["Sucursal"]) else 0)
seg = col2.multiselect("Segmento", df["Segmento"].unique(), default=["TRADICIONAL"])
can = col3.multiselect("Canal", df["Canal"].unique(), default=list(df["Canal"].unique()))

f = df[(df["Sucursal"] == suc) & (df["Segmento"].isin(seg)) & (df["Canal"].isin(can))].copy()

# KPIs (último mes disponible)
mes_max = f["Mes"].max()
f_mes = f[f["Mes"] == mes_max]
kpi1 = f_mes["$ TOTAL"].sum()
kpi2 = (f_mes["Habilitado B2B"].mean() * 100) if len(f_mes) > 0 else 0
kpi3 = (f_mes["$ FACT B2B"].sum() / f_mes["$ TOTAL"].sum() * 100) if f_mes["$ TOTAL"].sum() > 0 else 0

k1, k2, k3 = st.columns(3)
k1.metric("Ventas último mes (CLP)", f"{kpi1:,.0f}")
k2.metric("% Habilitados B2B (últ. mes)", f"{kpi2:,.1f}%")
k3.metric("% Facturación B2B (últ. mes)", f"{kpi3:,.1f}%")

# Series mensuales
serie = (f.groupby("Mes")
           .agg(total=("$ TOTAL", "sum"),
                fact_b2b=("$ FACT B2B", "sum"))
           .reset_index())
serie["pct_b2b"] = np.where(serie["total"] > 0, serie["fact_b2b"] / serie["total"] * 100, 0)

c1, c2 = st.columns(2)

with c1:
    st.subheader("Ventas mensuales (CLP)")
    fig = plt.figure()
    plt.plot(serie["Mes"], serie["total"])
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

with c2:
    st.subheader("% Facturación B2B")
    fig2 = plt.figure()
    plt.plot(serie["Mes"], serie["pct_b2b"])
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig2)

st.subheader("Tabla filtrada (primeros 1000 registros)")
st.dataframe(f.head(1000))
st.caption("Datos 100% simulados para fines demostrativos.")
