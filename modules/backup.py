"""
Q9 — File Handling: Backup & Restore
Export the full database to a timestamped JSON file.
Import a JSON file back (with explicit confirmation).
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from database import get_connection


EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)


# Order matters for import (parents before children to satisfy FKs)
TABLES_IN_ORDER = [
    "students",
    "courses",
    "enrollments",
    "marks",
    "fee_accounts",
    "payments",
    "warning_letters",
]


def _table_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _dump_table(conn, name):
    if not _table_exists(conn, name):
        return []
    rows = conn.execute(f"SELECT * FROM {name}").fetchall()
    return [dict(r) for r in rows]


def export_database():
    """Dump every table to a single JSON file. Returns (success, message, path)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"apex_backup_{timestamp}.json"
    filepath = EXPORTS_DIR / filename

    payload = {
        "meta": {
            "system": "APEX UNIVERSITY",
            "exported_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "format_version": "1.0",
        },
        "tables": {},
    }

    try:
        with get_connection() as conn:
            for table in TABLES_IN_ORDER:
                payload["tables"][table] = _dump_table(conn, table)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        total_rows = sum(len(v) for v in payload["tables"].values())
        return True, (
            f"Backup complete: {filename} "
            f"({total_rows} rows across {len(payload['tables'])} tables)."
        ), str(filepath)
    except Exception as e:
        return False, f"Export failed: {e}", None


def get_backup_summary():
    """Quick stats for the current DB."""
    summary = {}
    try:
        with get_connection() as conn:
            for table in TABLES_IN_ORDER:
                if _table_exists(conn, table):
                    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                else:
                    n = 0
                summary[table] = n
    except sqlite3.Error:
        pass
    return summary


def list_backups():
    if not EXPORTS_DIR.exists():
        return []
    items = []
    for p in sorted(EXPORTS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        stat = p.stat()
        items.append({
            "filename": p.name,
            "path": str(p),
            "size_kb": round(stat.st_size / 1024, 1),
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return items


def _validate_payload(payload):
    if not isinstance(payload, dict):
        return False, "Backup file must be a JSON object."
    if "tables" not in payload or not isinstance(payload["tables"], dict):
        return False, "Backup file is missing the 'tables' section."
    return True, ""


def import_database(file_bytes_or_path, replace=True):
    """
    Restore the DB from a JSON backup file.
    Returns (success, message, stats_dict).
    """
    try:
        if isinstance(file_bytes_or_path, (bytes, bytearray)):
            payload = json.loads(file_bytes_or_path.decode("utf-8"))
        else:
            with open(file_bytes_or_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}", {}
    except Exception as e:
        return False, f"Could not read file: {e}", {}

    ok, msg = _validate_payload(payload)
    if not ok:
        return False, msg, {}

    tables = payload["tables"]
    stats = {}

    try:
        with get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = OFF")

            if replace:
                for table in reversed(TABLES_IN_ORDER):
                    if table in tables and _table_exists(conn, table):
                        conn.execute(f"DELETE FROM {table}")

            for table in TABLES_IN_ORDER:
                if table not in tables:
                    continue
                if not _table_exists(conn, table):
                    stats[table] = 0
                    continue

                rows = tables[table]
                inserted = 0
                for row in rows:
                    if not isinstance(row, dict) or not row:
                        continue
                    cols = list(row.keys())
                    placeholders = ",".join(["?"] * len(cols))
                    col_list = ",".join(cols)
                    try:
                        conn.execute(
                            f"INSERT OR REPLACE INTO {table} ({col_list}) "
                            f"VALUES ({placeholders})",
                            tuple(row[c] for c in cols),
                        )
                        inserted += 1
                    except sqlite3.Error:
                        continue
                stats[table] = inserted

            conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()

        total = sum(stats.values())
        return True, f"Restore complete: {total} rows imported.", stats
    except Exception as e:
        return False, f"Restore failed: {e}", {}