# Sutellite — Canonical Observation Schema

**Document status:** Draft v1.1
**Last reviewed:** 2026-11-07
**Scope:** Cleaned and harmonised active-fire observations
**Dataset:** NASA FIRMS MODIS and VIIRS
**Implementation status:** Schema and processing rules defined; harmonisation implementation pending

---

## 1. Purpose

This document defines the canonical data model for Sutellite's MODIS and VIIRS active-fire observations.

The objective is to make observations from different satellites and processing streams available through a consistent data structure without erasing sensor-specific information or creating false equivalences between measurements.

The schema must:

- Preserve the original NASA FIRMS observations and their provenance.
- Standardise field names, data types, timestamps and geographic representation.
- Preserve sensor-specific measurement meanings and confidence systems.
- Distinguish ARCHIVE and NRT processing.
- Retain observations with identifiable data-quality anomalies.
- Support accurate geographic analysis and web-map visualisation.
- Remain suitable for future scientific analysis.

**NASA documentation takes precedence over project preferences.** Units, field meanings, product conventions and measurement interpretation must follow the relevant NASA product documentation. Any necessary transformation must be documented and reproducible.

This document is a draft specification. A field mapping marked provisional must not be treated as a fully verified scientific equivalence.

## 2. Dataset scope and inventory

### 2.1 Source

Sutellite uses active-fire observations downloaded through NASA FIRMS Archive Download.

The dataset includes:

- MODIS Collection 6.1.
- VIIRS Collection 2, 375 m, from Suomi-NPP.
- VIIRS Collection 2, 375 m, from NOAA-20.
- VIIRS Collection 2, 375 m, from NOAA-21.

Eight study regions are included:

| Region ID | Source directory |
|---|---|
| `angola` | `angola` |
| `brasil` | `brasil` |
| `rdc` | `rdc` |
| `zambia` | `zambia` |
| `california` | `california` |
| `espana` | `espana` |
| `indonesia` | `indonesia` |
| `australia` | `australia` |

Each region contains four sensor configurations:

1. MODIS.
2. VIIRS NOAA-20.
3. VIIRS NOAA-21.
4. VIIRS S-NPP.

Each sensor-region combination contains one ARCHIVE CSV and one NRT CSV.

| Dataset property | Observed value |
|---|---:|
| Study regions | 8 |
| Sensor-region combinations | 32 |
| CSV files | 64 |
| ARCHIVE files | 32 |
| NRT files | 32 |
| Total raw observations | 231,359,744 |
| Approximate raw data size | 17.45 GB |

The observation count represents source records, not unique fire events or individual real-world fires.

### 2.2 Observed source inventory

The following counts and date ranges were obtained during the initial full dataset inspection.

| Sensor and stream | Observations | First date | Last date |
|---|---:|---|---|
| MODIS ARCHIVE | 42,459,960 | 2000-11-01 | 2026-08-31 |
| MODIS NRT | 353,938 | 2026-09-01 | 2026-11-04 |
| NOAA-20 ARCHIVE | 56,991,138 | 2018-04-01 | 2026-07-31 |
| NOAA-20 NRT | 3,227,043 | 2026-08-01 | 2026-11-04 |
| NOAA-21 ARCHIVE | 23,268,163 | 2023-03-01 | 2026-07-31 |
| NOAA-21 NRT | 3,135,990 | 2026-08-01 | 2026-11-04 |
| S-NPP ARCHIVE | 98,814,015 | 2012-01-20 | 2026-07-31 |
| S-NPP NRT | 3,109,497 | 2026-08-01 | 2026-11-02 |
| **Total** | **231,359,744** | | |

These are inventory results for the currently downloaded dataset, not permanent NASA coverage limits. They must be regenerated when the source data is updated.

### 2.3 ARCHIVE and NRT

Two processing streams are present:

| Stream | Meaning |
|---|---|
| `ARCHIVE` | Standard-quality historical observations. |
| `NRT` | Near-real-time observations intended for lower-latency access. |

The NASA FIRMS Archive README identifies the standard-quality `fire_archive` MODIS and VIIRS products as processed by the University of Maryland and distributed through FIRMS. It identifies the NRT products as processed by NASA LANCE/FIRMS.

