# Sutellite – Raw Data Validation Report

**Date:** 2026-11-06  
**Stage:** Raw data validation  
**Status:** Completed

## 1. Scope

The validation process covered the complete raw dataset:

- **CSV files:** 64
- **Total observations:** 231,359,744
- **ARCHIVE observations:** 221,533,276
- **NRT observations:** 9,826,468

The dataset contains MODIS and VIIRS active-fire observations across eight study regions.

All raw CSV files were read without modifying their contents.

## 2. Validation results

The validation script processed all 64 CSV files.

| Result | Observations |
|---|---:|
| Total observations | 231,359,744 |
| Valid observations | 231,359,724 |
| Invalid observations | 20 |

The 20 invalid observations were all flagged by the same rule:

`frp:out_of_range`

This means their Fire Radiative Power (FRP) values were negative.

The invalid observations represent approximately **0.00000865%** of the dataset. The valid percentage rounds to 100.0000% at four decimal places.

No other validation errors were reported.

## 3. Negative FRP investigation

The 20 negative FRP observations were extracted and their complete records retrieved from the original CSV files.

The investigation confirmed:

- 6 observations came from MODIS ARCHIVE files.
- 14 observations came from VIIRS NRT files.
- The records were found across 7 source CSV files.
- All 20 records were successfully retrieved and cross-checked.

### Distribution

| Source | Observations |
|---|---:|
| MODIS ARCHIVE – Aqua | 6 |
| VIIRS NRT – NOAA-20 | 1 |
| VIIRS NRT – NOAA-21 | 8 |
| VIIRS NRT – S-NPP | 5 |
| **Total** | **20** |

Additional characteristics:

- FRP values ranged from -0.10 MW to -29.9 MW.
- 19 observations were daytime detections and 1 was a nighttime detection.
- All 6 MODIS observations had confidence value 0.
- Among the 14 VIIRS observations, 10 had low confidence (`l`) and 4 had nominal confidence (`n`).
- Several VIIRS observations had a brightness value of 367 K.

The complete records are stored in `NEGATIVE_FRP_CONTEXT.csv`. The concise list of affected observations is stored in `NEGATIVE_FRP_RECORDS.csv`.

## 4. NASA documentation review

The VIIRS Collection 2 375 m Active Fire Product User's Guide describes:

- VIIRS I4 brightness temperatures with a typical dynamic range of approximately 208–367 K.
- A pixel saturation quality condition that includes a brightness temperature of 367 K.
- FRP values expressed in megawatts (MW).
- Zero FRP as a fill value, with special retrieval cases also documented.
- Certain difficult retrieval situations in which FRP may be unavailable.

The guide does not document negative FRP as a valid physical result.

A brightness value of 367 K may indicate a saturation-related condition. However, this does not establish that saturation caused the negative FRP observations. No definitive cause has been identified for all 20 records.

**Reference:**

NASA, *VIIRS Collection 2 375-m Active Fire Product User's Guide* (May 2024).  
https://viirsland.gsfc.nasa.gov/PDF/VIIRS_activefire_User_Guide.pdf

## 5. Data treatment decisions

The following decisions will guide subsequent processing:

1. **Preserve the original data.** Raw CSV files must remain unchanged.
2. **Flag negative FRP values.** These observations remain identifiable as validation anomalies.
3. **Do not replace negative values with zero.** Zero has its own documented meaning in the product data and should not be used as an arbitrary correction.
4. **Exclude negative FRP values from FRP-based calculations in processed datasets**, unless a later source-specific investigation establishes a defensible alternative treatment.
5. **Retain provenance.** Any excluded or flagged observation must remain traceable to its original file and record.
6. **Treat 367 K as a potentially saturation-related brightness value**, not as a missing-value indicator.

These decisions apply to analytical processing, not to the original raw dataset.

## 6. Validation limitations

This validation stage checks structural and basic field-level consistency. It does not establish:

- Whether every detected hotspot corresponds to an actual fire.
- Whether multiple observations represent the same fire event.
- Whether MODIS and VIIRS detections are directly comparable.
- Whether ARCHIVE and NRT observations overlap.
- Whether all product-specific quality conditions have been interpreted.

These issues require additional processing and analysis.

## 7. Implementation

The validation and diagnostic work was carried out using:

| File | Purpose |
|---|---|
| `src/validate_data.py` | Validates raw CSV observations |
| `tests/test_validate_data.py` | Unit tests for validation rules |
| `src/inspect_negative_frp.py` | Extracts observations with negative FRP |
| `src/inspect_frp_context.py` | Retrieves complete records for those observations |
| `docs/data/NEGATIVE_FRP_RECORDS.csv` | List of negative FRP observations |
| `docs/data/NEGATIVE_FRP_CONTEXT.csv` | Complete context for the affected observations |

The validation unit test suite contains 15 tests, all of which passed.

## 8. Conclusion

The raw dataset passed the implemented structural and field-level checks except for 20 observations containing negative FRP values.

These observations have been isolated and documented. The raw dataset remains unchanged, and the identified anomalies will be handled explicitly during subsequent data cleaning and harmonisation.

**Validation stage: completed.**