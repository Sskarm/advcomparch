import csv
import re
import sys
from pathlib import Path

TOTAL_INSTR_RE = re.compile(r"^\s*Total Instructions:\s+(\d+)\s*$")
SECTION_HEADER = "Branch Predictors: (Name - Correct - Incorrect)"
SECTION_END = "BTB Predictors:"

# General predictor line:
#   Alpha21264: 28069975500 1469470326
GENERAL_PRED_RE = re.compile(r"^\s*(.+?):\s+(\d+)\s+(\d+)\s*$")

# Perceptron line in your current output:
#   Perceptron Branch Predictor (perceptrons: 256, history size: 20: 27656677952 1882767874
PERCEPTRON_RE = re.compile(
    r"^\s*Perceptron Branch Predictor \(perceptrons:\s*(\d+),\s*history size:\s*(\d+):\s*(\d+)\s+(\d+)\s*$"
)

PREDICTOR_ORDER = [
    "Static-AlwaysTaken",
    "Static-BTFNT",
    "Best-2bit-FSM (ABACBDCD:3)",
    "Pentium-M",
    "LocalHistory-BHT2048-H8",
    "LocalHistory-BHT4096-H4",
    "LocalHistory-BHT8192-H2",
    "GlobalHistory-H4-PHT16384",
    "GlobalHistory-H8-PHT16384",
    "GlobalHistory-H12-PHT16384",
    "Perceptron-M256-H20",
    "Perceptron-M128-H32",
    "Perceptron-M64-H60",
    "Alpha21264",
    "Tournament-2bit-vs-Global",
    "Tournament-2bit-vs-FSM",
    "Tournament-2bit-vs-Perceptron",
    "Tournament-Global-vs-Perceptron",
]


def benchmark_name_from_filename(file_path: Path) -> str:
    suffix = ".cslab_branch_preds_train.out"
    name = file_path.name
    if name.endswith(suffix):
        return name[:-len(suffix)]
    return file_path.stem


def normalize_predictor_name(raw_line: str, general_name: str = None, m: int = None, h: int = None) -> str:
    if m is not None and h is not None:
        return f"Perceptron-M{m}-H{h}"
    return general_name.strip()


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

            pm = PERCEPTRON_RE.match(raw_line)
            if pm:
                m = int(pm.group(1))
                h = int(pm.group(2))
                correct = int(pm.group(3))
                incorrect = int(pm.group(4))
                name = normalize_predictor_name(raw_line, m=m, h=h)
                result[name] = {
                    "correct": correct,
                    "incorrect": incorrect,
                }
                continue

            gm = GENERAL_PRED_RE.match(raw_line)
            if gm:
                name = normalize_predictor_name(raw_line, general_name=gm.group(1))
                correct = int(gm.group(2))
                incorrect = int(gm.group(3))
                result[name] = {
                    "correct": correct,
                    "incorrect": incorrect,
                }

    return result


def build_big_rows(parsed_files):
    header = ["Benchmark"]
    for pred in PREDICTOR_ORDER:
        header.append(f"{pred} Correct")
        header.append(f"{pred} Incorrect")
    header.append("Total Instructions")

    rows = [header]

    for bench, parsed in parsed_files:
        row = [bench]
        for pred in PREDICTOR_ORDER:
            row.append(parsed.get(pred, {}).get("correct", ""))
            row.append(parsed.get(pred, {}).get("incorrect", ""))
        row.append(parsed.get("total_instructions", ""))
        rows.append(row)

    return rows


def build_mpki_rows(parsed_files):
    header = ["Benchmark"]
    for pred in PREDICTOR_ORDER:
        header.append(f"{pred} MPKI")

    rows = [header]

    for bench, parsed in parsed_files:
        total_instructions = parsed.get("total_instructions", "")
        row = [bench]

        for pred in PREDICTOR_ORDER:
            incorrect = parsed.get(pred, {}).get("incorrect", "")
            if total_instructions and incorrect != "":
                mpki = (incorrect / total_instructions) * 1000
                row.append(mpki)
            else:
                row.append("")
        rows.append(row)

    return rows


def write_combined_csv(big_rows, mpki_rows, output_file: Path):
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # First big table
        writer.writerows(big_rows)

        # Two empty lines
        writer.writerow([])
        writer.writerow([])

        # Second MPKI table
        writer.writerows(mpki_rows)


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 make_final_predictor_csv.py <input_folder> [output_csv]")
        sys.exit(1)

    input_dir = Path(sys.argv[1]).expanduser().resolve()
    output_file = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) == 3
        else input_dir / "final_predictor_results.csv"
    )

    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a folder.")
        sys.exit(1)

    files = sorted(input_dir.glob("*.cslab_branch_preds_train.out"))
    if not files:
        raise FileNotFoundError(
            f"No files ending in '.cslab_branch_preds_train.out' found in {input_dir}"
        )

    parsed_files = []
    for file_path in files:
        bench = benchmark_name_from_filename(file_path)
        parsed = parse_file(file_path)
        parsed_files.append((bench, parsed))

    big_rows = build_big_rows(parsed_files)
    mpki_rows = build_mpki_rows(parsed_files)

    write_combined_csv(big_rows, mpki_rows, output_file)

    print(f"CSV created: {output_file}")


if __name__ == "__main__":
    main()