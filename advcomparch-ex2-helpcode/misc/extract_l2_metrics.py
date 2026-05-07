#!/usr/bin/env python3

import argparse
import csv
import re
from pathlib import Path


STAT_RE = re.compile(
    r"^(L[12])-(Load|Store|Total)-(Hits|Misses|Accesses):\s+(\d+)\s+([0-9.]+)%"
)

FILENAME_RE = re.compile(
    r".*cslab_cache_stats_L2_(?P<policy>[A-Za-z0-9]+)_(?P<l2_size>\d+)_(?P<l2_assoc>\d+)_(?P<l2_block>\d+)\.out$"
)


def safe_int(value):
    return int(value) if value not in (None, "") else None


def safe_float(value):
    return float(value) if value not in (None, "") else None


def div(num, den):
    if den is None or den == 0 or num is None:
        return None
    return num / den


def parse_out_file(path: Path):
    text = path.read_text(errors="replace").splitlines()

    row = {
        "file": str(path),
        "benchmark": path.parent.name,
        "policy": None,

        "total_instructions": None,
        "total_cycles": None,
        "ipc_reported": None,
        "ipc_computed": None,

        "l1_size_kb": None,
        "l1_block_b": None,
        "l1_assoc": None,

        "l2_size_kb": None,
        "l2_block_b": None,
        "l2_assoc": None,

        "l1_latency": None,
        "l2_latency": None,
        "mem_latency": None,
    }

    # Fallback config/policy from filename
    m = FILENAME_RE.match(path.name)
    if m:
        row["policy"] = m.group("policy")
        row["l2_size_kb_filename"] = safe_int(m.group("l2_size"))
        row["l2_assoc_filename"] = safe_int(m.group("l2_assoc"))
        row["l2_block_b_filename"] = safe_int(m.group("l2_block"))
    else:
        row["l2_size_kb_filename"] = None
        row["l2_assoc_filename"] = None
        row["l2_block_b_filename"] = None

    section = None

    for line in text:
        stripped = line.strip()

        # Total statistics
        if stripped.startswith("Total Instructions:"):
            row["total_instructions"] = safe_int(stripped.split(":", 1)[1].strip())
            continue

        if stripped.startswith("Total Cycles:"):
            row["total_cycles"] = safe_int(stripped.split(":", 1)[1].strip())
            continue

        if stripped.startswith("IPC:"):
            row["ipc_reported"] = safe_float(stripped.split(":", 1)[1].strip())
            continue

        # Cache config sections
        if stripped == "L1-Data Cache:":
            section = "l1"
            continue

        if stripped == "L2-Data Cache:":
            section = "l2"
            continue

        if stripped.startswith("Size(KB):") and section in ("l1", "l2"):
            row[f"{section}_size_kb"] = safe_int(stripped.split(":", 1)[1].strip())
            continue

        if stripped.startswith("Block Size(B):") and section in ("l1", "l2"):
            row[f"{section}_block_b"] = safe_int(stripped.split(":", 1)[1].strip())
            continue

        if stripped.startswith("Associativity:") and section in ("l1", "l2"):
            row[f"{section}_assoc"] = safe_int(stripped.split(":", 1)[1].strip())
            continue

        # Latencies
        if stripped.startswith("Latencies:"):
            parts = stripped.split(":", 1)[1].split()
            if len(parts) >= 3:
                row["l1_latency"] = safe_int(parts[0])
                row["l2_latency"] = safe_int(parts[1])
                row["mem_latency"] = safe_int(parts[2])
            continue

        # Replacement policy, e.g. L1-Sets:  256 - LRU - assoc:   4
        if stripped.startswith("L2-Sets:"):
            parts = stripped.split("-")
            if len(parts) >= 2:
                row["policy"] = parts[1].strip()
            continue

        # Cache stats
        sm = STAT_RE.match(stripped)
        if sm:
            level, access_type, metric, value, pct = sm.groups()

            key_base = f"{level.lower()}_{access_type.lower()}_{metric.lower()}"
            row[key_base] = safe_int(value)
            row[f"{key_base}_pct"] = safe_float(pct)

    # Derived metrics
    instr = row["total_instructions"]
    cycles = row["total_cycles"]

    row["ipc_computed"] = div(instr, cycles)

    # Total miss rates as fractions, not percentages
    row["l1_total_miss_rate"] = div(
        row.get("l1_total_misses"),
        row.get("l1_total_accesses")
    )

    row["l2_total_miss_rate"] = div(
        row.get("l2_total_misses"),
        row.get("l2_total_accesses")
    )

    row["l1_load_miss_rate"] = div(
        row.get("l1_load_misses"),
        row.get("l1_load_accesses")
    )

    row["l1_store_miss_rate"] = div(
        row.get("l1_store_misses"),
        row.get("l1_store_accesses")
    )

    row["l2_load_miss_rate"] = div(
        row.get("l2_load_misses"),
        row.get("l2_load_accesses")
    )

    row["l2_store_miss_rate"] = div(
        row.get("l2_store_misses"),
        row.get("l2_store_accesses")
    )

    # MPKI = Misses Per Kilo Instructions = misses / instructions * 1000
    row["l1_total_mpki"] = div(row.get("l1_total_misses"), instr)
    row["l2_total_mpki"] = div(row.get("l2_total_misses"), instr)
    row["l1_load_mpki"] = div(row.get("l1_load_misses"), instr)
    row["l1_store_mpki"] = div(row.get("l1_store_misses"), instr)
    row["l2_load_mpki"] = div(row.get("l2_load_misses"), instr)
    row["l2_store_mpki"] = div(row.get("l2_store_misses"), instr)

    for key in [
        "l1_total_mpki",
        "l2_total_mpki",
        "l1_load_mpki",
        "l1_store_mpki",
        "l2_load_mpki",
        "l2_store_mpki",
    ]:
        if row[key] is not None:
            row[key] *= 1000.0

    # Main memory accesses correspond to L2 misses
    row["mem_accesses"] = row.get("l2_total_misses")
    row["mem_mpki"] = div(row["mem_accesses"], instr)
    if row["mem_mpki"] is not None:
        row["mem_mpki"] *= 1000.0

    return row


