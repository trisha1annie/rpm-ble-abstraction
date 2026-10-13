# FHIR Mapping Specifications
This directory contains the FHIR resource mapping specifications used by the RPM BLE Abstraction Layer. Decoded raw Bluetooth Low Energy (BLE) payloads are passed to the FHIR normalisation layer for standardisation. Each decoded measurement is mapped to an HL7 FHIR observation resource, with its measurement value, unit of measure, physiological observation code, timestamp, and patient reference. These are mapped using standard terminologies, including:
- **HL7 FHIR R5** for healthcare resource structure
- **LOINC** for clinical observation codes
- **UCUM** for units of measurement

## Mapping Files
- `blood_pressure.yaml` – Maps measurements from Bluetooth Blood Pressure Service (UUID **1810**) to FHIR Blood Pressure Observations.
- `pulse_oximeter.yaml` – Maps measurements from Bluetooth Pulse Oximeter Service (UUID **1822**) to FHIR Oxygen Saturation and Heart Rate Observations.
- `weight.yaml` – Maps measurements from Bluetooth Weight Scale Service (UUID **181D**) to FHIR Body Weight, Body Height, and Body Mass Index (BMI) Observations.
- `yk_oximeter.yaml` – Maps measurements from the proprietary YK pulse oximeter (service **cdeacd80-5235-4c07-8846-93a37ee6b86d**, decoded through `src/wot/`) to FHIR Oxygen Saturation and Heart Rate Observations.

The normaliser loads these files and applies the source route, target, components, additional measurements, and constraints. `dynamic`, `quality_mapping`, and `validation` are kept here and are not applied yet. A pulse oximeter reading is rejected when a flag listed under `constraints.reject_status_flags` is set. A reading is also rejected when a field listed under `constraints.reject_values` holds one of its listed values. The YK oximeter uses this to drop the SpO2 0 and pulse 0 readings it sends when no finger is in the sensor.
