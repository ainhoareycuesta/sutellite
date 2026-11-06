# Sutellite â€” Canonical Observation Schema

**Status:** Draft v1
**Scope:** Cleaned and harmonised active-fire observations
**Dataset:** NASA FIRMS MODIS and VIIRS
**Current focus:** Accurate availability and harmonisation of source observations

---

## 1. Purpose

This document defines the canonical structure used by Sutellite to represent individual MODIS and VIIRS active-fire observations.

The schema must preserve:

- Original NASA measurements and their scientific meanings.
- Sensor-specific differences.
- Acquisition time and geographic information.
- Source provenance and processing history.
- Data validation results and quality flags.

Harmonisation must not create false equivalence between measurements from different sensors.

Raw NASA files must remain unchanged.

## 2. Source products and provenance

Sutellite uses data downloaded through NASA FIRMS Archive Download.

Two source streams are present:

| Source stream | Description |
|---|---|
| ARCHIVE | Standard-quality historical observations distributed through NASA FIRMS |
| NRT | Near-real-time observations distributed through NASA FIRMS |

ARCHIVE observations replace corresponding NRT observations as standard-quality products become available.

The original source stream must remain identifiable in every processed record.

### 2.1 Source collections and filename identifiers

| Sensor/platform | Collection |
|---|---|
| MODIS Terra/Aqua | MODIS Collection 6.1 |
| VIIRS S-NPP | VIIRS Collection 2 |
| VIIRS NOAA-20 | VIIRS Collection 2 |
| VIIRS NOAA-21 | VIIRS Collection 2 |

The original FIRMS filename contains a product identifier. This identifier must be preserved exactly as it appears in the filename.

Examples observed in this dataset:

- MODIS: `M-C61`
- VIIRS NOAA-20: `J1V-C2`

The source collection and original filename identifier must be stored separately.

Do not substitute underlying product-family identifiers for the original FIRMS filename identifier.

### 2.2 Provenance fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| observation_id | String | No | Deterministic identifier for a source record |
| region | String | No | Study region |
| sensor | String | No | MODIS or VIIRS |
| platform | String | No | Normalised satellite platform |
| satellite_raw | String | No | Original satellite field value |
| instrument_raw | String | No | Original instrument field value |
| processing_stream | String | No | ARCHIVE or NRT |
| distribution_service | String | No | NASA FIRMS |
| source_collection | String | No | MODIS_C6.1 or VIIRS_C2 |
| source_product_token_raw | String | No | Exact product identifier from original filename |
| source_file | String | No | Original relative source filename |
| source_record_index | Int64 | No | One-based data-record index within the source file |
| firms_version_raw | String | No | Original version field value |

`observation_id` must be deterministic and traceable to the source record. It must not depend on the absolute path of a user's computer.

`source_file` must use a relative path, not a machine-specific absolute path.

`firms_version_raw` must preserve the original value. Do not assume that it independently identifies the software revision of the underlying product.

Do not assign a processing centre unless it is explicitly established by the relevant NASA product documentation.

## 3. Geographic fields

| Field | Type | Unit / CRS | Nullable |
|---|---|---|---|
| latitude_deg | Float64 | Decimal degrees, WGS 84 | No |
| longitude_deg | Float64 | Decimal degrees, WGS 84 | No |

The source geographic reference system is WGS 84 (EPSG:4326).

Coordinates must:

- Preserve their original numerical values.
- Not be rounded during harmonisation.
- Remain in geographic coordinates in the scientific dataset.

Projection into EPSG:3857 is for web-map rendering only.

Metric calculations must use appropriate geodesic calculations or suitable projected coordinate systems.

## 4. Acquisition time fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| acq_date | Date | No | Acquisition date |
| acq_time_raw | String | No | Original acquisition-time token |
| acq_time_hhmm_utc | String | No | Normalised four-character HHMM value |
| acq_datetime_utc | Datetime[UTC] | No | Combined UTC timestamp |

NASA FIRMS acquisition time is supplied in UTC, using hours and minutes (HHMM).

Some CSV values do not contain leading zeros. For example:

- Raw value: `410`
- Normalised value: `0410`
- Timestamp component: 04:10 UTC

Seconds must be set to zero because the source does not provide second-level acquisition precision.

The original time token must be retained.

Invalid time values must be flagged rather than silently corrected.

