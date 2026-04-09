# otx_collect.py
import os, json, time, csv
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd
from dotenv import load_dotenv
from ioctypes import normalize_type

OTX_API = "https://otx.alienvault.com/api/v1"
STATE_FILE = Path("state.json")
OUT_DIR = Path("out")
OUT_JSON = OUT_DIR / "iocs.json"
OUT_CSV  = OUT_DIR / "iocs.csv"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# def load_state():
#     if STATE_FILE.exists():
#         return json.loads(STATE_FILE.read_text())
#     return {"modified_since": "1970-01-01T00:00:00+00:00"}  # first run: grab all

from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

STATE_FILE = Path("state.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    # First run: last 7 days (UTC)
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    return {"modified_since": seven_days_ago}


def save_state(modified_since: str):
    STATE_FILE.write_text(json.dumps({"modified_since": modified_since}, indent=2))

def fetch_pulses_since(api_key: str, modified_since: str):
    """
    Pull all subscribed pulses updated since `modified_since`.
    Handles pagination via 'next' field in response.
    """
    headers = {"X-OTX-API-KEY": api_key}
    url = f"{OTX_API}/pulses/subscribed"
    params = {"modified_since": modified_since, "limit": 100}
    all_results = []
    while True:
        r = requests.get(url, headers=headers, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        all_results.extend(results)
        nxt = data.get("next")
        if not nxt:
            break
        # 'next' is a URL with its own query; follow it directly
        url = nxt
        params = None
    return all_results

def extract_iocs_from_pulses(pulses: list[dict]) -> list[dict]:
    """
    Flatten indicators from pulses; normalize and include provenance.
    """
    out = []
    for p in pulses:
        pid = p.get("id")
        pname = p.get("name")
        ptlp = p.get("tlp", "TLP:AMBER")  # default if missing
        pmod = p.get("modified") or p.get("created")
        for ind in p.get("indicators", []):
            raw_type = ind.get("type")
            std_type = normalize_type(raw_type)
            indicator = ind.get("indicator")
            if std_type and indicator:
                out.append({
                    "type": std_type,
                    "indicator": indicator.strip(),
                    "pulse_id": pid,
                    "pulse_title": pname,
                    "pulse_tlp": ptlp,
                    "pulse_modified": pmod,
                    "source": "OTX",
                })
    # dedupe by (type, indicator)
    seen = set()
    uniq = []
    for i in out:
        key = (i["type"], i["indicator"])
        if key not in seen:
            seen.add(key); uniq.append(i)
    return uniq

def most_recent_modified(pulses: list[dict]) -> str | None:
    """
    Find the latest pulse 'modified' timestamp to advance the watermark.
    """
    best = None
    for p in pulses:
        ts = p.get("modified") or p.get("created")
        if not ts:
            continue
        if best is None or ts > best:
            best = ts
    return best

def write_outputs(iocs: list[dict]):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # JSON
    OUT_JSON.write_text(json.dumps(iocs, indent=2))
    # CSV
    cols = ["type","indicator","pulse_id","pulse_title","pulse_tlp","pulse_modified","source"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in iocs:
            w.writerow({k: row.get(k, "") for k in cols})

def main():
    load_dotenv(encoding='utf-8-sig')
    api_key = os.getenv("OTX_API_KEY")
    if not api_key:
        raise SystemExit("Missing OTX_API_KEY in .env")

    state = load_state()
    modified_since = state["modified_since"]

    print(f"[otx] fetching pulses modified since: {modified_since}")
    pulses = fetch_pulses_since(api_key, modified_since)
    print(f"[otx] pulses fetched: {len(pulses)}")

    iocs = extract_iocs_from_pulses(pulses)
    print(f"[otx] normalized unique IOCs: {len(iocs)}")

    write_outputs(iocs)
    print(f"[otx] wrote {OUT_JSON} and {OUT_CSV}")

    # advance state to latest pulse modified, if any; otherwise keep old watermark
    latest = most_recent_modified(pulses)
    if latest:
        save_state(latest)
        print(f"[otx] updated watermark -> {latest}")
    else:
        print("[otx] no new pulses; watermark unchanged.")

if __name__ == "__main__":
    main()
