import json
import os
from threading import Lock

DB_FILE = os.path.join(os.path.dirname(__file__), "score_cache.json")
_lock = Lock()

def _read_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_cached_score(owner, repo_name):
    key = f"{owner}/{repo_name}"
    with _lock:
        data = _read_db()
        return data.get(key)

def save_score(owner, repo_name, score_data):
    key = f"{owner}/{repo_name}"
    with _lock:
        data = _read_db()
        data[key] = score_data
        _write_db(data)
