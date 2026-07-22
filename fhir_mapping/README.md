# FHIR Mapping Specifications
This directory contains the FHIR resource mapping specifications used by the RPM BLE Abstraction Layer. Decoded raw Bluetooth Low Energy (BLE) payloads are passed to the FHIR normalization layer for standardization. Each decoded measurement is mapped to an HL7 FHIR observation resource, with its measurement value, unit of measure, physiological observation code, timestamp, and patient reference. These are mapped using standard terminologies, including:
- **HL7 FHIR R5** for healthcare resource structure
- **LOINC** for clinical observation codes
- **UCUM** for units of measurement

These YAML files are **project-specific mapping specifications** 
## Mapping Files
- `blood_pressure.yaml` – Maps measurements from Bluetooth Blood Pressure Service (UUID **1810**) to FHIR Blood Pressure Observations.
- `pulse_oximeter.yaml` – Maps measurements from Bluetooth Pulse Oximeter Service (UUID **1822**) to FHIR Oxygen Saturation and Heart Rate Observations.
- `weight.yaml` – Maps measurements from Bluetooth Weight Scale Service (UUID **181D**) to FHIR Body Weight, Body Height, and Body Mass Index (BMI) Observations.