The README describes an approximately three-month processing lag for standard-quality archive products. The current FIRMS Archive Download page describes replacement of NRT data by standard science-quality data with an approximately five-month lag. This difference demonstrates that the lag is not a fixed rule.

Consequently:

- ARCHIVE is the preferred historical source where standard-quality coverage exists.
- NRT supplies recent observations not yet represented in ARCHIVE.
- The actual coverage boundary must be determined from the files and source metadata.
- The pipeline must not hardcode a universal replacement date or a fixed processing delay.
- ARCHIVE and NRT must never be blindly concatenated.

Every processed observation must preserve its original processing stream.

## 3. Product and sensor identification

### 3.1 Collection identifiers

| Sensor | Platform | Collection |
|---|---|---|
| MODIS | Terra | Collection 6.1 |
| MODIS | Aqua | Collection 6.1 |
| VIIRS | Suomi-NPP | Collection 2 |
| VIIRS | NOAA-20 | Collection 2 |
| VIIRS | NOAA-21 | Collection 2 |

The collection is identified using the source product and filename, not solely through the `version` field.

### 3.2 Observed filename tokens

Examples from the downloaded dataset:

| Sensor/platform | Observed token |
|---|---|
| MODIS | `M-C61` |
| VIIRS S-NPP | `SV-C2` |
| VIIRS NOAA-20 | `J1V-C2` |
| VIIRS NOAA-21 | `J2V-C2` |

The complete filename must be retained in provenance.

Do not assume that every NASA documentation example uses exactly the same filename convention as the regional Archive Download files.

### 3.3 Satellite and instrument identification

The raw `satellite` and `instrument` fields must be preserved.

Observed platform identifiers include:

| Raw satellite value | Canonical platform |
|---|---|
| `Terra` | `TERRA` |
| `Aqua` | `AQUA` |
| `SNPP` | `SNPP` |
| `N20` | `NOAA-20` |
| `N21` | `NOAA-21` |

The raw `instrument` field distinguishes:

- `MODIS`
- `VIIRS`

For VIIRS, the platform identifier is needed to distinguish S-NPP, NOAA-20 and NOAA-21.

Do not infer the platform from `instrument` alone.

### 3.4 Product processing provenance

The following source distinctions must be represented:

| Provenance field | ARCHIVE | NRT |
|---|---|---|
| Distribution service | NASA FIRMS | NASA FIRMS |
| Processing provider | University of Maryland | NASA LANCE/FIRMS |
| Processing stream | `ARCHIVE` | `NRT` |
| Quality category | Standard quality | Near-real-time |

These values describe the product processing described by NASA's Archive README. They must not be replaced with a generic processing-centre label.

## 4. Raw CSV schemas

### 4.1 ARCHIVE

All inspected ARCHIVE CSV files contain 15 columns:

```text
latitude
longitude
brightness
scan
track
acq_date
acq_time
satellite
instrument
confidence
version
bright_t31
frp
daynight
type
```

### 4.2 NRT

All inspected NRT CSV files contain 14 columns:

```text
latitude
longitude
brightness
scan
track
acq_date
acq_time
satellite
instrument
confidence
version
bright_t31
frp
daynight
```

The `type` column is absent from the inspected NRT product files.

This is a structural product-schema difference, not an individual missing observation value.

The pipeline must not invent a `type` value for NRT observations.

### 4.3 Raw data preservation

Raw source CSV files are immutable input data.

The processing pipeline must:

- Never overwrite raw CSV files.
- Never change their column names.
- Never round or rewrite source values.
- Preserve source file identity and record position.
- Keep provenance sufficient to trace every processed observation back to its original source row.

The canonical schema is a processing representation, not a replacement for the original source data.

## 5. Canonical schema

### 5.1 General conventions

Canonical field names use lowercase `snake_case`.

Numeric scientific fields are stored as `Float64` in the harmonised representation unless a field has a more appropriate integer or categorical type.

Using `Float64` is a project storage decision. It does not imply that the original instrument measurements have `Float64` accuracy.

Original numerical values and their available decimal precision must be preserved. Do not round measurements for visual convenience.

