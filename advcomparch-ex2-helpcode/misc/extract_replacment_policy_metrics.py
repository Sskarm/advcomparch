#!/usr/bin/env python3

import argparse
import csv
import re
from pathlib import Path


# Example filename:
# 403.gcc.cslab_cache_stats_L2_Random_1024_08_256.out
FILENAME_RE = re.compile(
    r"^(?P<benchmark>.+?)\.cslab_cache_stats_L2_"
    r"(?P<policy>.+?)_"
    r"(?P<l2_size>\d+)_"
    r"(?P<l2_assoc>\d+)_"
    r"(?P<l2_block>\d+)\.out$"
)

STAT_RE = re.compile(
    r"^(L[12])-(Load|Store|Total)-(Hits|Misses|Accesses):\s+(\d+)\s+([0-9.]+)%"
)


def to_int(x):
    return int(x) if x not in (None, "") else None


def to_float(x):
    return float(x) if x not in (None, "") else None


def safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def parse_filename(path: Path):
    match = FILENAME_RE.match(path.name)

    if not match:
        raise ValueError(f"Filename does not match expected format: {path.name}")

    return {
        "benchmark": match.group("benchmark"),
        "replacement_policy": match.group("policy"),
        "l2_size_kb": int(match.group("l2_size")),
        "l2_assoc": int(match.group("l2_assoc")),
        "l2_block_b": int(match.group("l2_block")),
    }


def parse_out_file(path: Path):
    filename_data = parse_filename(path)

    row = {
        "file": str(path),
        **filename_data,

        "total_instructions": None,
        "total_cycles": None,
        "ipc_reported": None,
        "ipc_computed": None,

        "l1_size_kb": None,
        "l1_assoc": None,
        "l1_block_b": None,

        "l2_size_kb_from_file": None,
        "l2_assoc_from_file": None,
        "l2_block_b_from_file": None,

        "l1_latency": None,
        "l2_latency": None,
        "mem_latency": None,

        # Useful for debugging only.
        # Policy used in analysis comes from filename, not from these.
        "policy_printed_l1": None,
        "policy_printed_l2": None,
    }

    section = None

    for raw_line in path.read_text(errors="replace").splitlines():
        line = raw_line.strip()

        if line.startswith("Total Instructions:"):
            row["total_instructions"] = to_int(line.split(":", 1)[1].strip())
            continue

        if line.startswith("Total Cycles:"):
            row["total_cycles"] = to_int(line.split(":", 1)[1].strip())
            continue

        if line.startswith("IPC:"):
            row["ipc_reported"] = to_float(line.split(":", 1)[1].strip())
            continue

        if line == "L1-Data Cache:":
            section = "l1"
            continue

        if line == "L2-Data Cache:":
            section = "l2"
            continue

        if line.startswith("Size(KB):"):
            value = to_int(line.split(":", 1)[1].strip())
            if section == "l1":
                row["l1_size_kb"] = value
            elif section == "l2":
                row["l2_size_kb_from_file"] = value
            continue

        if line.startswith("Block Size(B):"):
            value = to_int(line.split(":", 1)[1].strip())
            if section == "l1":
                row["l1_block_b"] = value
            elif section == "l2":
                row["l2_block_b_from_file"] = value
            continue

        if line.startswith("Associativity:"):
            value = to_int(line.split(":", 1)[1].strip())
            if section == "l1":
                row["l1_assoc"] = value
            elif section == "l2":
                row["l2_assoc_from_file"] = value
            continue

        if line.startswith("Latencies:"):
            parts = line.split(":", 1)[1].split()
            if len(parts) >= 3:
                row["l1_latency"] = to_int(parts[0])
                row["l2_latency"] = to_int(parts[1])
                row["mem_latency"] = to_int(parts[2])
            continue

        if line.startswith("L1-Sets:"):
            # Example: L1-Sets:  256 - MRU - assoc:   4
            parts = [p.strip() for p in line.split("-")]
            if len(parts) >= 2:
                row["policy_printed_l1"] = parts[1]
            continue

        if line.startswith("L2-Sets:"):
            # Example: L2-Sets:  512 - MRU - assoc:   8
            parts = [p.strip() for p in line.split("-")]
            if len(parts) >= 2:
                row["policy_printed_l2"] = parts[1]
            continue

        stat_match = STAT_RE.match(line)
        if stat_match:
            level, access_type, metric, value, pct = stat_match.groups()

            key = f"{level.lower()}_{access_type.lower()}_{metric.lower()}"
            row[key] = to_int(value)
            row[f"{key}_pct"] = to_float(pct)

    instr = row["total_instructions"]
    cycles = row["total_cycles"]

    row["ipc_computed"] = safe_div(instr, cycles)

    # Miss rates as fractions, e.g. 0.1509, not 15.09.
    row["l1_total_miss_rate"] = safe_div(
        row.get("l1_total_misses"),
        row.get("l1_total_accesses")
    )

    row["l2_total_miss_rate"] = safe_div(
        row.get("l2_total_misses"),
        row.get("l2_total_accesses")
    )

    row["l1_load_miss_rate"] = safe_div(
        row.get("l1_load_misses"),
        row.get("l1_load_accesses")
    )

    row["l1_store_miss_rate"] = safe_div(
        row.get("l1_store_misses"),
        row.get("l1_store_accesses")
    )

    row["l2_load_miss_rate"] = safe_div(
        row.get("l2_load_misses"),
        row.get("l2_load_accesses")
    )

    row["l2_store_miss_rate"] = safe_div(
        row.get("l2_store_misses"),
        row.get("l2_store_accesses")
    )

    # MPKI = misses / instructions * 1000
    row["l1_total_mpki"] = safe_div(row.get("l1_total_misses"), instr)
    row["l2_total_mpki"] = safe_div(row.get("l2_total_misses"), instr)
    row["l1_load_mpki"] = safe_div(row.get("l1_load_misses"), instr)
    row["l1_store_mpki"] = safe_div(row.get("l1_store_misses"), instr)
    row["l2_load_mpki"] = safe_div(row.get("l2_load_misses"), instr)
    row["l2_store_mpki"] = safe_div(row.get("l2_store_misses"), instr)

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

    # Main memory accesses are L2 misses.
    row["mem_accesses"] = row.get("l2_total_misses")
    row["mem_mpki"] = safe_div(row["mem_accesses"], instr)

    if row["mem_mpki"] is not None:
        row["mem_mpki"] *= 1000.0

    return row


