from __future__ import annotations

import csv
import io
import json
from typing import Any


def results_to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2)


def results_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
