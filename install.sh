#!/bin/sh
set -e

REPO="MaxPer2005/maxpack"
BINARY="maxpack"
CHECKSUMS="SHA256SUMS.txt"

# Detect OS and architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Darwin) OS_TAG="darwin" ;;
    Linux)  OS_TAG="linux" ;;
    *)      echo "Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
    x86_64|amd64)   ARCH_TAG="amd64" ;;
    arm64|aarch64)   ARCH_TAG="arm64" ;;
    *)               echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

ASSET="${BINARY}-${OS_TAG}-${ARCH_TAG}"
case "${OS_TAG}-${ARCH_TAG}" in
    darwin-arm64|linux-amd64) ;;
    *)
        echo "Current release supports only macOS Apple Silicon and Linux x86_64." >&2
        echo "See https://github.com/${REPO}/releases/latest for manual downloads." >&2
        exit 1
        ;;
esac
echo "Installing ${ASSET}..."

# Get latest release download URL
DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"
CHECKSUM_URL="https://github.com/${REPO}/releases/latest/download/${CHECKSUMS}"

# Create temp file
TMP="$(mktemp)"
SUMS_TMP="$(mktemp)"
trap 'rm -f "$TMP" "$SUMS_TMP"' EXIT

download() {
    url="$1"
    out="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$out"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$out" "$url"
    else
        echo "Error: curl or wget required"; exit 1
    fi
}

# Download
download "$DOWNLOAD_URL" "$TMP"
download "$CHECKSUM_URL" "$SUMS_TMP"

EXPECTED="$(awk -v asset="$ASSET" '$2 == asset { print $1 }' "$SUMS_TMP")"
if [ -z "$EXPECTED" ]; then
    echo "Error: checksum entry for ${ASSET} not found" >&2
    exit 1
fi

if command -v shasum >/dev/null 2>&1; then
    ACTUAL="$(shasum -a 256 "$TMP" | awk '{print $1}')"
elif command -v sha256sum >/dev/null 2>&1; then
    ACTUAL="$(sha256sum "$TMP" | awk '{print $1}')"
else
    echo "Warning: no SHA-256 tool found; skipping checksum verification" >&2
    ACTUAL="$EXPECTED"
fi

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "Error: checksum verification failed for ${ASSET}" >&2
    exit 1
fi

chmod +x "$TMP"

# macOS: remove quarantine attribute to avoid Gatekeeper block
if [ "$OS" = "Darwin" ]; then
    xattr -d com.apple.quarantine "$TMP" 2>/dev/null || true
fi

# Install: prefer ~/.local/bin (no sudo), fall back to /usr/local/bin
INSTALL_DIR=""

if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    INSTALL_DIR="$HOME/.local/bin"
    cp "$TMP" "${INSTALL_DIR}/${BINARY}"
    chmod +x "${INSTALL_DIR}/${BINARY}"

    # Check if in PATH
    case ":$PATH:" in
        *":$INSTALL_DIR:"*) ;;
        *)
            echo ""
            echo "NOTE: Add ~/.local/bin to your PATH:"
            echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
            echo ""
            ;;
    esac
elif [ -w /usr/local/bin ]; then
    INSTALL_DIR="/usr/local/bin"
    cp "$TMP" "${INSTALL_DIR}/${BINARY}"
    chmod +x "${INSTALL_DIR}/${BINARY}"
else
    INSTALL_DIR="/usr/local/bin"
    echo "Installing to ${INSTALL_DIR} (requires sudo)..."
    sudo cp "$TMP" "${INSTALL_DIR}/${BINARY}"
    sudo chmod +x "${INSTALL_DIR}/${BINARY}"
fi

echo "Installed ${BINARY} to ${INSTALL_DIR}/${BINARY}"
"${INSTALL_DIR}/${BINARY}" --version 2>/dev/null || true
