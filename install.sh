#!/bin/sh
set -e

REPO="PerSerMax/maxpack"
BINARY="maxpack"

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
echo "Installing ${ASSET}..."

# Get latest release download URL
DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"

# Create temp file
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

# Download
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$DOWNLOAD_URL" -o "$TMP"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TMP" "$DOWNLOAD_URL"
else
    echo "Error: curl or wget required"; exit 1
fi

chmod +x "$TMP"

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
