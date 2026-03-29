#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter


TIME_REAL_RE = re.compile(r"^real\s+([0-9]+(?:\.[0-9]+)?)$")
TIME_RSS_RE_BSD = re.compile(r"^\s*([0-9]+)\s+maximum resident set size$")
TIME_RSS_RE_GNU = re.compile(r"^\s*Maximum resident set size \(kbytes\):\s*([0-9]+)$")


@dataclass
class RunResult:
    wall_s: float
    rss_bytes: int | None
    archive_bytes: int


@dataclass
class DatasetSummary:
    dataset: str
    input_bytes: int
    runs: list[RunResult]
    median_wall_s: float
    best_wall_s: float
    median_rss_bytes: int | None
    archive_bytes: int
    ratio_x: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a simple maxpack benchmark on one or more dataset directories."
    )
    parser.add_argument("datasets", nargs="+", help="Dataset directories to benchmark")
    parser.add_argument(
        "--binary",
        default=os.environ.get("MAXPACK_BINARY", "maxpack"),
        help="Path to the maxpack binary (default: MAXPACK_BINARY or `maxpack` from PATH)",
    )
    parser.add_argument("--mode", default="fast", choices=["fast", "efficient"])
    parser.add_argument("--global-zstd-level", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    return parser.parse_args()


def input_bytes(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            full = Path(root) / name
            try:
                if full.is_symlink():
                    total += len(os.readlink(full))
                else:
                    total += full.stat().st_size
            except FileNotFoundError:
                continue
    return total


def run_once(binary: str, dataset: Path, mode: str, global_zstd_level: int) -> RunResult:
    with tempfile.TemporaryDirectory(prefix=f"maxpack-public-smoke-{dataset.name}-") as tempdir:
        out_path = Path(tempdir) / f"{dataset.name}.maxpack"
        if sys.platform == "darwin":
            time_prefix = ["/usr/bin/time", "-lp"]
        elif sys.platform.startswith("linux"):
            time_prefix = ["/usr/bin/time", "-v"]
        else:
            time_prefix = []
        cmd = [
            *time_prefix,
            binary,
            "--accept-license",
            "pack",
            str(dataset),
            "--output",
            str(out_path),
            "--global-zstd-level",
            str(global_zstd_level),
            "--mode",
            mode,
        ]
        started = perf_counter()
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        ended = perf_counter()
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            raise SystemExit(proc.returncode)

        rss_bytes = None
        real_s = None
        for line in proc.stderr.splitlines():
            match = TIME_REAL_RE.match(line.strip())
            if match:
                real_s = float(match.group(1))
                continue
            match = TIME_RSS_RE_BSD.match(line.strip())
            if match:
                rss_bytes = int(match.group(1))
                continue
            match = TIME_RSS_RE_GNU.match(line.strip())
            if match:
                rss_bytes = int(match.group(1)) * 1024

        wall_s = real_s if real_s is not None else (ended - started)
        archive_bytes = out_path.stat().st_size
        return RunResult(wall_s=wall_s, rss_bytes=rss_bytes, archive_bytes=archive_bytes)


def summarize(dataset: Path, input_size: int, runs: list[RunResult]) -> DatasetSummary:
    walls = [run.wall_s for run in runs]
    rss_values = [run.rss_bytes for run in runs if run.rss_bytes is not None]
    archive_bytes = runs[0].archive_bytes
    return DatasetSummary(
        dataset=dataset.name,
        input_bytes=input_size,
        runs=runs,
        median_wall_s=statistics.median(walls),
        best_wall_s=min(walls),
        median_rss_bytes=int(statistics.median(rss_values)) if rss_values else None,
        archive_bytes=archive_bytes,
        ratio_x=(input_size / archive_bytes) if archive_bytes else 0.0,
    )


def print_summary(results: list[DatasetSummary]) -> None:
    for result in results:
        rss = (
            f"{result.median_rss_bytes / (1024 * 1024):.0f} MB"
            if result.median_rss_bytes is not None
            else "n/a"
        )
        run_str = ", ".join(f"{run.wall_s:.2f}s" for run in result.runs)
        print(
            f"{result.dataset}: median {result.median_wall_s:.2f}s, "
            f"best {result.best_wall_s:.2f}s, ratio {result.ratio_x:.1f}x, "
            f"archive {result.archive_bytes:,} B, peak RSS {rss}"
        )
        print(f"  runs: {run_str}")


def main() -> int:
    args = parse_args()
    results: list[DatasetSummary] = []
    for dataset_str in args.datasets:
        dataset = Path(dataset_str)
        if not dataset.exists():
            raise SystemExit(f"dataset not found: {dataset}")
        total_bytes = input_bytes(dataset)
        for _ in range(args.warmups):
            run_once(args.binary, dataset, args.mode, args.global_zstd_level)
        runs = [
            run_once(args.binary, dataset, args.mode, args.global_zstd_level)
            for _ in range(args.runs)
        ]
        results.append(summarize(dataset, total_bytes, runs))

    print_summary(results)
    if args.json_out:
        payload = [asdict(result) for result in results]
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
