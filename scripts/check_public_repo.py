#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LICENSE = ROOT / "LICENSE.md"
INSTALL = ROOT / "install.sh"
SUMS = ROOT / "SHA256SUMS.txt"
DOCS = ROOT / "docs" / "index.html"

EXPECTED_CLI = {
    "maxpack-darwin-arm64",
    "maxpack-linux-amd64",
}
EXPECTED_FFI = {
    "libmaxpack-darwin-arm64.dylib",
    "libmaxpack-linux-amd64.so",
}
EXPECTED_SUMS = EXPECTED_CLI | EXPECTED_FFI | {"maxpack.h"}


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def parse_sha256sums(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
        require(match is not None, f"Invalid SHA256SUMS line: {line!r}")
        digest, name = match.groups()
        require(name not in entries, f"Duplicate SHA256SUMS entry: {name}")
        entries[name] = digest
    return entries


def main() -> None:
    for path in (
        README,
        LICENSE,
        INSTALL,
        SUMS,
        DOCS,
        ROOT / "benchmarks_curves.png",
        ROOT / "sqrt_ratio_growth.png",
        ROOT / "maxpack.h",
    ):
        require(path.exists(), f"Missing required file: {path}")

    readme = README.read_text()
    license_text = LICENSE.read_text()
    install = INSTALL.read_text()
    docs = DOCS.read_text()

    require(
        "https://raw.githubusercontent.com/MaxPer2005/maxpack/main/install.sh | sh" in readme,
        "README quick-install command is missing or points at the wrong repo",
    )
    require(
        "25 GB per archive" in readme,
        "README no longer advertises the expected 25 GB free-tier limit",
    )
    require(
        "25 GB per archive creation or archive update operation" in license_text,
        "LICENSE no longer matches the expected free-tier limit wording",
    )
    require(
        'REPO="MaxPer2005/maxpack"' in install,
        "install.sh points at the wrong GitHub repository",
    )
    require(
        "darwin-arm64|linux-amd64" in install,
        "install.sh supported matrix drifted from the public contract",
    )

    for asset in sorted(EXPECTED_CLI | EXPECTED_FFI):
        require(f"`{asset}`" in readme, f"README is missing supported asset {asset}")

    require(
        "docs/index.html" in readme,
        "README no longer links to the public benchmark methodology page",
    )
    require(
        "../benchmarks_curves.png" in docs and "../sqrt_ratio_growth.png" in docs,
        "docs/index.html no longer references the expected plot assets",
    )
    require(
        "../README.md" in docs,
        "docs/index.html no longer links back to the repository README",
    )

    entries = parse_sha256sums(SUMS.read_text())
    require(
        set(entries) == EXPECTED_SUMS,
        f"SHA256SUMS entries drifted. Expected {sorted(EXPECTED_SUMS)}, got {sorted(entries)}",
    )

    print("public repo surface OK")


if __name__ == "__main__":
    main()