## 5. Scientific measurements

All numerical measurements are stored using Float64 in the harmonised dataset.

This is a storage decision. It does not imply greater measurement accuracy than the source product provides.

### 5.1 Brightness temperatures

| Canonical field | MODIS source | VIIRS source | Unit |
|---|---|---|---|
| modis_bt21_22_k | brightness | â€” | K |
| modis_bt31_k | bright_t31 | â€” | K |
| viirs_bt_i4_k | â€” | brightness | K |
| viirs_bt_i5_k | â€” | bright_t31 | K |

MODIS brightness measurements represent Band 21/22 and Band 31 brightness temperatures.

VIIRS fire-pixel brightness measurements represent I4 and I5 brightness temperatures.

All are expressed in Kelvin.

**VIIRS export-name note:**

The downloaded VIIRS CSV files use `brightness` and `bright_t31` as column names.

NASA's VIIRS product documentation identifies the corresponding fire-pixel brightness measurements as I4 and I5. The FIRMS VIIRS attribute documentation uses `Bright_ti4` and `Bright_ti5` terminology, with alternative service names in some interfaces.

The proposed mapping is:

- `brightness` â†’ I4
- `bright_t31` â†’ I5

The original raw column names must always be preserved in source metadata.

The raw name `bright_t31` must not be interpreted as meaning that VIIRS has a MODIS Band 31 measurement.

This mapping must be checked against the exact FIRMS Archive Download product specification and covered by schema tests before production processing.

Brightness measurements from different spectral channels must never be treated as interchangeable.

### 5.2 Fire Radiative Power

| Field | Source field | Type | Unit |
|---|---|---|---|
| frp_mw | frp | Float64 | MW |

FRP represents pixel-integrated Fire Radiative Power.

MODIS and VIIRS FRP values must retain their sensor identity. Their retrieval methods are not assumed to be identical.

Negative FRP observations must be retained and flagged.

They must not be replaced with zero.

Null FRP values must remain null.

Negative FRP observations are excluded from FRP-based calculations by default, but remain available for inspection.

### 5.3 Pixel dimensions

| Field | Source field | Type | Unit |
|---|---|---|---|
| scan_km | scan | Float64 | km |
| track_km | track | Float64 | km |

These fields describe actual pixel dimensions along the scan and track directions.

They must not be replaced by nominal sensor-resolution constants.

Nominal resolution belongs in the sensor metadata table.

## 6. Sensor-specific metadata

### 6.1 Confidence

| Field | Type | Sensor | Description |
|---|---|---|---|
| confidence_raw | String | All | Original confidence value |
| confidence_system | String | All | Confidence methodology |
| confidence_modis_percent | Float64 | MODIS | MODIS confidence percentage |
| confidence_viirs_class | String | VIIRS | VIIRS confidence category |

MODIS confidence uses a numeric scale from 0 to 100.

VIIRS confidence uses:

- `l` â€” low
- `n` â€” nominal
- `h` â€” high

The two confidence systems must remain separate.

No conversion to a common confidence score is permitted without a separately justified and documented methodology.

### 6.2 Detection type

| Field | Type | Nullable | Description |
|---|---|---|---|
| detection_type_code | Int8 | Yes | Original NASA detection-type code |

Documented values:

| Code | Description |
|---|---|
| 0 | Presumed vegetation fire |
| 1 | Active volcano |
| 2 | Other static land source |
| 3 | Offshore detection |

Detection type is not confirmation that an observation is a wildfire.

The field is structurally absent from NRT files in this dataset. Its harmonised value must therefore be null for those records.

NASA has documented a Type-field inconsistency in older VIIRS standard-product software versions.

The original CSV version field does not independently identify that software revision.

Consequently, retain the raw type code and its provenance, but do not treat it as verified ground truth without checking the applicable product documentation.

### 6.3 Day/night

| Field | Type | Values |
|---|---|---|
| daynight | String | D, N |

- `D` â€” daytime observation
- `N` â€” nighttime observation

### 6.4 Product version

`firms_version_raw` preserves the source version exactly.

Examples observed in this dataset include:

- MODIS ARCHIVE: `6.03`, `61.03`
- MODIS NRT: `6.1NRT`
- VIIRS ARCHIVE: `2`
- VIIRS NRT: `2.0NRT`