### 5.2 Identity and provenance fields

| Canonical field | Type | Nullable | Description |
|---|---|---|---|
| `observation_id` | String | No | Stable identifier for one source observation record. |
| `region_id` | String | No | Canonical study-region identifier. |
| `sensor` | String | No | `MODIS` or `VIIRS`. |
| `platform` | String | No | `TERRA`, `AQUA`, `SNPP`, `NOAA-20` or `NOAA-21`. |
| `satellite_raw` | String | No | Original source `satellite` value. |
| `instrument_raw` | String | No | Original source `instrument` value. |
| `processing_stream` | String | No | `ARCHIVE` or `NRT`. |
| `distribution_service` | String | No | `NASA_FIRMS`. |
| `processing_provider` | String | No | `UNIVERSITY_OF_MARYLAND` or `NASA_LANCE_FIRMS`. |
| `source_collection` | String | No | Canonical collection identifier, such as `MODIS_C61` or `VIIRS_C2`. |
| `source_product_token_raw` | String | No | Original filename product token, e.g. `M-C61` or `J1V-C2`. |
| `source_file` | String | No | Relative path to the source CSV. |
| `source_record_index` | UInt64 | No | One-based data-record index, excluding the CSV header. |
| `firms_version_raw` | String | No | Original source `version` value. |

`observation_id` must identify a source record, not a real-world fire.

A deterministic identifier may be generated from the source file identifier and one-based source record index. It must remain stable across repeated processing of the same source snapshot.

`source_record_index` counts data rows only. The header row is not record 1.

### 5.3 Geographic fields

| Canonical field | Type | Nullable | Unit / reference |
|---|---|---|---|
| `latitude_deg` | Float64 | No | Decimal degrees, WGS 84. |
| `longitude_deg` | Float64 | No | Decimal degrees, WGS 84. |

NASA FIRMS supplies the observations in the WGS 84 geographic coordinate system.

Canonical CRS:

```text
EPSG:4326
```

Coordinates represent the centre of the nominal fire pixel. They do not necessarily identify the precise physical location of the fire.

The original coordinate values must be preserved without rounding.

### 5.4 Time fields

| Canonical field | Type | Nullable | Description |
|---|---|---|---|
| `acq_date` | Date | No | Original acquisition date. |
| `acq_time_raw` | String | No | Original CSV acquisition-time value. |
| `acq_time_hhmm_utc` | String | No | Normalised four-character UTC time. |
| `acq_datetime_utc` | Timestamp | No | Combined UTC date and time. |

NASA FIRMS acquisition time is provided in UTC using hours and minutes (`HHMM`).

The normalisation process must:

1. Preserve the original value as `acq_time_raw`.
2. Interpret it as hours and minutes, not as a decimal number.
3. Pad a leading zero when necessary.
4. Validate that the parsed hour and minute are valid.
5. Construct the combined timestamp in UTC.

Example:

```text
acq_date:          2026-08-04
acq_time_raw:      410
acq_time_hhmm_utc: 0410
acq_datetime_utc:  2026-08-04T04:10:00Z
```

The seconds component is set to `00` because the source acquisition time is supplied at minute precision. It must not be interpreted as a measured second.

Invalid time values must be flagged rather than silently corrected.

### 5.5 Brightness-temperature fields

Brightness temperatures are sensor-specific measurements. Similar field names do not imply identical spectral channels.

| Canonical field | Sensor | Source CSV field | Meaning | Unit |
|---|---|---|---|---|
| `modis_bt21_22_k` | MODIS | `brightness` | MODIS Band 21/22 brightness temperature | K |
| `modis_bt31_k` | MODIS | `bright_t31` | MODIS Band 31 brightness temperature | K |
| `viirs_bt_i4_k` | VIIRS | `brightness` | VIIRS I4 brightness temperature | K |
| `viirs_bt_i5_k` | VIIRS | `bright_t31` | Proposed Archive Download alias for VIIRS I5 brightness temperature | K |

#### MODIS mapping

NASA FIRMS documents:

- `brightness` as Band 21/22 brightness temperature.
- `bright_t31` as Band 31 brightness temperature.

