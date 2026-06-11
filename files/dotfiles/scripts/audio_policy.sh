#!/bin/bash

# Audio routing policy for Omarchy systems with split speaker/headphone profiles.
# If you move to a new laptop, verify these assumptions first:
# - `pactl list cards` shows one built-in `alsa_card.pci-*` audio device
# - the built-in card has profiles containing `Headphones` and `Speaker`
# - `pactl list sinks short` and `pactl list sources short` expose HiFi nodes
#   ending in `Headphones`, `Speaker`, `Mic1`, and `Mic2`
# If those names differ, update the regex helpers below before enabling the
# service on the new machine.

set -u

builtin_card() {
  pactl list cards short | awk '$2 ~ /^alsa_card[.]pci-/ { print $2; exit }'
}

profile_name() {
  local needle="$1"
  local card
  card="$(builtin_card)"

  [[ -n "$card" ]] || return 1

  pactl list cards | awk -v card="$card" -v needle="$needle" '
    $1 == "Name:" { in_card = ($2 == card) }
    in_card && $0 ~ /^[[:space:]]*Profiles:/ { in_profiles = 1; next }
    in_card && in_profiles && $0 ~ /^[[:space:]]*Active Profile:/ { next }
    in_card && in_profiles && $0 ~ /^[[:space:]]*Ports:/ { exit }
    in_card && in_profiles {
      line = $0
      sub(/^[[:space:]]+/, "", line)
      split(line, parts, ":")
      if (parts[1] ~ needle) {
        print parts[1]
        exit
      }
    }
  '
}

first_sink_matching() {
  local pattern="$1"
  pactl list sinks short | awk -v pattern="$pattern" '$2 ~ pattern { print $2; exit }'
}

first_source_matching() {
  local pattern="$1"
  pactl list sources short | awk -v pattern="$pattern" '$2 ~ pattern { print $2; exit }'
}

headphones_sink() {
  first_sink_matching '^alsa_output[.]pci-.*[.]HiFi__Headphones__sink$'
}

speaker_sink() {
  first_sink_matching '^alsa_output[.]pci-.*[.]HiFi__Speaker__sink$'
}

mic2_source() {
  first_source_matching '^alsa_input[.]pci-.*[.]HiFi__Mic2__source$'
}

mic1_source() {
  first_source_matching '^alsa_input[.]pci-.*[.]HiFi__Mic1__source$'
}

webcam_source() {
  first_source_matching '^alsa_input[.]usb-.*[.]analog-stereo$'
}

have_sink() {
  pactl list sinks short | rg -q "^[0-9]+\s+${1//./\\.}(\s|$)"
}

have_source() {
  pactl list sources short | rg -q "^[0-9]+\s+${1//./\\.}(\s|$)"
}

first_bluetooth_sink() {
  pactl list sinks short | awk '$2 ~ /^bluez_output\./ { print $2; exit }'
}

headphones_connected() {
  pactl list cards | rg -q '\[Out\] Headphones:.*,[[:space:]]available\)$'
}

set_profile() {
  local profile="$1"
  local card
  card="$(builtin_card)"

  [[ -n "$card" && -n "$profile" ]] || return 0
  pactl set-card-profile "$card" "$profile" || true
}

set_default_sink() {
  local sink="$1"
  pactl set-default-sink "$sink" || return 0

  pactl list sink-inputs short | while read -r input_id _; do
    pactl move-sink-input "$input_id" "$sink" >/dev/null 2>&1 || true
  done
}

set_default_source() {
  local source="$1"
  pactl set-default-source "$source" || return 0

  pactl list source-outputs short | while read -r output_id _; do
    pactl move-source-output "$output_id" "$source" >/dev/null 2>&1 || true
  done
}

apply_source_policy() {
  local mic2 mic1 webcam
  mic2="$(mic2_source)"
  mic1="$(mic1_source)"
  webcam="$(webcam_source)"

  if headphones_connected && [[ -n "$mic2" ]] && have_source "$mic2"; then
    set_default_source "$mic2"
  elif [[ -n "$mic1" ]] && have_source "$mic1"; then
    set_default_source "$mic1"
  elif [[ -n "$mic2" ]] && have_source "$mic2"; then
    set_default_source "$mic2"
  elif [[ -n "$webcam" ]] && have_source "$webcam"; then
    set_default_source "$webcam"
  fi
}

apply_output_policy() {
  local bt_sink hp_profile sp_profile hp_sink sp_sink
  bt_sink="$(first_bluetooth_sink)"
  hp_profile="$(profile_name "Headphones")"
  sp_profile="$(profile_name "Speaker")"
  hp_sink="$(headphones_sink)"
  sp_sink="$(speaker_sink)"

  if headphones_connected; then
    set_profile "$hp_profile"
    sleep 0.5
    hp_sink="$(headphones_sink)"
    if [[ -n "$hp_sink" ]] && have_sink "$hp_sink"; then
      set_default_sink "$hp_sink"
      return
    fi
  fi

  set_profile "$sp_profile"
  sleep 0.5

  if [[ -n "$bt_sink" ]] && have_sink "$bt_sink"; then
    set_default_sink "$bt_sink"
    return
  fi

  sp_sink="$(speaker_sink)"
  if [[ -n "$sp_sink" ]] && have_sink "$sp_sink"; then
    set_default_sink "$sp_sink"
  fi
}

snapshot_state() {
  local hp_state bt_sink

  if headphones_connected; then
    hp_state=1
  else
    hp_state=0
  fi

  bt_sink="$(first_bluetooth_sink)"
  printf '%s|%s\n' "$hp_state" "$bt_sink"
}

relevant_event() {
  local event="$1"

  [[ $event == *" on card "* || $event == *" on sink "* || $event == *" on source "* ]]
}

wait_for_audio() {
  for _ in $(seq 1 40); do
    if pactl info >/dev/null 2>&1; then
      return
    fi
    sleep 0.25
  done
}

main() {
  local last_state new_state event

  wait_for_audio
  apply_output_policy
  apply_source_policy
  last_state="$(snapshot_state)"

  while read -r event; do
    relevant_event "$event" || continue

    new_state="$(snapshot_state)"
    if [[ "$new_state" != "$last_state" ]]; then
      apply_output_policy
      apply_source_policy
      last_state="$new_state"
    fi
  done < <(pactl subscribe)
}

main "$@"
