#!/usr/bin/env python3
"""Ejecuta una nueva campaña de red sin sobrescribir los resultados históricos."""

import argparse
import csv
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NETEM = ROOT / "scripts/network/netem.sh"
CLOUD = ROOT / "build/bin/exe/examples/cloud_ixl"
HISTORICAL_CSV = Path(__file__).with_name("datos.csv")

CLOUD_ENV = {
    "CLOUD_IXL_RASTA_CONFIG": str(ROOT / "config/rasta_client1_local.cfg"),
    "CLOUD_IXL_OC_CH1_IP": "127.0.0.1",
    "CLOUD_IXL_OC_CH1_PORT": "8888",
    "CLOUD_IXL_OC_CH2_IP": "127.0.0.1",
    "CLOUD_IXL_OC_CH2_PORT": "8889",
}

FINAL = {
    "SCI-LS command confirmed": "confirmada",
    "SCI-LS command not confirmed": "fallida",
    "SCI-LS command rejected": "fallida",
    "SCI-LS command failed": "fallida",
}


def enter_namespace():
    if os.environ.get("NETEM_CAMPAIGN_NS") == "1":
        subprocess.run(["ip", "link", "set", "lo", "up"], check=True)
        return
    os.environ["NETEM_CAMPAIGN_NS"] = "1"
    os.execvp(
        "unshare",
        [
            "unshare",
            "--user",
            "--map-root-user",
            "--net",
            sys.executable,
            str(Path(__file__).resolve()),
            *sys.argv[1:],
        ],
    )