Both are measured in Kelvin.

These MODIS mappings are confirmed by the NASA MODIS attribute documentation.

#### VIIRS mapping

NASA FIRMS documents:

- `Bright_ti4` / `Brightness` in web services as VIIRS I4 brightness temperature.
- `Bright_ti5` / `Brightness_2` in web services as VIIRS I5 brightness temperature.

The VIIRS Collection 2 User Guide independently identifies the fire-pixel temperature fields as I4 and I5.

The downloaded Sutellite VIIRS Archive CSVs use the shared headers `brightness` and `bright_t31`, rather than the channel-specific names `bright_ti4` and `bright_ti5`.

The first field maps to I4 through NASA's documented `Brightness` alias.

The second field is treated as the proposed archive-export alias for I5 because of its position in the shared archive schema and its correspondence with the documented second VIIRS temperature field. However, NASA's public attribute table does not explicitly name `bright_t31` as the VIIRS I5 alias.

**Mapping status:** The canonical I5 interpretation is provisional at the archive-export alias level. The source value and raw header must remain preserved, and this mapping must be confirmed against the exact archive export specification or a directly comparable standard product before it is treated as fully authoritative.

Do not interpret VIIRS `bright_t31` as MODIS Band 31.

Do not combine MODIS Band 21/22, MODIS Band 31, VIIRS I4 and VIIRS I5 into one generic brightness field.

### 5.6 Fire Radiative Power

| Canonical field | Type | Source CSV field | Unit |
|---|---|---|---|
| `frp_mw` | Float64 | `frp` | MW |

FRP represents pixel-integrated Fire Radiative Power.

NASA defines the unit as megawatts (MW).

Important rules:

- Preserve the original FRP value.
- Do not multiply or divide FRP by pixel area.
- Do not convert MODIS FRP into VIIRS FRP or vice versa.
- Do not assume identical retrieval behaviour between sensors.
- Do not replace missing values with zero.
- Do not replace negative values with zero.

#### VIIRS FRP retrieval characteristic

NASA's VIIRS Collection 2 User Guide explains that the 375 m fire pixels can share fractional FRP values derived from a single co-located 750 m retrieval.

In some cases, one 750 m FRP retrieval is divided between two 375 m fire-affected pixels.

Therefore, two VIIRS detections may contain fractional FRP values originating from the same larger retrieval.

This has implications for aggregation and emissions calculations. The two 375 m observations must not automatically be interpreted as two independent full-pixel FRP retrievals.

The guide also documents rare situations in which VIIRS detections have FRP set to zero, including certain M13 saturation cases. Other difficult retrieval situations can produce null FRP.

Consequently, zero and null must remain distinguishable. Zero must not automatically be treated as a missing value.

#### Negative FRP observations

The initial dataset validation identified 20 observations with negative FRP.

NASA's cited product documentation does not describe negative FRP as an ordinary valid output.

The project must therefore:

- Retain the original observations.
- Preserve their coordinates and timestamps.
- Flag negative FRP values.
- Exclude negative FRP values from FRP-based calculations by default.
- Keep them available for inspection and mapping.
- Never silently replace them with zero.
- Never label them as false fires without evidence.

The cause of these negative values has not been established.

### 5.7 Pixel dimensions

| Canonical field | Type | Source CSV field | Unit |
|---|---|---|---|
| `scan_km` | Float64 | `scan` | km |
| `track_km` | Float64 | `track` | km |

These fields represent the actual along-scan and along-track pixel dimensions.

Nominal sensor resolution is not a substitute for these values.

NASA explains that pixel dimensions vary across the satellite scan and become larger away from nadir.

Preserve the original dimensions and precision.

Do not assume every observation has a square pixel.

The exact footprint geometry cannot be reconstructed accurately from only the centre coordinates, scan and track dimensions unless the required viewing geometry and orientation information are also available.

Do not generate exact square pixel polygons by simply placing `scan_km × track_km` around every centre point.

### 5.8 Confidence

