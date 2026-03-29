#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import re
import sys


EXPECTED_RELEASE_ASSETS = {
    "libmaxpack-darwin-arm64.dylib",
    "libmaxpack-linux-amd64.so",
    "maxpack-darwin-arm64",
    "maxpack-linux-amd64",
    "maxpack.h",
    "SHA256SUMS.txt",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def parse_sha256sums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
        require(match is not None, f"Invalid SHA256SUMS line: {line!r}")
        digest, name = match.groups()
        require(name not in entries, f"Duplicate SHA256SUMS entry: {name}")
        entries[name] = digest
    return entries


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: check_release_assets.py <release-dir>")

    root = Path(sys.argv[1]).resolve()
    require(root.is_dir(), f"Release directory not found: {root}")

    present = {path.name for path in root.iterdir() if path.is_file()}
    require(
        present == EXPECTED_RELEASE_ASSETS,
        f"Release assets drifted. Expected {sorted(EXPECTED_RELEASE_ASSETS)}, got {sorted(present)}",
    )

    sums_path = root / "SHA256SUMS.txt"
    entries = parse_sha256sums(sums_path)
    expected_summed = EXPECTED_RELEASE_ASSETS - {"SHA256SUMS.txt"}
    require(
        set(entries) == expected_summed,
        f"SHA256SUMS drifted. Expected {sorted(expected_summed)}, got {sorted(entries)}",
    )

    for name, expected_digest in sorted(entries.items()):
        actual = sha256(root / name)
        require(actual == expected_digest, f"Checksum mismatch for {name}")

    print("release assets OK")


if __name__ == "__main__":
    main()
