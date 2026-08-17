#!/usr/bin/env bash
set -euo pipefail

# Idempotent personal package installer for Arch/Omarchy.
# Default behavior updates first. Use --no-upgrade to install only.

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
  printf '%s\n' "Error: pacman not found (this script is for Arch/Omarchy)." >&2
  exit 1
fi

SUDO=""
[[ $EUID -ne 0 ]] && SUDO="sudo"

if command -v omarchy >/dev/null; then
  if [[ "${1-}" != "--no-upgrade" ]]; then
    omarchy update
  fi

  omarchy pkg add "${PKGS[@]}"
elif [[ "${1-}" == "--no-upgrade" ]]; then
  $SUDO pacman -S --needed "${PKGS[@]}"
else
  $SUDO pacman -Syu --needed "${PKGS[@]}"
fi