| Canonical field | Type | Nullable | Description |
|---|---|---|---|
| `confidence_raw` | String | Yes | Original source confidence value. |
| `confidence_system` | String | No | Confidence convention used by the sensor. |
| `confidence_modis_pct` | Float64 | Yes | MODIS confidence value, where applicable. |
| `confidence_viirs_class` | String | Yes | VIIRS confidence category, where applicable. |

MODIS and VIIRS use different confidence conventions.

**MODIS**

- Numeric confidence from 0 to 100.
- Retain the original numeric value.
- The value is expressed as a percentage by NASA FIRMS.
- Do not reinterpret it as a calibrated probability.

**VIIRS**

- `l` = low
- `n` = nominal
- `h` = high

These are categorical classes, not percentages.

Do not map VIIRS classes to invented numeric scores.

Do not convert MODIS and VIIRS confidence values into a shared scale without a separate, scientifically defensible methodology.

The canonical `confidence_system` must identify the convention:

```text
MODIS_PERCENT_0_100
VIIRS_LNH
```

### 5.9 Detection type

| Canonical field | Type | Nullable | Description |
|---|---|---|---|
| `detection_type_code` | Int8 | Yes | Original detection type code. |
| `detection_type_label` | String | Yes | Documented description where applicable. |

The observed ARCHIVE files contain the `type` field. The inspected NRT files do not.

NASA FIRMS type codes:

| Code | Description |
|---|---|
| 0 | Presumed vegetation fire |
| 1 | Active volcano |
| 2 | Other static land source |
| 3 | Offshore detection |

Preserve the original code.

Do not assume that every hotspot is a vegetation fire.

Do not assign type 0 to NRT observations where the source field is structurally absent.

The absence of `type` must be distinguishable from a row-level missing value.

### 5.10 Day/night

| Canonical field | Type | Nullable | Source values |
|---|---|---|---|
| `daynight` | String | No | `D`, `N` |

Definitions:

- `D` = daytime.
- `N` = nighttime.

Preserve the original source value.

### 5.11 Nominal sensor resolution

| Canonical field | Type | Sensor | Unit |
|---|---|---|---|
| `nominal_resolution_m` | UInt16 | MODIS | m |
| `nominal_resolution_m` | UInt16 | VIIRS | m |

Nominal values:

| Sensor | Nominal resolution |
|---|---:|
| MODIS | 1,000 m |
| VIIRS | 375 m |

This is sensor/product metadata, not a measurement of the exact dimensions of an individual observation.

Use `scan_km` and `track_km` for individual pixel dimensions.

Never upsample MODIS observations to 375 m or imply that doing so increases their spatial resolution.

## 6. Source version and collection handling

The source `version` field must be retained as a string.

Observed values include:

| Sensor and stream | Values observed |
|---|---|
| MODIS ARCHIVE | `6.03`, `61.03` |
| MODIS NRT | `6.1NRT` |
| VIIRS ARCHIVE | `2` |
| VIIRS NRT | `2.0NRT` |

The values `6.03` and `61.03` both occur in the MODIS ARCHIVE dataset.

The exact reason for the difference has not been established. Do not silently convert either value or assume they mean different scientific collections without supporting documentation.

Version values must never be parsed as floating-point numbers.

Preserve:

- `firms_version_raw`
- `source_collection`
- `processing_stream`
- `source_product_token_raw`

The collection and processing stream must be identifiable independently of the version string.

## 7. Null and missing-value conventions

Missing data must be represented as null, not as invented numeric or categorical values.

The pipeline must distinguish at least three cases:

| Case | Meaning |
|---|---|
| Structurally absent | The product schema does not contain that field. |
| Row-level missing | The field exists in the product schema, but the individual record has no value. |
| Not applicable | The field has no meaning for that observation or product. |

Examples:

- `type` absent in NRT: structurally absent.
- Null FRP in a record: row-level missing.
- MODIS confidence field on a VIIRS observation: not applicable.

Do not:

- Replace missing FRP with zero.
- Invent confidence values.
- Invent detection type codes.
- Treat an absent field as a detected zero.
- Delete an otherwise useful geographic observation solely because an optional measurement is missing.

Where feasible, record the reason for missingness in a field-specific status or quality flag.

## 8. Data-quality and validation conventions

### 8.1 Validation status

