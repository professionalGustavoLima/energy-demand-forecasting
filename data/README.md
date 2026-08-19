# Data Pipeline Overview

The data pipeline retrieves scheduled electricity load data from the ONS API and transforms it into a trusted dataset.

## 1. Raw Data — `01_raw`

### Source and Retrieval

**API:** [ONS Carga Programada API](https://apicarga.ons.org.br/prd/cargaprogramada)

**Load areas:**

* `SECO` — Southeast/Central-West
* `N` — North
* `NE` — Northeast
* `S` — South

**Date range:** `2020-01-01` to `2026-06-30`

### API Requests

The extraction is performed by `ONSDataloader` in:

`data/01_raw/load_data.py`

The requested period is divided into **6-month intervals** to retrieve the data.

Each API request is specific to one load area and one date interval:

```text
https://apicarga.ons.org.br/prd/cargaprogramada
    ?dat_inicio={START_DATE}
    &dat_fim={END_DATE}
    &cod_areacarga={LOAD_CODE}
```

The API response is returned as JSON and converted into a pandas DataFrame.

### Retry Strategy

Each API request supports:

* Maximum of `3` attempts
* Request timeout of `60` seconds
* `5` seconds between failed attempts

If all attempts fail, the pipeline raises a `RuntimeError`.

### Raw Data Consolidation

Data retrieved from all load areas and time intervals is concatenated into a single DataFrame using:

```python
pd.concat(dataframes, ignore_index=True)
```

The resulting raw dataset is saved as:

`data/01_raw/raw_data.parquet`

---

## 2. Trusted Data — `02_trusted`

### Transformation

The raw data is transformed by `ONSTrustedData` in:

`data/02_trusted/transform_data.py`

The transformation consists of two main steps:

1. Convert the dataset from **long format to wide format**.
2. Rename columns according to the trusted data schema.

### Long to Wide Transformation

The raw dataset contains one row per load area and timestamp.

The data is pivoted using:

* `dat_referencia`
* `din_referenciautc`
* `cod_areacarga`
* `val_cargaglobalprogramada`

The resulting structure contains one column for each load area.

### Column Mapping

| Raw Column          | Trusted Column                               |
| ------------------- | -------------------------------------------- |
| `dat_referencia`    | `ref_date`                                   |
| `din_referenciautc` | `ref_datetime`                               |
| `N`                 | `north_scheduled_load_mwmed`                 |
| `NE`                | `northeast_scheduled_load_mwmed`             |
| `S`                 | `south_scheduled_load_mwmed`                 |
| `SECO`              | `southeast_centralwest_scheduled_load_mwmed` |

The resulting trusted dataset is saved as:

`data/02_trusted/trusted_data.parquet`

---

## Pipeline Flow

```text
ONS Carga Programada API
          │
          ▼
   JSON API responses
          │
          ▼
     Raw DataFrame
          │
          ▼
data/01_raw/raw_data.parquet
          │
          ▼
    Long → Wide
          │
          ▼
    Column Mapping
          │
          ▼
data/02_trusted/trusted_data.parquet
```

---

## Output Structure

```text
data/
├── 01_raw/
│   ├── load_data.py
│   └── raw_data.parquet
│
├── 02_trusted/
│   ├── transform_data.py
│   └── trusted_data.parquet
│
└── README.md
```

---

*Pipeline: ONS API → Raw Data → Long-to-Wide Transformation → Trusted Data*