def launch(command, cwd, extra_env=None):
    env = os.environ.copy()
    env.update(extra_env or {})
    process = subprocess.Popen(
        ["stdbuf", "-oL", "-eL", *map(str, command)],
        cwd=cwd,
        env=env,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    process.lines = []

    def read_output():
        for line in process.stdout:
            process.lines.append((time.monotonic(), line.rstrip()))

    threading.Thread(target=read_output, daemon=True).start()
    return process


def wait_for(process, messages, timeout, start=0):
    limit = time.monotonic() + timeout
    while time.monotonic() < limit:
        for instant, line in process.lines[start:]:
            for message in messages:
                if message in line:
                    return message, instant
        if process.poll() is not None:
            break
        time.sleep(0.02)
    return None


def stop(process):
    if process.poll() is not None:
        return
    try:
        process.stdin.write("q\n")
        process.stdin.flush()
        process.wait(timeout=2)
    except (BrokenPipeError, subprocess.TimeoutExpired):
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()


def apply_netem(*arguments):
    result = subprocess.run(
        [str(NETEM), *map(str, arguments)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(result.stdout)


def read_netem_dropped():
    try:
        qdiscs = json.loads(
            subprocess.check_output(
                ["tc", "-s", "-j", "qdisc", "show", "dev", "lo"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return ""

    return next(
        (
            qdisc.get("drops", "")
            for qdisc in qdiscs
            if qdisc.get("kind") == "netem" and qdisc.get("handle") == "c1d2:"
        ),
        "",
    )

def start_pair():
    oc_binary = Path(os.environ["CLOUD_IXL_OC_BIN"]).expanduser().resolve()
    oc = launch([oc_binary], oc_binary.parent)
    if not wait_for(oc, ["Listening as LS RaSTA ID"], 8):
        stop(oc)
        raise RuntimeError("El OC no ha arrancado")
    cloud = launch([CLOUD], ROOT, CLOUD_ENV)
    if not wait_for(cloud, ["PDI: initialisation completed"], 15):
        stop(cloud)
        stop(oc)
        raise RuntimeError("No se ha establecido PDI")
    time.sleep(0.2)
    return oc, cloud


def finish_order(cloud, mark, sent, timeout=13):
    final = wait_for(cloud, FINAL, timeout, mark)
    if final:
        result = FINAL[final[0]]
    elif cloud.poll() is not None:
        result = "proceso_cerrado"
    else:
        result = "sin_respuesta"

    matched = next(
        (instant for instant, line in cloud.lines[mark:] if "Command and message match" in line),
        None,
    )
    elapsed = round((matched - sent) * 1000, 3) if sent and matched else ""
    return result, elapsed


def send_order(cloud, aspect=0):
    mark = len(cloud.lines)
    if cloud.poll() is not None:
        return "proceso_cerrado", ""
    cloud.stdin.write(f"a\n{aspect}\n")
    cloud.stdin.flush()
    sent = wait_for(cloud, ["SCI-LS signal aspect command sent"], 2, mark)
    return finish_order(cloud, mark, sent[1] if sent else None)


def normal_test(name, arguments, repetition, settle=0.25, recovery=True):
    apply_netem("clear")
    oc, cloud = start_pair()
    try:
        if arguments:
            apply_netem(*arguments)
            time.sleep(settle)
        result, elapsed = send_order(cloud)
        netem_dropped = read_netem_dropped()
        apply_netem("clear")
        recovered = send_order(cloud, 1)[0] if recovery and result == "confirmada" else ""
        return [name, repetition, result, elapsed, recovered, netem_dropped]
    finally:
        apply_netem("clear")
        stop(cloud)
        stop(oc)


def idle_outage(name, seconds):
    apply_netem("clear")
    oc, cloud = start_pair()
    try:
        apply_netem("loss", 100)
        time.sleep(seconds)
        netem_dropped = read_netem_dropped()
        apply_netem("clear")
        time.sleep(1)
        result, elapsed = send_order(cloud)
        return [name, 1, result, elapsed, result, netem_dropped]
    finally:
        apply_netem("clear")
        stop(cloud)
        stop(oc)


def pending_outage():
    apply_netem("clear")
    oc, cloud = start_pair()
    try:
        apply_netem("delay", 3000)
        mark = len(cloud.lines)
        cloud.stdin.write("a\n0\n")
        cloud.stdin.flush()
        sent = wait_for(cloud, ["SCI-LS signal aspect command sent"], 2, mark)
        apply_netem("loss", 100)
        time.sleep(5)
        netem_dropped = read_netem_dropped()
        apply_netem("clear")
        result, elapsed = finish_order(cloud, mark, sent[1] if sent else None, 9)
        return ["corte_orden_pendiente", 1, result, elapsed, "", netem_dropped]
    finally:
        apply_netem("clear")
        stop(cloud)
        stop(oc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=HISTORICAL_CSV.parent / "runs" / f"datos_{datetime.now():%Y%m%d_%H%M%S_%f}.csv",
        help="CSV nuevo; por defecto, runs/datos_<fecha_hora>.csv junto al script",
    )
    args = parser.parse_args()
    try:
        output = args.output.expanduser().resolve()
        if output == HISTORICAL_CSV.resolve():
            parser.error("datos.csv contiene la campaña histórica; elige otro archivo de salida.")
        if output.exists():
            parser.error(f"El archivo de salida ya existe; elige otro: {output}")
        value = os.environ.get("CLOUD_IXL_OC_BIN", "")
        if not value.strip():
            parser.error("Configura CLOUD_IXL_OC_BIN con la ruta al ejecutable externo del OC.")
        oc_binary = Path(value).expanduser().resolve()
        if not oc_binary.is_file() or not os.access(oc_binary, os.X_OK):
            parser.error(f"CLOUD_IXL_OC_BIN debe indicar un fichero existente y ejecutable: {oc_binary}")
        output.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    enter_namespace()
    scenarios = [
        ("sin_degradacion", (), 0.25, False),
        ("retardo_100ms", ("delay", 100), 0.25, True),
        ("retardo_500ms", ("delay", 500), 0.25, True),
        ("retardo_1000ms", ("delay", 1000), 0.25, True),
        ("retardo_3000ms", ("delay", 3000), 0.25, True),
        ("perdida_1pct", ("loss", 1), 2.25, True),
        ("perdida_5pct", ("loss", 5), 2.25, True),
        ("perdida_10pct", ("loss", 10), 2.25, True),
        ("perdida_30pct", ("loss", 30), 2.25, True),
        ("perdida_100pct", ("loss", 100), 0.25, True),
        ("duplicacion_1pct", ("duplicate", 1), 2.25, True),
        ("duplicacion_5pct", ("duplicate", 5), 2.25, True),
        ("duplicacion_10pct", ("duplicate", 10), 2.25, True),
        ("reordenamiento_5pct", ("reorder", 5), 2.25, True),
        ("reordenamiento_10pct", ("reorder", 10), 2.25, True),
        ("reordenamiento_25pct", ("reorder", 25), 2.25, True),
    ]

    rows = []
    try:
        for name, arguments, settle, recovery in scenarios:
            for repetition in range(1, 4):
                result = normal_test(name, arguments, repetition, settle, recovery)
                rows.append(result)
                print(name, repetition, result[2], flush=True)

        rows.append(idle_outage("corte_5s", 5))
        rows.append(idle_outage("corte_10s", 10))
        rows.append(pending_outage())
        rows.append(normal_test("perdida_canal_1", ("channel1-loss",), 1, 2.25))
        rows.append(normal_test("perdida_canal_2", ("channel2-loss",), 1, 2.25))
        rows.append(normal_test("recuperacion_final", (), 1, recovery=False))
    finally:
        apply_netem("clear")

    try:
        # La creación exclusiva impide sobrescribir un archivo creado durante la campaña.
        output_file = output.open("x", newline="", encoding="utf-8")
    except OSError as error:
        parser.error(f"No se puede crear el archivo de salida {output}: {error}")
    with output_file as file:
        writer = csv.writer(file)
        writer.writerow(
            ("prueba", "repeticion", "resultado", "tiempo_ms", "recuperacion", "netem_dropped")
        )
        writer.writerows(rows)
    print(f"Resultados guardados en {output}")


if __name__ == "__main__":
    main()
