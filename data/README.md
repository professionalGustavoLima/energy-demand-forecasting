# Data Pipeline Overview

## Source and Retrieval

**API**: [ONS API](https://apicarga.ons.org.br/prd/cargaprogramada) (Agência Nacional de Energia Elétrica - Cargas Programadas)

**Regions fetched**: `SECO`, `N`, `NE`, `S` (Brazilian electricity load regions)

**Date range**: 2025-01-01 to 2026-06-30 in API calls; pipeline designed for 2020-01-01 to 2026-06-30

## Retrieval Format

JSON responses from region-specific endpoints, formatted as pandas DataFrames. Each call appends `&cod_areacarga={CODE}` to the base URL:

```
https://apicarga.ons.org.br/prd/cargaprogramada?dat_inicio=2025-01-01&dat_fim=2026-06-30&cod_areacarga={REGION}
```

## Processing and Output

**Concatenation**: Regional DataFrames concatenated into `df_final` via pandas `.concat()` (ignore_index=True)

**Output format**: Parquet file at `energy-demand-forecasting/data/raw/raw_data.parquet`

---

*Pipeline: Python requests + pandas → ONS Carga Programada API JSON response → parquet*