Every processed observation must retain a validation status.

Suggested values:

| Value | Meaning |
|---|---|
| `valid` | No validation issue was detected. |
| `invalid` | One or more strict validation rules failed. |

Field-level quality flags must identify the individual issue rather than relying only on a record-level status.

Examples:

```text
negative_frp
invalid_latitude
invalid_longitude
invalid_acq_date
invalid_acq_time
missing_required_field
malformed_source_row
```

A validation failure does not automatically mean that the entire observation must be deleted.

For example, a negative FRP value makes the FRP measurement unsuitable for default FRP-based calculations, but the observation may still contain useful coordinates, timestamps and sensor provenance.

### 8.2 Negative FRP policy

The initial validation identified:

```text
Total observations: 231,359,744
Valid observations: 231,359,724
Invalid observations: 20
Invalid field: FRP
```

All 20 negative FRP observations were retained in the diagnostic reports.

These observations must remain traceable to their original files and rows.

### 8.3 Numeric validation

Validate:

- Latitude within -90 to +90 degrees.
- Longitude within -180 to +180 degrees.
- Numeric values are finite.
- Scan and track dimensions are positive when present.
- FRP is not negative for FRP-based analytical eligibility.
- Dates and times are parseable and valid.
- Categorical values follow the relevant sensor/product convention.

Do not apply one sensor's categorical validation rules to another sensor.

## 9. Geographic reference and spatial calculations

### 9.1 Storage CRS

All geographic observation coordinates use:

```text
EPSG:4326 — WGS 84
```

Store longitude and latitude as decimal degrees.

Preserve original coordinate precision.

### 9.2 Web-map rendering

Web-map rendering may use:

```text
EPSG:3857 — Web Mercator
```

This is a display projection, not the canonical storage CRS.

The original WGS 84 coordinates must remain available.

### 9.3 Distance and area

Do not calculate distances or areas by treating decimal degrees as metres.

Use:

- Geodesic calculations on the appropriate Earth model, or
- A suitable local projected CRS for distance and area calculations.

For area statistics, use an appropriate equal-area projection or geodesic area calculation.

The projection must be selected according to the geographic extent and intended measurement.

### 9.4 Pixel footprints

The initial map should represent observations as detection points using their original coordinates.

Pixel footprints are a future enhancement.

Accurate footprints require sensor-specific geometry and sufficient geolocation/orientation information. Nominal resolution alone is not enough.

MODIS and VIIRS footprints must remain distinguishable.

## 10. ARCHIVE/NRT source precedence and overlap

The harmonisation pipeline must avoid double-counting observations from different processing streams.

The agreed policy is:

1. Use ARCHIVE wherever standard-quality coverage is available.
2. Use NRT for the most recent periods not yet represented in ARCHIVE.
3. Preserve the original source stream for every record.
4. Determine coverage boundaries using actual source files and metadata.
5. Do not assume the same replacement date applies to all sensors or regions.
6. Do not modify or delete raw source files.

If ARCHIVE and NRT overlap, the source-selection logic must prefer standard-quality ARCHIVE observations for the affected sensor, region and date once archive coverage is available.

The implementation must be tested for partial coverage and gaps rather than relying solely on a global date cutoff.

The source-selection decision must be reproducible and documented.

## 11. Duplicate observations and fire-event clustering

### 11.1 Observation identity

An observation is one source record associated with a satellite detection.

Two observations may describe the same physical fire without being duplicate records.

The following must remain distinct:

- MODIS and VIIRS detections of the same fire.
- Observations made by different satellites.
- Repeated observations of a fire at different acquisition times.
- Nearby detections from the same or different sensors.

### 11.2 Exact duplicate records

Exact duplicate handling must use a carefully defined identity rule.

Coordinates and timestamps being close is not sufficient to declare two records duplicates.

Where exact duplicates are identified:

- Preserve their original provenance.
- Retain a traceable link between original and retained records.
- Record the deduplication rule.
- Do not delete raw observations.

Automatic cross-sensor deduplication is not part of the initial harmonisation implementation.

### 11.3 Candidate fire-event clustering

Clustering is a separate derived-data operation.

