import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(7)
Path("data").mkdir(exist_ok=True)

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

df = pd.DataFrame(rows)
df.to_csv("data/b2b_talca_ficticio.csv", index=False)
print("OK -> data/b2b_talca_ficticio.csv")
