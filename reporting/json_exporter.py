"""Export scan results as JSON."""

import json
from datetime import datetime

def export_json(results, target, start_port, end_port, os_guess, filepath):
    data = {
        "target": target,
        "date": datetime.now().isoformat(),
        "port_range": f"{start_port}-{end_port}",
        "os_guess": os_guess,
        "open_ports": results
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
