# logdrift

A log tailing utility that detects anomalous patterns in structured JSON logs using rolling baselines.

---

## Installation

```bash
pip install logdrift
```

Or install from source:

```bash
git clone https://github.com/youruser/logdrift.git
cd logdrift && pip install -e .
```

---

## Usage

Tail a log file and detect anomalies in real time:

```bash
logdrift tail --file /var/log/app/output.log --window 5m --threshold 2.5
```

Use it as a library in your own code:

```python
from logdrift import LogTailer, BaselineDetector

detector = BaselineDetector(window="5m", threshold=2.5)
tailer = LogTailer(path="/var/log/app/output.log", detector=detector)

for anomaly in tailer.stream():
    print(f"[ANOMALY] {anomaly.timestamp} — {anomaly.message}")
```

**Key options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--file` | Path to the JSON log file | required |
| `--window` | Rolling baseline window size | `10m` |
| `--threshold` | Standard deviations before alerting | `3.0` |
| `--field` | JSON field to monitor | `level` |

---

## How It Works

logdrift maintains a rolling statistical baseline over a configurable time window. As new log entries arrive, each entry is scored against the baseline. When a field's frequency or value drifts beyond the configured threshold, an anomaly event is emitted.

---

## License

MIT © 2024 Your Name