#!/usr/bin/env bash

set -euo pipefail

readonly IFACE="lo"
readonly OC_IP="127.0.0.1"
readonly CH1_PORT="8888"
readonly CH2_PORT="8889"
readonly ROOT_HANDLE="c1d1:"
readonly NETEM_HANDLE="c1d2:"
readonly IMPAIRED_CLASS="c1d1:1"

usage() {
    cat <<'EOF'
Usage:
  sudo ./scripts/network/netem.sh delay MILLISECONDS
  sudo ./scripts/network/netem.sh loss PERCENT
  sudo ./scripts/network/netem.sh duplicate PERCENT
  sudo ./scripts/network/netem.sh reorder PERCENT
  sudo ./scripts/network/netem.sh outage SECONDS
  sudo ./scripts/network/netem.sh channel1-loss
  sudo ./scripts/network/netem.sh channel2-loss
  sudo ./scripts/network/netem.sh clear
  ./scripts/network/netem.sh status
EOF
}

clear_qdisc() {
    tc qdisc del dev "$IFACE" root handle "$ROOT_HANDLE" 2>/dev/null || true
}

add_filter() {
    local port="$1"

    tc filter add dev "$IFACE" protocol ip parent "$ROOT_HANDLE" prio 1 u32 \
        match ip protocol 17 0xff \
        match ip dst "$OC_IP/32" \
        match ip dport "$port" 0xffff \
        flowid "$IMPAIRED_CLASS"
}

apply_netem() {
    local ports="$1"
    shift

    clear_qdisc
    tc qdisc add dev "$IFACE" root handle "$ROOT_HANDLE" prio bands 2 \
        priomap 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
    tc qdisc add dev "$IFACE" parent "$IMPAIRED_CLASS" handle "$NETEM_HANDLE" netem "$@"

    if [[ "$ports" == "both" ]]; then
        add_filter "$CH1_PORT"
        add_filter "$CH2_PORT"
    else
        add_filter "$ports"
    fi

    printf 'netem applied on %s\n' "$IFACE"
}

show_status() {
    tc -s qdisc show dev "$IFACE"
    tc filter show dev "$IFACE" parent "$ROOT_HANDLE" 2>/dev/null || true
}

timed_outage() {
    local seconds="$1"

    apply_netem both loss 100%
    trap clear_qdisc EXIT
    sleep "$seconds"
    clear_qdisc
    trap - EXIT
    printf 'outage finished after %s seconds\n' "$seconds"
}

command="${1:-help}"

case "$command" in
    delay)
        [[ $# == 2 ]] || { usage >&2; exit 1; }
        apply_netem both delay "${2}ms"
        ;;
    loss|duplicate)
        [[ $# == 2 ]] || { usage >&2; exit 1; }
        apply_netem both "$command" "${2}%"
        ;;
    reorder)
        [[ $# == 2 ]] || { usage >&2; exit 1; }
        apply_netem both delay 100ms reorder "${2}%"
        ;;
    outage)
        [[ $# == 2 ]] || { usage >&2; exit 1; }
        timed_outage "$2"
        ;;
    channel1-loss)
        apply_netem "$CH1_PORT" loss 100%
        ;;
    channel2-loss)
        apply_netem "$CH2_PORT" loss 100%
        ;;
    clear)
        clear_qdisc
        printf 'netem cleared from %s\n' "$IFACE"
        ;;
    status)
        show_status
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        usage >&2
        exit 1
        ;;
esac
