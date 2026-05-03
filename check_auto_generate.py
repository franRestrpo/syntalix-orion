import json
from apps_metadata import APP_METADATA

missing = []
for app_id, meta in APP_METADATA.items():
    vars_def = meta.get('variables', {})
    for var_name, var_info in vars_def.items():
        if var_info.get('required') is True and var_info.get('auto_generate') is not False:
            missing.append(f"{app_id} -> {var_name}")

print("Missing auto_generate: False for required variables:")
print(json.dumps(missing, indent=2))