def find_out_files(input_dir: Path):
    files = []

    for path in input_dir.rglob("*.out"):
        # Ignore files like something.out.time
        if path.name.endswith(".out.time"):
            continue

        # Also ignore any accidental time/log files
        if ".out.time" in path.name:
            continue

        files.append(path)

    return sorted(files)


def write_csv(rows, output_path: Path):
    if not rows:
        raise RuntimeError("No rows to write.")

    preferred_columns = [
        "benchmark",
        "policy",
        "file",

        "l1_size_kb",
        "l1_assoc",
        "l1_block_b",
        "l2_size_kb",
        "l2_assoc",
        "l2_block_b",

        "l1_latency",
        "l2_latency",
        "mem_latency",

        "total_instructions",
        "total_cycles",
        "ipc_reported",
        "ipc_computed",

        "l1_total_accesses",
        "l1_total_hits",
        "l1_total_misses",
        "l1_total_miss_rate",
        "l1_total_mpki",

        "l2_total_accesses",
        "l2_total_hits",
        "l2_total_misses",
        "l2_total_miss_rate",
        "l2_total_mpki",

        "mem_accesses",
        "mem_mpki",

        "l1_load_accesses",
        "l1_load_hits",
        "l1_load_misses",
        "l1_load_miss_rate",
        "l1_load_mpki",

        "l1_store_accesses",
        "l1_store_hits",
        "l1_store_misses",
        "l1_store_miss_rate",
        "l1_store_mpki",

        "l2_load_accesses",
        "l2_load_hits",
        "l2_load_misses",
        "l2_load_miss_rate",
        "l2_load_mpki",

        "l2_store_accesses",
        "l2_store_hits",
        "l2_store_misses",
        "l2_store_miss_rate",
        "l2_store_mpki",

        "l2_size_kb_filename",
        "l2_assoc_filename",
        "l2_block_b_filename",
    ]

    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())

    extra_columns = sorted(all_keys - set(preferred_columns))
    columns = preferred_columns + extra_columns

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def sort_key(row):
    return (
        row.get("benchmark") or "",
        row.get("l2_size_kb") or 0,
        row.get("l2_assoc") or 0,
        row.get("l2_block_b") or 0,
        row.get("policy") or "",
        row.get("file") or "",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract IPC, miss rates and MPKI from PIN cache simulator .out files."
    )

    parser.add_argument(
        "--input",
        "-i",
        default="outputs/L2_cache",
        help="Input L2_cache directory. Default: outputs/L2_cache"
    )

    parser.add_argument(
        "--output",
        "-o",
        default="outputs/l2_cache_metrics.csv",
        help="Output CSV path. Default: outputs/l2_cache_metrics.csv"
    )

    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    out_files = find_out_files(input_dir)

    if not out_files:
        raise RuntimeError(f"No .out files found under: {input_dir}")

    rows = []

    for path in out_files:
        try:
            rows.append(parse_out_file(path))
        except Exception as exc:
            print(f"WARNING: failed to parse {path}: {exc}")

    rows.sort(key=sort_key)

    write_csv(rows, output_path)

    print(f"Parsed .out files: {len(rows)}")
    print(f"Wrote CSV: {output_path}")

    expected_per_benchmark = {}
    for row in rows:
        b = row["benchmark"]
        expected_per_benchmark[b] = expected_per_benchmark.get(b, 0) + 1

    print("")
    print("Files per benchmark:")
    for bench, count in sorted(expected_per_benchmark.items()):
        print(f"  {bench}: {count}")


if __name__ == "__main__":
    main()