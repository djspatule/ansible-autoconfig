#!/usr/bin/env bash
set -euo pipefail

# Idempotent: "--needed" skips packages that are already installed.
# Default behavior also updates your system first (-Syu). Use --no-upgrade if you don't want that.

PKGS=(
  curl
  btop
  python-psutil   # Arch name for "python3-psutil"
  micro
  fastfetch
  pdfgrep
  tldr
  ncdu
  mc
  bat
  clamav
  cmatrix
  eza
  sl
  tree
  ripgrep
  vlc
  drawing
  imagemagick
)

if ! command -v pacman >/dev/null; then
  echo "Error: pacman not found (this script is for Arch/Omarchy)."
  exit 1
fi

SUDO=""
[[ $EUID -ne 0 ]] && SUDO="sudo"

if [[ "${1-}" == "--no-upgrade" ]]; then
  # Install only (no full system upgrade)
  $SUDO pacman -S --needed "${PKGS[@]}"
else
  # Recommended on Arch: sync repos + full upgrade + install missing packages
  $SUDO pacman -Syu --needed "${PKGS[@]}"
fi