The original observations must remain available regardless of clustering.

A future candidate event model may include:

- `event_id`
- Constituent `observation_id` values
- Configurable temporal thresholds
- Configurable spatial thresholds
- Cluster membership
- Clustering method/version

Clusters are candidate fire events, not verified wildfires.

The website should eventually allow users to choose among:

1. Individual satellite detections.
2. Candidate clusters of detections.
3. Both views together.

Clustering and AI-based prediction are outside the current implementation scope.

## 12. Processed-data layers

The project uses three conceptual data layers.

### 12.1 Cleaned observations

Contains source observations after structural parsing and validation.

Requirements:

- Preserve source provenance.
- Preserve raw source values.
- Apply strict validation checks.
- Record field-level quality flags.
- Retain observations with anomalies for inspection.
- Do not replace missing or anomalous values silently.

### 12.2 Harmonised observations

Contains observations represented using the canonical schema.

Requirements:

- Standardised field names and types.
- Normalised sensor and platform identifiers.
- Common UTC timestamp representation.
- WGS 84 geographic coordinates.
- Sensor-specific brightness-temperature fields.
- Original confidence convention preserved.
- Original detection type preserved where available.
- ARCHIVE/NRT source provenance preserved.
- Quality flags retained.

Only mappings whose meanings are confirmed or explicitly marked provisional may be applied.

### 12.3 Derived datasets

Contains outputs generated from harmonised observations.

Potential future examples:

- Candidate fire-event clusters.
- Spatial and temporal statistics.
- Aggregated fire activity.
- Emissions-related inputs.
- AI training and prediction outputs.

Derived datasets must not overwrite or replace the underlying observations.

This layer is not part of the current implementation beyond what is necessary to make harmonised observations available.

## 13. Storage and processing

### 13.1 Primary format

Parquet is the primary format for cleaned and harmonised observations.

Reasons:

- Columnar access.
- Compression.
- Efficient analytical queries.
- Typed fields.
- Suitable handling of large datasets.

### 13.2 Additional formats

| Format | Intended use |
|---|---|
| Parquet | Main processed observation storage. |
| CSV | Small exports and interoperability. |
| GeoJSON | Geographic subsets and map features. |
| JSON | Configuration and API responses. |

GeoJSON must not be used as the primary storage format for the full 231-million-observation dataset.

### 13.3 Partitioning

Partition the Parquet dataset using useful dimensions, initially:

- Region.
- Year.

Additional partitioning by sensor or processing stream should be introduced only when query performance and file size justify it.

Avoid one giant Parquet file and avoid creating thousands of tiny files.

### 13.4 Memory constraints

The raw dataset is approximately 17.45 GB, and the project environment has 16 GB RAM.

The pipeline must therefore:

- Process CSV files in chunks or as streams.
- Avoid loading the entire dataset into memory.
- Write processed data incrementally.
- Use bounded intermediate datasets.
- Avoid unnecessary copies of large data.
- Support restarting or identifying completed file partitions.

The original raw dataset remains outside Git.

## 14. Web-map requirements

The harmonised dataset is intended to support a web application with interactive 2D and potentially 2.5D mapping.

Initial map requirements:

- Display individual observation points.
- Keep MODIS and VIIRS layers independently selectable.
- Show the sensor/platform identity.
- Expose the acquisition time in UTC.
- Expose relevant measurements and confidence in tooltips.
- Make quality flags visible.
- Distinguish negative FRP observations from ordinary observations.
- Allow users to filter observations by sensor, platform, region and time.
- Avoid interpreting unobserved areas as areas with zero fires.

Negative FRP observations should remain available on the map but be visually distinguishable.

The default FRP-based analytical view should exclude negative FRP values. A user should still be able to inspect all observations.

The map should use harmonised processed data rather than independently loading and parsing the full raw CSV collection in the browser.

## 15. Measurement and scientific consistency rules

The following rules apply throughout the project:

