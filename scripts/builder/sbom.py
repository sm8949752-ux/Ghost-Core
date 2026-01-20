import json
import os
import platform

def generate_sbom(version,name,url, components, output_path):
    """
    Constructs a valid CycloneDX JSON SBOM.
    
    Args:
        version (str): The version of the main application.
        components (list): List of dicts [{'name': '...', 'version': '...', 'file': '...'}]
        output_path (str): Where to save the JSON file.
    """
    
    # 1. Main Component 
    # Defined manually because we built it from source
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "component": {
                "type": "container",
                "name": f"ghost-core/{name}",
                "version": version
            }
        },
        "components": [
            {
                "type": "application",
                "name": f"{name}",
                "version": version,
                # PURL links to the generic download URL (Source of Truth)
                "purl": f"pkg:generic/{name}@{version}?download_url={url}",
                "cpe": f"cpe:2.3:a:{name}:{name}:{version}:*:*:*:*:*:*:*",
                "properties": [
                    {"name": "syft:package:type", "value": "manual"},
                    {"name": "ghost:build:mode", "value": "source-compiled"}
                ]
            }
        ]
    }

    # 2. Add Dependencies (Libraries)
    # We use a set to avoid duplicate entries if multiple libs belong to the same package
    processed_pkgs = set()
    arch = platform.machine() # e.g., x86_64, aarch64
    
    for comp in components:
        pkg_key = f"{comp['name']}@{comp['version']}"
        
        if pkg_key in processed_pkgs:
            continue
            
        sbom["components"].append({
            "type": "library",
            "name": comp['name'],
            "version": comp['version'],
            # Important: PURL for Alpine/Wolfi packages
            "purl": f"pkg:alpine/{comp['name']}@{comp['version']}?arch={arch}",
            "description": f"Dependency imported from builder: {comp['file']}"
        })
        
        processed_pkgs.add(pkg_key)

    # 3. Write to Disk
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, 'w') as f:
            json.dump(sbom, f, indent=2)
        print(f"    -> SBOM successfully written with {len(sbom['components'])} components.")
    except IOError as e:
        print(f"Error writing SBOM: {e}")
