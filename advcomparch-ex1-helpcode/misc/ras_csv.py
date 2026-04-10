import csv
import re
import sys
from pathlib import Path

RAS_SIZES = [4, 8, 16, 32, 48, 64]

RAS_RE = re.compile(r"^RAS \((\d+) entries\):\s+(\d+)\s+(\d+)\s*$")


def benchmark_name_from_filename(file_path: Path) -> str:
    name = file_path.name

    known_suffixes = [
        ".cslab_branch_preds_train.out",
        ".cslab_branch_stats_train.out",
        ".out",
    ]

    for suffix in known_suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]

    return file_path.stem


def parse_ras_file(file_path: Path) -> dict:
    results = {}

    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            match = RAS_RE.match(line)
            if match:
                ras_size = int(match.group(1))
                correct = int(match.group(2))
                incorrect = int(match.group(3))
                results[ras_size] = {
                    "correct": correct,
                    "incorrect": incorrect,
                }

    return results


def build_rows(input_dir: Path):
    out_files = sorted(input_dir.glob("*.out"))

    if not out_files:
        raise FileNotFoundError(f"No .out files found in folder: {input_dir}")

    rows = []

    header = ["benchmark"]
    for size in RAS_SIZES:
        header.append(f"RAS-{size} Correct")
        header.append(f"RAS-{size} Incorrect")
    rows.append(header)

    for file_path in out_files:
        bench = benchmark_name_from_filename(file_path)
        parsed = parse_ras_file(file_path)

        row = [bench]
        for size in RAS_SIZES:
            row.append(parsed.get(size, {}).get("correct", ""))
            row.append(parsed.get(size, {}).get("incorrect", ""))
        rows.append(row)

    return rows


def write_csv(rows, output_file: Path):
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 make_ras_csv.py <input_folder> [output_csv]")
        sys.exit(1)

    input_dir = Path(sys.argv[1]).expanduser().resolve()
    output_file = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) == 3
        else input_dir / "ras_results.csv"
    )

    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a folder.")
        sys.exit(1)

    rows = build_rows(input_dir)
    write_csv(rows, output_file)

    print(f"CSV created: {output_file}")


if __name__ == "__main__":
    main()