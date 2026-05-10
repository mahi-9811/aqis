# python
from typing import Dict, Any
from pathlib import Path
import json
from datetime import datetime

EVENT_LOG = Path("data/history/events.log")

def append_event(event_type: str, metadata: Dict[str, Any]) -> None:
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "meta": metadata
    }
    # append as JSON line
    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")