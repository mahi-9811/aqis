# python
from typing import Any, Dict, List, Optional
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import uuid

DB_PATH = Path("data/history/history.db")
SNAPSHOT_ROOT = Path("data/history")

class StorageAdapter:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path), timeout=30, isolation_level="DEFERRED")

    def _ensure_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
              id TEXT PRIMARY KEY,
              test_name TEXT,
              timestamp TEXT,
              version INTEGER,
              failed INTEGER,
              retries INTEGER,
              exception TEXT,
              avg_timing_ms REAL,
              drift INTEGER,
              snapshot_path TEXT
            )""")
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_ts ON history(test_name, timestamp)
            """)
            conn.commit()

    def insert_record(self, record: Dict[str, Any], snapshot_json: Dict[str, Any]) -> str:
        """
        Insert metadata into SQLite and write snapshot file. Returns record id.
        """
        record_id = str(uuid.uuid4())
        ts = datetime.utcnow().isoformat() + "Z"
        # write snapshot
        date_dir = SNAPSHOT_ROOT / ts[:10]
        date_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = date_dir / f"{record_id}.json"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_json, f, default=str)

        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO history (id,test_name,timestamp,version,failed,retries,exception,avg_timing_ms,drift,snapshot_path)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                record_id,
                record["test_name"],
                ts,
                record.get("version", 1),
                1 if record.get("failed") else 0,
                record.get("retries", 0),
                record.get("exception", ""),
                record.get("avg_timing_ms", None),
                1 if record.get("drift") else 0,
                str(snapshot_path)
            ))
            conn.commit()
        return record_id

    def query_history(self, test_name: str, limit: int = 100, since: Optional[str] = None) -> List[Dict[str,Any]]:
        q = "SELECT id,test_name,timestamp,version,failed,retries,exception,avg_timing_ms,drift,snapshot_path FROM history WHERE test_name = ?"
        params = [test_name]
        if since:
            q += " AND timestamp >= ?"
            params.append(since)
        q += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(q, params)
            rows = cur.fetchall()
        keys = ["id","test_name","timestamp","version","failed","retries","exception","avg_timing_ms","drift","snapshot_path"]
        return [dict(zip(keys,row)) for row in rows]        # python
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