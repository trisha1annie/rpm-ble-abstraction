# GATT Decode Registry

This directory contains the components for the SIG-standard decoding pathway of the BLE simulated physiological devices architecture. 

## Architecture Overview

The system is built around two primary decoding pathways:

1. **SIG-standard pathway:** This pathway matches discovered BLE services and characteristics against recognised Bluetooth SIG assigned numbers. Once a device is identified, its raw characteristic payloads are decoded using our local YAML registry rules.
2. **Proprietary pathway:** This acts as a fallback for device profiles that either don't follow SIG-standard assignments or rely on non-standard, custom data schemas.

**Important Note on ECG:** ECG device emulation is explicitly excluded from this SIG-standard registry work. ECG functionality relies heavily on vendor-specific payloads and doesn't fit neatly into standardised GATT parsing within our architecture. Instead, it is handled entirely by the proprietary pathway.

## Components

- **`vendor/bluetooth-numbers-database/`**: A local clone of the NordicSemiconductor Bluetooth Numbers Database. It provides raw JSON files (located under `v1/`) that map standard assigned numbers (UUIDs) to their identifiers and names.
- **`tools/build_uuid_cache.py`**: A build script that reads the vendored database and extracts only the UUIDs required for our supported profiles, outputting a streamlined offline JSON cache.
- **`cache/uuid_lookup.json`**: The offline runtime cache. The application uses this to identify discovered BLE attributes without needing an active network connection.
## Supported SIG-Standard Devices

At present, the offline cache and decode registry include scaffolds for:
- Blood Pressure Monitor (0x1810)
- Weight Scale (0x181D)
- Pulse Oximeter (0x1822)
