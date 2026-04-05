import csv
import re
import sys
from pathlib import Path

PREDICTORS = [
    "Nbit-16K-1",
    "Nbit-16K-2",
    "Nbit-16K-3",
    "Nbit-16K-4",
]

PREDICTOR_LINE_RE = re.compile(r"^\s*(.+?):\s+(\d+)\s+(\d+)\s*$")


def parse_predictor_file(file_path: Path) -> dict:
    results = {}

    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        in_branch_predictor_section = False

        for raw_line in f:
            line = raw_line.strip()

            if line == "Branch Predictors: (Name - Correct - Incorrect)":
                in_branch_predictor_section = True
                continue

            if in_branch_predictor_section and line.startswith("BTB Predictors:"):
                break

            if not in_branch_predictor_section or not line:
                continue

            match = PREDICTOR_LINE_RE.match(raw_line)
            if not match:
                continue

            predictor_name = match.group(1).strip()
            correct = int(match.group(2))
            incorrect = int(match.group(3))

            if predictor_name in PREDICTORS:
                results[predictor_name] = {
                    "correct": correct,
                    "incorrect": incorrect,
                }

    return results


def benchmark_name_from_filename(file_path: Path) -> str:
    suffix = ".cslab_branch_preds_train.out"
    name = file_path.name
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return file_path.stem


def build_rows(input_dir: Path):
    out_files = sorted(input_dir.glob("*.cslab_branch_preds_train.out"))

    if not out_files:
        raise FileNotFoundError(
            f"No files ending in '.cslab_branch_preds_train.out' were found in: {input_dir}"
        )

    rows = []
    header = [
        "Benchmark",
        "1-bit Correct",
        "1-bit Incorrect",
        "2-bit Correct",
        "2-bit Incorrect",
        "3-bit Correct",
        "3-bit Incorrect",
        "4-bit Correct",
        "4-bit Incorrect",
    ]
    rows.append(header)

    for file_path in out_files:
        bench = benchmark_name_from_filename(file_path)
        parsed = parse_predictor_file(file_path)

        row = [
            bench,
            parsed.get("Nbit-16K-1", {}).get("correct", ""),
            parsed.get("Nbit-16K-1", {}).get("incorrect", ""),
            parsed.get("Nbit-16K-2", {}).get("correct", ""),
            parsed.get("Nbit-16K-2", {}).get("incorrect", ""),
            parsed.get("Nbit-16K-3", {}).get("correct", ""),
            parsed.get("Nbit-16K-3", {}).get("incorrect", ""),
            parsed.get("Nbit-16K-4", {}).get("correct", ""),
            parsed.get("Nbit-16K-4", {}).get("incorrect", ""),
        ]
        rows.append(row)

    return rows


def write_csv(rows, output_file: Path):
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 make_predictor_csv.py <input_folder> [output_csv]")
        sys.exit(1)

    input_dir = Path(sys.argv[1]).expanduser().resolve()
    output_file = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) == 3
        else input_dir / "predictors_summary.csv"
    )

    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a folder.")
        sys.exit(1)

    rows = build_rows(input_dir)
    write_csv(rows, output_file)

    print(f"CSV created: {output_file}")


if __name__ == "__main__":
    main()