# B2B Dashboard (Streamlit Demo)
![Dashboard Preview](assets/dashboard_preview.png)

> **Demo con datos simulados** (Sucursal, Segmento, Canal, % habilitados y % facturación B2B).  
> Incluye filtros, KPIs con delta vs periodo anterior, gráficos y descargas CSV.

---

### ✨ Features
- Sidebar con filtros (Sucursal, Segmento, Canal) y **rango de meses**.
- **KPIs** con variación vs periodo anterior.
- **Gráficas**: Ventas mensuales, % B2B vs % habilitados.
- Vistas por **Segmento** y **Canal** (barras + tablas).
- **Descarga** de datos filtrados y resumen en CSV.
- **Autogenera** el dataset si no existe (`make_fake_data.py`).

---

## 🚀 Cómo usar (Codespaces o local)

### 1) Instalar dependencias
```bash
pip install -r requirements.txt
