
# Raw Data Characteristics

## 1. Dataset Inventory

### Overview

The project uses active fire detection data downloaded from NASA FIRMS (Fire Information for Resource Management System).

| Characteristic | Description |
|---|---|
| Total CSV files | 64 |
| Study regions | 8 |
| Sensor configurations | 4 |
| Product types | 2 |
| Approximate raw data size | 17.45 GB |
| Start date | 2000-11-01 |
| End date | 2026-11-04 |

### Study Regions

The dataset covers eight study regions:

- Angola
- Brazil
- Democratic Republic of the Congo (DRC)
- Zambia
- California
- Spain
- Indonesia
- Australia

### Sensor Configurations

Each study region contains data from four sensor configurations:

1. MODIS
2. VIIRS S-NPP
3. VIIRS NOAA-20
4. VIIRS NOAA-21

This results in 32 sensor-specific folders across the eight regions.

### Product Types

Each sensor-specific folder contains two CSV products:

- **ARCHIVE:** Standard archived fire detection data.
- **NRT:** Near Real-Time fire detection data.

Therefore, the dataset contains 32 ARCHIVE files and 32 NRT files.

### Data Storage

Original NASA FIRMS CSV files are stored outside the Git repository. Each developer must configure their local dataset directory through the `SUTELLITE_DATA_DIR` environment variable.


## 2. Sensor Identification

### MODIS

MODIS (Moderate Resolution Imaging Spectroradiometer) data comes from the Terra and Aqua satellites.

- Folder suffix: `_modis`
- CSV filename prefix: `fire_archive_M-C61` or `fire_nrt_M-C61`
- Instrument value: `MODIS`
- Satellite values: `Terra`, `Aqua`
- Nominal spatial resolution: approximately 1 km

### VIIRS S-NPP

VIIRS (Visible Infrared Imaging Radiometer Suite) data comes from the Suomi National Polar-orbiting Partnership satellite.

- Folder suffix: `_viirs_snpp`
- CSV filename prefix: `fire_archive_SV-C2` or `fire_nrt_SV-C2`
- Instrument value: `SNPP`
- Satellite value: `SNPP`
- Nominal spatial resolution: approximately 375 m

### VIIRS NOAA-20

- Folder suffix: `_viirs_20`
- CSV filename prefix: `fire_archive_J1V-C2` or `fire_nrt_J1V-C2`
- Instrument value: `VIIRS`
- Satellite value: `N20`
- Nominal spatial resolution: approximately 375 m

### VIIRS NOAA-21

- Folder suffix: `_viirs_21`
- CSV filename prefix: `fire_archive_J2V-C2` or `fire_nrt_J2V-C2`
- Instrument value: `VIIRS`
- Satellite value: `N21`
- Nominal spatial resolution: approximately 375 m

### Identification Strategy

Sensor identification should primarily use the source folder and filename metadata.

The `instrument` field alone is insufficient to distinguish all sensors because VIIRS S-NPP uses `SNPP`, while NOAA-20 and NOAA-21 use `VIIRS`.


## 3. ARCHIVE vs NRT

The dataset contains two NASA FIRMS product types for each sensor configuration.

### ARCHIVE

ARCHIVE files contain standard archived fire detection observations.

- Filename prefix: `fire_archive`
- Number of files: 32
- One file per study region and sensor configuration.
- Includes the `type` field.
- Examples of version values:
  - MODIS: `6.03`
  - VIIRS: `2`

### NRT (Near Real-Time)

NRT files contain near real-time fire detection observations.

- Filename prefix: `fire_nrt`
- Number of files: 32
- One file per study region and sensor configuration.
- Does not include the `type` field in the inspected CSV schemas.
- Examples of version values:
  - MODIS: `6.1NRT`
  - VIIRS: `2.0NRT`

### Important Considerations

ARCHIVE and NRT are separate data products and should not be blindly concatenated.

Their temporal coverage may overlap. Combining them without checking for duplicate or superseded observations could lead to double counting.

The processing pipeline must preserve the original product source so that observations can be traced back to ARCHIVE or NRT.

The absence of the `type` field in NRT must also be handled explicitly during harmonisation. Missing information must not be interpreted as a particular detection type.


## 4. CSV Schemas

The 64 CSV files were inspected automatically using `src/inspect_schemas.py`.

The inspection confirmed that all files follow consistent schemas within their respective sensor and product groups.

### ARCHIVE Schema

ARCHIVE files contain 15 columns:

| Column | Position |
|---|---:|
| latitude | 1 |
| longitude | 2 |
| brightness | 3 |
| scan | 4 |
| track | 5 |
| acq_date | 6 |
| acq_time | 7 |
| satellite | 8 |
| instrument | 9 |
| confidence | 10 |
| version | 11 |
| bright_t31 | 12 |
| frp | 13 |
| daynight | 14 |
| type | 15 |

### NRT Schema

NRT files contain 14 columns:

| Column | Position |
|---|---:|
| latitude | 1 |
| longitude | 2 |
| brightness | 3 |
| scan | 4 |
| track | 5 |
| acq_date | 6 |
| acq_time | 7 |
| satellite | 8 |
| instrument | 9 |
| confidence | 10 |
| version | 11 |
| bright_t31 | 12 |
| frp | 13 |
| daynight | 14 |

### Schema Consistency

The inspection found:

- 8 files per sensor/product combination.
- 1 unique schema per sensor/product combination.
- Identical column names and ordering across all eight regions within each combination.
- `type` is the only column absent from NRT files.

