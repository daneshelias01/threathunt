# ThreatHunt

Small Python utility for collecting Indicators of Compromise (IOCs) from subscribed [AlienVault OTX](https://otx.alienvault.com/) pulses and exporting them into local JSON and CSV files.

## What it does

- Pulls subscribed OTX pulses updated since the last saved watermark
- Defaults to the last 7 days on first run
- Normalizes supported IOC types into a simple hunting-friendly schema
- Deduplicates indicators by `(type, indicator)`
- Writes outputs to `out/iocs.json` and `out/iocs.csv`
- Saves the latest processed pulse timestamp to `state.json`

## Supported IOC types

The current normalization layer supports:

- `IPv4` -> `ipv4`
- `IPv6` -> `ipv6`
- `domain` -> `domain`
- `hostname` -> `domain`
- `url` / `URI` -> `url`
- `FileHash-MD5` -> `md5`
- `FileHash-SHA1` -> `sha1`
- `FileHash-SHA256` -> `sha256`
- `FileHash-SHA512` -> `sha512`

Unsupported indicator types are ignored.

## Requirements

- Python 3.10+
- An AlienVault OTX API key

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Add your OTX API key to a `.env` file.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```env
OTX_API_KEY=your_otx_api_key_here
```

## Usage

Run the collector:

```bash
python3 otx_collect.py
```

Example flow:

- Reads `OTX_API_KEY` from `.env`
- Loads `state.json` if it exists
- If no state exists, fetches pulses modified in the last 7 days
- Extracts and normalizes indicators from subscribed pulses
- Writes fresh output files to `out/`
- Updates `state.json` with the newest pulse timestamp returned

## Output

### JSON

`out/iocs.json` contains a list of normalized IOC records like:

```json
[
  {
    "type": "ipv4",
    "indicator": "1.2.3.4",
    "pulse_id": "12345",
    "pulse_title": "Example Pulse",
    "pulse_tlp": "TLP:AMBER",
    "pulse_modified": "2026-04-08T10:20:30+00:00",
    "source": "OTX"
  }
]
```

### CSV

`out/iocs.csv` contains:

- `type`
- `indicator`
- `pulse_id`
- `pulse_title`
- `pulse_tlp`
- `pulse_modified`
- `source`

## Project structure

```text
.
├── ioctypes.py       # IOC type normalization
├── otx_collect.py    # main collector script
├── requirements.txt
└── README.md
```

## Notes

- The repository currently uses `otx_collect.py` as the working entrypoint; `main.py` is empty.
- `pandas` is listed in `requirements.txt` but is not currently used by the script.
- `out/`, `.env`, and `state.json` are ignored by git.

## Next improvements

- Add CLI flags for custom date ranges and output paths
- Add logging and retry/backoff for transient API failures
- Add tests for IOC normalization and deduplication
- Add support for more OTX indicator types
