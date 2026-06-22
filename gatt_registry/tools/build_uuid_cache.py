import json
import os
import datetime

# The SIG-standard services we want to support
TARGET_SERVICES = {
    "1810": "Blood Pressure",
    "181D": "Weight Scale",
    "1822": "Pulse Oximeter",
}

# The characteristics we want to support for those services
TARGET_CHARACTERISTICS = {
    # Blood Pressure
    "2A35": "Blood Pressure Measurement",
    "2A36": "Intermediate Cuff Pressure",
    "2A49": "Blood Pressure Feature",
    # Weight Scale
    "2A9D": "Weight Measurement",
    "2A9E": "Weight Scale Feature",
    # Pulse Oximeter
    "2A5E": "PLX Spot-Check Measurement",
    "2A5F": "PLX Continuous Measurement",
    "2A60": "PLX Features",
    "2A52": "Record Access Control Point",
}

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_uuid(uuid_str):
    """Normalize UUID to uppercase, pad to 16 bits if it's a short UUID, etc."""
    uuid_str = str(uuid_str).strip().upper()
    return uuid_str

def extract_metadata(data_list, target_uuids):
    """Filter the list to only include target UUIDs and normalize them."""
    extracted = {}
    for item in data_list:
        raw_uuid = item.get("uuid")
        if not raw_uuid:
            continue
            
        uuid_norm = normalize_uuid(raw_uuid)
        
        # Check if the normalized UUID matches any of our targets
        if uuid_norm in target_uuids:
            extracted[uuid_norm] = {
                "name": item.get("name"),
                "identifier": item.get("identifier"),
                "source": item.get("source")
            }
    return extracted

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vendor_dir = os.path.join(base_dir, "vendor", "bluetooth-numbers-database", "v1")
    cache_dir = os.path.join(base_dir, "cache")
    
    services_file = os.path.join(vendor_dir, "service_uuids.json")
    characteristics_file = os.path.join(vendor_dir, "characteristic_uuids.json")
    
    if not os.path.exists(services_file) or not os.path.exists(characteristics_file):
        print(f"Error: Vendor JSON files not found in {vendor_dir}")
        print("Please ensure the NordicSemiconductor repository is cloned.")
        return

    services_data = load_json(services_file)
    characteristics_data = load_json(characteristics_file)

    print("Extracting SIG-standard services...")
    services_cache = extract_metadata(services_data, set(TARGET_SERVICES.keys()))
    
    print("Extracting related characteristics...")
    characteristics_cache = extract_metadata(characteristics_data, set(TARGET_CHARACTERISTICS.keys()))

    cache_output = {
        "_meta": {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_repo": "NordicSemiconductor/bluetooth-numbers-database",
            "description": "Offline cache for SIG-standard GATT UUIDs (filtered)"
        },
        "services": services_cache,
        "characteristics": characteristics_cache
    }

    os.makedirs(cache_dir, exist_ok=True)
    cache_filepath = os.path.join(cache_dir, "uuid_lookup.json")
    
    with open(cache_filepath, 'w', encoding='utf-8') as f:
        json.dump(cache_output, f, indent=2)
        
    print(f"Successfully wrote {len(services_cache)} services and {len(characteristics_cache)} characteristics to {cache_filepath}")

if __name__ == "__main__":
    main()
