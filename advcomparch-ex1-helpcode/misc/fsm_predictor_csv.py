import os
import re
import csv
import sys

PREDICTORS = [
    "FSM-1",
    "FSM-2",
    "FSM-3",
    "FSM-4",
    "FSM-5",
]

CSV_HEADERS = [
    "Benchmark",
    "Total Instructions",
    "FSM-1 Correct", "FSM-1 Incorrect",
    "FSM-2 Correct", "FSM-2 Incorrect",
    "FSM-3 Correct", "FSM-3 Incorrect",
    "FSM-4 Correct", "FSM-4 Incorrect",
    "FSM-5 Correct", "FSM-5 Incorrect",
]


def extract_benchmark_name(filename: str) -> str:
    name_no_ext = os.path.splitext(filename)[0]
    return name_no_ext.split(".cslab_branch_preds_train")[0]


def extract_total_instructions(content: str) -> int:
    m = re.search(r"Total Instructions:\s*(\d+)", content)
    if not m:
        raise ValueError("Missing 'Total Instructions'")
    return int(m.group(1))


def extract_predictor_stats(content: str, predictor_name: str):
    pattern = rf"{re.escape(predictor_name)}\s*\([^)]+\):\s*(\d+)\s+(\d+)"
    m = re.search(pattern, content)
    if not m:
        raise ValueError(f"Missing predictor stats for {predictor_name}")
    return int(m.group(1)), int(m.group(2))  # correct, incorrect


def parse_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(file_path)
    benchmark = extract_benchmark_name(filename)
    total_instructions = extract_total_instructions(content)

    row = {
        "Benchmark": benchmark,
        "Total Instructions": total_instructions,
    }

    for predictor in PREDICTORS:
        correct, incorrect = extract_predictor_stats(content, predictor)
        row[f"{predictor} Correct"] = correct
        row[f"{predictor} Incorrect"] = incorrect

    return row


def main(input_folder: str, output_csv: str):
    files = sorted(
        f for f in os.listdir(input_folder)
        if f.endswith(".out")
    )

    if not files:
        print("No .out files found.")
        sys.exit(1)

    rows = []
    for filename in files:
        path = os.path.join(input_folder, filename)
        try:
            row = parse_file(path)
            rows.append(row)
            print(f"OK: {filename}")
        except Exception as e:
            print(f"SKIP: {filename} -> {e}")

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCreated CSV: {output_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage:")
        print("python parse_fsm_predictors.py <input_folder> <output_csv>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])