def find_result_files(input_dir: Path):
    result_files = []

    for path in input_dir.rglob("*.out"):
        # This ignores .out.time because those files do not end exactly in .out.
        if path.name.endswith(".out.time"):
            continue

        if path.is_file():
            result_files.append(path)

    return sorted(result_files)


def write_csv(rows, output_path: Path):
    preferred_columns = [
        "benchmark",
        "replacement_policy",

        "l2_size_kb",
        "l2_assoc",
        "l2_block_b",

        "ipc_reported",
        "ipc_computed",

        "l2_total_mpki",
        "l2_total_miss_rate",
        "l1_total_mpki",
        "l1_total_miss_rate",

        "total_instructions",
        "total_cycles",

        "l1_size_kb",
        "l1_assoc",
        "l1_block_b",

        "l1_latency",
        "l2_latency",
        "mem_latency",

        "l1_total_accesses",
        "l1_total_hits",
        "l1_total_misses",

        "l2_total_accesses",
        "l2_total_hits",
        "l2_total_misses",

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

        "l2_size_kb_from_file",
        "l2_assoc_from_file",
        "l2_block_b_from_file",

        "policy_printed_l1",
        "policy_printed_l2",

        "file",
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
        row.get("benchmark", ""),
        row.get("replacement_policy", ""),
        row.get("l2_size_kb", 0),
        row.get("l2_assoc", 0),
        row.get("l2_block_b", 0),
        row.get("file", ""),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract replacement policy experiment metrics from PIN .out files."
    )

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input directory containing benchmark folders with .out files."
    )

    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output CSV file."
    )

    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    files = find_result_files(input_dir)

    if not files:
        raise RuntimeError(f"No .out files found under: {input_dir}")

    rows = []

    skipped = []

    for path in files:
        try:
            rows.append(parse_out_file(path))
        except Exception as exc:
            skipped.append((path, str(exc)))

    rows.sort(key=sort_key)

    write_csv(rows, output_path)

    print(f"Input directory: {input_dir}")
    print(f"Parsed .out files: {len(rows)}")
    print(f"Skipped files: {len(skipped)}")
    print(f"Output CSV: {output_path}")

    if skipped:
        print("")
        print("Skipped files:")
        for path, reason in skipped:
            print(f"  {path}: {reason}")

    print("")
    print("Counts by replacement policy:")
    counts = {}
    for row in rows:
        policy = row["replacement_policy"]
        counts[policy] = counts.get(policy, 0) + 1

    for policy, count in sorted(counts.items()):
        print(f"  {policy}: {count}")


if __name__ == "__main__":
    main()