1. NASA documentation takes precedence for source field meanings, measurement units and product conventions.
2. Preserve the original source field and value.
3. Preserve source precision; do not introduce arbitrary rounding.
4. Do not invent conversions between non-equivalent measurements.
5. Do not equate MODIS and VIIRS confidence systems.
6. Do not equate spectral channels merely because their field names look similar.
7. Do not upsample MODIS observations to VIIRS resolution.
8. Do not scale FRP by pixel area.
9. Do not treat a detection point as the exact physical location or extent of a fire.
10. Do not infer that two nearby observations are duplicates.
11. Distinguish missing, zero, invalid and structurally absent values.
12. Keep all transformations reproducible and documented.

## 16. Current implementation scope

### Included

- Raw dataset inventory.
- CSV schema inspection.
- Field profiling.
- Data validation.
- Negative FRP diagnostics.
- Canonical schema definition.
- Streaming/chunked processing design.
- Cleaned observations.
- Harmonised observations.
- Provenance and quality flags.
- Parquet output design.

### Deferred

- AI training.
- Fire prediction.
- Automated wildfire verification.
- Production fire-event clustering.
- Emissions estimation.
- Detailed pixel-footprint reconstruction.
- Advanced spatial analytics.

The immediate objective is to make all available source observations accurately accessible and harmonised.

AI training and predictive functionality must not be introduced into the current data-harmonisation stage.

## 17. Verification requirements before production

The following checks must be completed before the schema is treated as final:

| Check | Status |
|---|---|
| MODIS Collection 6.1 identification | Confirmed |
| VIIRS Collection 2 identification | Confirmed |
| MODIS `brightness` channel mapping | Confirmed |
| MODIS `bright_t31` channel mapping | Confirmed |
| VIIRS `brightness` to I4 mapping | Confirmed by NASA FIRMS attribute definition |
| VIIRS archive `bright_t31` to I5 alias | Provisional; exact Archive Download alias confirmation required |
| MODIS confidence convention | Confirmed |
| VIIRS confidence convention | Confirmed |
| FRP unit | Confirmed |
| VIIRS fractional FRP behaviour | Confirmed |
| Acquisition time UTC convention | Confirmed |
| WGS 84 coordinate convention | Confirmed |
| ARCHIVE/NRT processing distinction | Confirmed |
| ARCHIVE processing provider | Confirmed |
| NRT processing provider | Confirmed |
| Exact pixel-footprint geometry | Deferred |
| MODIS `61.03` version interpretation | Unresolved |

Before production use, add automated schema tests that:

- Verify the exact expected raw headers for each sensor and stream.
- Verify sensor/platform identification from both filename and source fields.
- Reject unsupported combinations of product token, instrument and platform.
- Prevent MODIS temperature mappings from being applied to VIIRS rows.
- Keep the VIIRS I5 alias explicitly versioned or provisional until verified.
- Validate acquisition date and time.
- Preserve nullable and structurally absent fields.
- Preserve original source values and provenance.
- Confirm that all input rows are accounted for in processing reports.

## 18. NASA references

The following official sources define the product conventions and field meanings used in this schema.

1. **NASA FIRMS Archive Download**
   https://firms.modaps.eosdis.nasa.gov/download/

2. **NASA FIRMS Archive README — MODIS and VIIRS Fire/Hotspot Data Download**
   https://nrt3.modaps.eosdis.nasa.gov/archive/FIRMS/README.pdf
   Updated December 30, 2025. Describes archive directory structure, file naming, processing providers, NRT/standard-quality distinctions and data citation.

3. **NASA FIRMS MODIS Fire/Hotspot Attributes**
   https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html

4. **NASA FIRMS VIIRS Fire/Hotspot Attributes**
   https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html

5. **VIIRS Collection 2 375-m Active Fire Product User's Guide, Version 1.2**
   https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf
   June 2025. Documents the I4/I5 channels, product fields, confidence encoding, FRP retrieval and standard monthly product structure.

6. **MODIS Collection 6 and Collection 6.1 Active Fire Product User's Guide**
   https://www.earthdata.nasa.gov/s3fs-public/2023-09/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf

7. **NASA FIRMS Data Ingest Tutorial**
   https://firms.modaps.eosdis.nasa.gov/content/academy/data_ingest/firms_data_ingest.html

8. **NASA FIRMS API Tutorial**
   https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html

---

**End of document.**
