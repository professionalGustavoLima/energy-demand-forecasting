import requests
import pandas as pd

load_code = ["SECO", "N", "NE", "S"]
start_date = "2020-01-01"
end_date = "2026-06-30"

url = "https://apicarga.ons.org.br/prd/cargaprogramada?dat_inicio=2025-01-01&dat_fim=2026-06-30&cod_areacarga="
dfs = []

for code in load_code:
    response = requests.get(url+f"{code}")
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    dfs.append(df)

df_final = pd.concat(dfs, ignore_index=True)
df_final.to_parquet("energy-demand-forecasting/data/raw/raw_data.parquet")
print(df_final)