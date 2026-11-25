"""Discover the EtherCAT terminals of a Beckhoff PLC for the EtherCAT terminal-state widgets.

READ-ONLY. This wraps exactly one read-only ads-actions command and refuses to
run anything else:

    ads read-ecat-topology <plc> --format json --port-end 65535

which returns every configured terminal (port, name, type) and its port A-D
neighbours (the tree). The result is reformatted into
the discovery JSON read by :class:`EthercatTerminalStatesStretch` and written to
the user cache (``~/.cache/ecat-states/<plc>.json``) unless ``-o`` is given.

Load ads-actions first:   ctrlenv-pathmunge ads-actions

Examples
--------
    python -m pcdswidgets.common.ethercat.discover plc-sds-raptor
    python -m pcdswidgets.common.ethercat.discover plc-sds-raptor -o plc-sds-raptor.json
    python -m pcdswidgets.common.ethercat.discover plc-sds-raptor --ethercat-master-ams-net-id 172.21.38.26.2.1
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from pcdswidgets.common.ethercat.constants import CACHE_DIR

SCHEMA_VERSION = 1

# The only ads-actions sub-command that may ever be executed (passive ADS reads).
READ_ONLY_SUBCOMMANDS = frozenset({"read-ecat-topology"})

# The released CLI defaults to --port-end 1199, which would silently drop terminals
# with higher ports (large PLCs, fixed addresses). Always scan the full ADS range.
PORT_END = 65535

# Fallback location of the released ads-actions CLI (what ctrlenv-pathmunge adds to PATH).
RELEASED_ADS = "/reg/g/pcds/pyps/apps/ads-actions/latest-released/bin/rhel9-x86_64/ads"


def resolve_output(path: str | Path | None, plc: str) -> Path:
    """
    Discovery file for ``plc`` at ``path``.

    No path -> ``~/.cache/ecat-states/<plc>.json``. A directory (an existing one, a
    path ending in ``/``, or a path without a file suffix) -> ``<path>/<plc>.json``.
    Anything else is the file itself. Missing parent directories are created on write.
    """
    if path is None or str(path).strip() == "":
        return CACHE_DIR / f"{plc}.json"
    text = str(path).strip()
    resolved = Path(text).expanduser()
    if resolved.is_dir() or text.endswith(("/", os.sep)) or (not resolved.exists() and not resolved.suffix):
        return resolved / f"{plc}.json"
    return resolved


def can_create(path: Path) -> bool:
    """True if ``path`` can be written: it is writable, or its nearest existing ancestor directory is."""
    if path.exists():
        return path.is_file() and os.access(path, os.W_OK)
    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    return parent.is_dir() and os.access(parent, os.W_OK | os.X_OK)


def writable_output(target: Path, plc: str) -> Path:
    """``target`` if it can be written, else the user cache ``~/.cache/ecat-states/<plc>.json``."""
    return target if can_create(target) else resolve_output(None, plc)


def find_ads() -> str | None:
    """Locate the ads-actions CLI: $ADS_ACTIONS_BIN, then ``ads`` on PATH, then the released install."""
    for candidate in (os.environ.get("ADS_ACTIONS_BIN"), shutil.which("ads"), RELEASED_ADS):
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    return None


def run_ads(ads: str, subcommand: str, args: list[str], timeout: float) -> str:
    """Run one read-only ads-actions sub-command and return stdout."""
    if subcommand not in READ_ONLY_SUBCOMMANDS:
        raise RuntimeError(f"refusing to run non read-only ads command: {subcommand}")
    cmd = [ads, subcommand, *args]
    print("+ " + " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{subcommand} failed (rc={proc.returncode}): {proc.stderr.strip()[-400:]}")
    return proc.stdout


def parse_topology(text: str) -> dict:
    """Decode read-ecat-topology JSON (tolerates leading diagnostic lines)."""
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in read-ecat-topology output")
    return json.loads(text[start:])


def discover(plc: str, master_ams_net_id: str | None, timeout: float) -> dict:
    ads = find_ads()
    if ads is None:
        raise RuntimeError("ads-actions not found; run `ctrlenv-pathmunge ads-actions` first")
    extra = ["--ethercat-master-ams-net-id", master_ams_net_id] if master_ams_net_id else []
    args = [plc, *extra, "--format", "json", "--port-end", str(PORT_END)]

    topo = parse_topology(run_ads(ads, "read-ecat-topology", args, timeout))
    slaves = sorted(topo.get("slaves", []), key=lambda s: int(s["port"]))
    if not slaves:
        raise RuntimeError(f"read-ecat-topology found no EtherCAT terminals on {plc}")
    listed = set((topo.get("summary") or {}).get("summary_ports") or [])
    missing = sorted(listed - {int(s["port"]) for s in slaves})
    if missing:
        print(f"warning: {len(missing)} configured port(s) not readable: {missing}", file=sys.stderr)

    terminals = [
        {
            "port": int(slave["port"]),
            "name": slave.get("device_name") or f"Port {slave['port']}",
            "type": slave.get("terminal_type") or "",
            "neighbors": {side: int(value or 0) for side, value in (slave.get("port_neighbors") or {}).items()},
        }
        for slave in slaves
    ]

    return {
        "schema": SCHEMA_VERSION,
        "plc": plc,
        "generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sources": [f"ads read-ecat-topology {' '.join(args)}"],
        "terminals": terminals,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("plc", help="PLC host name or IP, e.g. plc-sds-raptor")
    parser.add_argument(
        "-o",
        "--output",
        help="output JSON, or a directory for <dir>/<plc>.json (default: ~/.cache/ecat-states/<plc>.json)",
    )
    parser.add_argument(
        "--ethercat-master-ams-net-id",
        default=None,
        help="EtherCAT master AMS Net ID (default: let ads-actions resolve it)",
    )
    parser.add_argument("--timeout", type=float, default=300.0, help="per-command timeout in seconds (default 300)")
    args = parser.parse_args(argv)

    output = resolve_output(args.output, args.plc)
    try:
        result = discover(args.plc, args.ethercat_master_ams_net_id, args.timeout)
    except Exception as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    tmp.replace(output)
    print(f"wrote {output} ({len(result['terminals'])} terminals)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
