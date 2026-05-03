#!/bin/bash
# Installation script for de-af package
# This script sets up de-af without requiring pip install due to sandbox restrictions

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DE_AF_DIR="$SCRIPT_DIR/de_af"

# Create symlinks in a user-accessible bin directory
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

echo "Installing de-af CLI tools to $BIN_DIR..."

# Create symlinks to the CLI scripts
ln -sf "$DE_AF_DIR/bin/de-af" "$BIN_DIR/de-af"
ln -sf "$DE_AF_DIR/bin/de-fast" "$BIN_DIR/de-fast"

echo "✓ de-af installed successfully!"
echo "✓ de-fast installed successfully!"
echo ""
echo "Make sure $BIN_DIR is in your PATH."
echo "You can add it by adding this line to your ~/.bashrc or ~/.zshrc:"
echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
