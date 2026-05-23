"""Command-line entry point for logdrift."""

import argparse
import sys

from logdrift.detector import AnomalyDetector
from logdrift.tailer import LogTailer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logdrift",
        description="Tail JSON logs and detect anomalous event-rate spikes.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Path to a JSON log file, or '-' to read from stdin (default: stdin).",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Rolling baseline window in seconds (default: 60).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        metavar="MULTIPLIER",
        help="Alert when rate exceeds baseline * MULTIPLIER (default: 3.0).",
    )
    parser.add_argument(
        "--key-field",
        default="event",
        metavar="FIELD",
        help="JSON field used as the event key (default: 'event').",
    )
    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    detector = AnomalyDetector(window_seconds=args.window, threshold=args.threshold)

    def _print_anomaly(event):
        print(f"[ANOMALY] {event}", file=sys.stderr, flush=True)

    tailer = LogTailer(detector, on_anomaly=_print_anomaly, key_field=args.key_field)

    if args.file == "-":
        stream = sys.stdin
    else:
        try:
            stream = open(args.file, "r")  # noqa: WPS515
        except OSError as exc:
            print(f"logdrift: cannot open '{args.file}': {exc}", file=sys.stderr)
            return 1

    try:
        tailer.tail(stream)
    except KeyboardInterrupt:
        stats = tailer.stats
        print(
            f"\nlogdrift: stopped — "
            f"{stats['lines_read']} lines processed, "
            f"{stats['parse_errors']} parse errors.",
            file=sys.stderr,
        )
    finally:
        if stream is not sys.stdin:
            stream.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
