"""Log tailer: reads JSON log lines from a file or stdin and feeds them to the detector."""

import json
import sys
import time
from typing import Callable, IO, Iterator, Optional

from logdrift.detector import AnomalyDetector, AnomalyEvent


def _iter_lines(stream: IO[str], poll_interval: float = 0.1) -> Iterator[str]:
    """Yield lines from *stream*, blocking until new data arrives."""
    while True:
        line = stream.readline()
        if line:
            yield line.rstrip("\n")
        else:
            time.sleep(poll_interval)


def parse_log_line(raw: str) -> Optional[dict]:
    """Return parsed JSON dict or *None* if the line is not valid JSON."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


class LogTailer:
    """Tail a JSON log stream and report anomalies via a callback."""

    def __init__(
        self,
        detector: AnomalyDetector,
        on_anomaly: Callable[[AnomalyEvent], None],
        key_field: str = "event",
    ) -> None:
        self.detector = detector
        self.on_anomaly = on_anomaly
        self.key_field = key_field
        self._lines_read: int = 0
        self._parse_errors: int = 0

    def process_line(self, raw: str) -> Optional[AnomalyEvent]:
        """Parse *raw*, observe the event key, and return any anomaly."""
        record = parse_log_line(raw)
        if record is None:
            self._parse_errors += 1
            return None
        self._lines_read += 1
        key = record.get(self.key_field, "<unknown>")
        event = self.detector.observe(str(key))
        if event is not None:
            self.on_anomaly(event)
        return event

    def tail(self, stream: IO[str] = sys.stdin, poll_interval: float = 0.1) -> None:
        """Block and process lines from *stream* until interrupted."""
        for line in _iter_lines(stream, poll_interval=poll_interval):
            self.process_line(line)

    @property
    def stats(self) -> dict:
        return {
            "lines_read": self._lines_read,
            "parse_errors": self._parse_errors,
        }