Do not silently normalise, reinterpret or discard these values.

## 7. Nominal sensor metadata

Nominal resolution is maintained in a separate sensor/product metadata table rather than repeated in every observation.

| Sensor/platform | Nominal spatial resolution |
|---|---:|
| MODIS Terra | 1,000 m |
| MODIS Aqua | 1,000 m |
| VIIRS S-NPP | 375 m |
| VIIRS NOAA-20 | 375 m |
| VIIRS NOAA-21 | 375 m |

These values describe nominal resolution, not the actual dimensions of every detected pixel.

Actual dimensions are retained in `scan_km` and `track_km`.

Pixel footprints must eventually account for sensor-specific geometry, scan position and pixel dimensions. They must not be approximated as identical fixed-size squares.

## 8. Data quality fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| validation_status | String | No | Project validation result |
| validation_flags | List[String] | No | Specific validation anomalies |

`validation_status` describes whether a record passes Sutellite's validation rules. It does not establish whether the detected hotspot is a real fire.

Example validation flags:

- `negative_frp`
- `invalid_coordinates`
- `invalid_timestamp`
- `invalid_confidence`
- `invalid_detection_type`

Negative FRP records remain available in the dataset and on the map.

They are excluded from FRP-based calculations by default, but users must be able to inspect them.

Validation rules must distinguish between invalid observations and observations that are scientifically unusual but still worth retaining.

## 9. Nullability rules

Missing values must not be invented or silently replaced.

The following distinctions must be preserved:

1. **Structurally unavailable field:** The source product does not provide the field, such as `type` in NRT files.

2. **Missing observation value:** The source product provides the field, but an individual record has no value.

3. **Not applicable:** The field does not apply to that sensor or product.

Where feasible, the reason for a null value must be recorded in processing metadata.

Do not:

- Replace missing FRP with zero.
- Invent confidence values.
- Invent detection-type values.
- Delete otherwise usable observations solely because an optional field is missing.

## 10. Record identity and duplicates

Every source record must remain traceable to its original file and record position.

Exact duplicate detection is a separate processing operation.

Records must not be considered duplicates merely because their coordinates and timestamps are close.

Detections from different satellites remain separate measurements.

Clustering detections into candidate fire events is outside the scope of this schema version.

Original individual detections must remain available even if clustering is introduced later.

## 11. Data types and storage

| Data category | Storage type |
|---|---|
| Coordinates and scientific measurements | Float64 |
| Record index | Int64 |
| Detection type | Int8 |
| Acquisition date | Date |
| Acquisition timestamp | Datetime with UTC timezone |
| Categories and provenance | String |
| Validation flags | List[String] |

The primary processed storage format is Parquet.

Processing must be performed incrementally or in chunks. The complete raw dataset must never be loaded into memory at once.

Original CSV files must remain unchanged.

Parquet partitioning should use useful dimensions such as region and year, while avoiding excessive numbers of small files.

## 12. Dataset layers

Sutellite distinguishes three conceptual data layers:

1. **Cleaned observations:** Validated records, source provenance and quality flags.
2. **Harmonised observations:** Common schema, standardised timestamps and field representations while preserving sensor-specific measurements.
3. **Derived datasets:** Future clusters, spatial statistics and AI predictions.

The current implementation covers the first two layers.

AI training, prediction and event clustering are outside the current implementation scope.

## 13. Out-of-scope functionality

This schema version does not define:

- AI training datasets.
- AI predictions.
- Predicted historical detections.
- Verified fire-event records.
- Final event-clustering algorithms.
- Emissions estimates.

These may be developed as separate derived datasets later.

## 14. NASA references

1. [NASA FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/)

2. [NASA FIRMS Archive README](https://nrt3.modaps.eosdis.nasa.gov/archive/FIRMS/README.pdf)

3. [NASA FIRMS MODIS attributes](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html)

4. [NASA FIRMS VIIRS attributes](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html)

5. [VIIRS Collection 2 375-m Active Fire Product User Guide](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.0.pdf)

6. [MODIS Collection 6 and 6.1 Active Fire Product User Guide](https://www.earthdata.nasa.gov/s3fs-public/2023-09/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf)

7. [NASA FIRMS Data Ingest Tutorial](https://firms.modaps.eosdis.nasa.gov/content/academy/data_ingest/firms_data_ingest.html)
