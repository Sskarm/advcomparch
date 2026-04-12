import csv
import re
import sys
from pathlib import Path

TOTAL_INSTR_RE = re.compile(r"^\s*Total Instructions:\s+(\d+)\s*$")
SECTION_HEADER = "Branch Predictors: (Name - Correct - Incorrect)"
SECTION_END = "BTB Predictors:"

# Matches lines like:
#   Perceptron Branch Predictor (perceptrons: 32, history size: 4: 493313818 81152397
PREDICTOR_RE = re.compile(
    r"^\s*Perceptron Branch Predictor \(perceptrons:\s*(\d+),\s*history size:\s*(\d+):\s*(\d+)\s+(\d+)\s*$"
)

PERCEPTRON_ORDER = [
    (32, 4), (32, 8), (32, 32), (32, 60), (32, 72),
    (512, 4), (512, 8), (512, 32), (512, 60), (512, 72),
    (1024, 4), (1024, 8), (1024, 32), (1024, 60), (1024, 72),
]


def benchmark_name_from_filename(file_path: Path) -> str:
    suffix = ".cslab_branch_preds_train.out"
    name = file_path.name
    if name.endswith(suffix):
        return name[:-len(suffix)]
    return file_path.stem


def parse_file(file_path: Path) -> dict:
    result = {
        "total_instructions": ""
    }

    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        in_branch_section = False

        for raw_line in f:
            line = raw_line.strip()

            total_match = TOTAL_INSTR_RE.match(line)
            if total_match:
                result["total_instructions"] = int(total_match.group(1))
                continue

            if line == SECTION_HEADER:
                in_branch_section = True
                continue

            if in_branch_section and line.startswith(SECTION_END):
                break

            if not in_branch_section or not line:
                continue

            m = PREDICTOR_RE.match(raw_line)
            if not m:
                continue

            perceptrons = int(m.group(1))
            history = int(m.group(2))
            correct = int(m.group(3))
            incorrect = int(m.group(4))

            result[(perceptrons, history)] = {
                "correct": correct,
                "incorrect": incorrect,
            }

    return result


def build_rows(input_dir: Path):
    files = sorted(input_dir.glob("*.cslab_branch_preds_train.out"))
    if not files:
        raise FileNotFoundError(
            f"No files ending in '.cslab_branch_preds_train.out' found in {input_dir}"
        )

    header = ["Benchmark"]
    for m, h in PERCEPTRON_ORDER:
        header.append(f"M{m}-H{h} Correct")
        header.append(f"M{m}-H{h} Incorrect")
    header.append("Total Instructions")

    rows = [header]

    for file_path in files:
        bench = benchmark_name_from_filename(file_path)
        parsed = parse_file(file_path)

        row = [bench]
        for key in PERCEPTRON_ORDER:
            row.append(parsed.get(key, {}).get("correct", ""))
            row.append(parsed.get(key, {}).get("incorrect", ""))
        row.append(parsed.get("total_instructions", ""))

        rows.append(row)

    return rows


def write_csv(rows, output_file: Path):
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 make_perceptron_csv.py <input_folder> [output_csv]")
        sys.exit(1)

    input_dir = Path(sys.argv[1]).expanduser().resolve()
    output_file = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) == 3
        else input_dir / "perceptron_results.csv"
    )

    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a folder.")
        sys.exit(1)

    rows = build_rows(input_dir)
    write_csv(rows, output_file)

    print(f"CSV created: {output_file}")


if __name__ == "__main__":
    main()