All other 14 columns are present in every CSV file.


## 5. Field Descriptions

The following table describes the 14 fields shared by ARCHIVE and NRT products, plus the additional ARCHIVE field.

| Field | Description |
|---|---|
| `latitude` | Geographic latitude of the detected hotspot. |
| `longitude` | Geographic longitude of the detected hotspot. |
| `brightness` | Brightness temperature of the fire pixel, in Kelvin. |
| `scan` | Pixel size in the scan direction, in kilometres. |
| `track` | Pixel size in the track direction, in kilometres. |
| `acq_date` | Date of the satellite observation (`YYYY-MM-DD`). |
| `acq_time` | Time of the satellite observation, in UTC (`HHMM`). |
| `satellite` | Satellite that produced the observation. |
| `instrument` | Instrument identifier reported in the source product. |
| `confidence` | Confidence indicator associated with the fire detection. |
| `version` | Version of the source data product. |
| `bright_t31` | Brightness temperature of the 11-micrometre channel, in Kelvin. |
| `frp` | Fire Radiative Power (FRP), in megawatts (MW). |
| `daynight` | Indicates whether the observation occurred during daytime (`D`) or nighttime (`N`). |
| `type` | Detection type classification. Present in ARCHIVE files only. |

### Notes

- `acq_time` must be handled as a four-digit time value to preserve leading zeros.
- `confidence` has different representations in MODIS and VIIRS products.
- `version` must be preserved because different product versions may have different processing characteristics.
- `type` is not available in the inspected NRT schemas.


## 6. Known Differences Between MODIS and VIIRS

The inspection of representative CSV rows revealed several differences between the products.

### 6.1 Confidence

MODIS and VIIRS use different confidence representations.

| Sensor | Observed representation | Example values |
|---|---|---|
| MODIS | Numeric | `16`, `67`, `89` |
| VIIRS | Categorical | `l`, `n`, `h` |

These values must not be treated as directly equivalent.

A common confidence representation would require a documented methodology. Arbitrary conversion between numeric and categorical values must be avoided.

### 6.2 Satellite and Instrument Identifiers

The inspected files contain the following identifiers:

| Sensor configuration | Satellite values | Instrument values |
|---|---|---|
| MODIS | `Terra`, `Aqua` | `MODIS` |
| VIIRS S-NPP | `SNPP` | `SNPP` |
| VIIRS NOAA-20 | `N20` | `VIIRS` |
| VIIRS NOAA-21 | `N21` | `VIIRS` |

The `instrument` field alone cannot distinguish all four sensor configurations.

The source folder and filename should therefore also be used to identify the sensor.

### 6.3 Product Versions

The inspected samples contain different version identifiers:

| Sensor | ARCHIVE | NRT |
|---|---|---|
| MODIS | `6.03` | `6.1NRT` |
| VIIRS | `2` | `2.0NRT` |

Original version identifiers should be retained as metadata.

### 6.4 Detection Type

The `type` field is present in ARCHIVE but absent from NRT.

The inspected samples contain values `0` and `2` in VIIRS ARCHIVE files.

The field must be interpreted according to the relevant product documentation. Its absence in NRT must not be interpreted as a specific detection type.

### 6.5 Spatial Resolution

The nominal spatial resolutions differ:

- MODIS: approximately 1 km.
- VIIRS: approximately 375 m.

This difference affects the detection of smaller fires and makes raw hotspot counts from the two instruments unsuitable for direct comparison without accounting for their different observation characteristics.

### 6.6 Temporal Coverage

The sensors do not cover identical date ranges.

Their observations must be analysed according to their actual operational periods. Missing historical coverage must not be interpreted as an absence of fire activity.


## 7. Harmonisation Considerations

The differences identified during data inspection introduce several requirements for the harmonisation process.

### 7.1 Preserve Original Data

- Original NASA FIRMS CSV files must remain unchanged.
- Raw field values should be preserved.
- Every processed observation should retain its source sensor, satellite, product type, and original version.
- Processed data should remain traceable to its original file.

### 7.2 Confidence Harmonisation

MODIS numeric confidence values and VIIRS categorical confidence values must not be directly equated.

Any common confidence classification must be based on documented criteria and a justified methodology.

### 7.3 Spatial Harmonisation

MODIS and VIIRS have different nominal spatial resolutions.

The processing pipeline must account for this difference when comparing detection counts and spatial distributions.

MODIS observations should not simply be upsampled to VIIRS resolution under the assumption that this creates equivalent spatial information.

### 7.4 Temporal Harmonisation

- Acquisition dates and times must be interpreted consistently.
- All timestamps should retain their UTC reference.
- Differences in satellite operational periods must be considered.
- ARCHIVE and NRT observations must be distinguished to avoid duplicate counting.

### 7.5 Missing Information

Fields absent from a source product must be represented explicitly as missing or unavailable.

Missing values must not be replaced with assumed classifications or measurements.

### 7.6 Detection Counts

A hotspot detection is not necessarily equivalent to a unique fire event.

Comparisons between sensors must distinguish individual satellite detections from grouped fire events.

### 7.7 Processing Traceability

The harmonised dataset should retain enough metadata to identify:

- Original source file.
- Study region.
- Sensor configuration.
- Satellite.
- Product type (ARCHIVE or NRT).
- Original product version.

These considerations will guide the design of the processing and harmonisation pipeline.
