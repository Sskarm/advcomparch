import os
import re
import csv
import sys

# ΒΑΛΕ ΕΔΩ ΤΑ ΑΚΡΙΒΗ LABELS ΟΠΩΣ ΕΜΦΑΝΙΖΟΝΤΑΙ ΣΤΟ OUTPUT
SELECTED_PREDICTORS = [
    "Nbit-32K-1",
    "2bit-Counter-16K",
    "FSM-2-16K",
    "FSM-3-16K",
    "FSM-4-16K",
    "FSM-5-16K",
    "Nbit-8K-4"
]

def extract_benchmark_name(filename: str) -> str:
    name_no_ext = os.path.splitext(filename)[0]

    suffixes = [
        ".cslab_branch_preds_train",
        ".cslab_branch_preds_ref",
        ".cslab_branch_preds",
    ]

    for suffix in suffixes:
        if name_no_ext.endswith(suffix):
            return name_no_ext[:-len(suffix)]

    return name_no_ext


def extract_total_instructions(content: str) -> int:
    m = re.search(r"^Total Instructions:\s*(\d+)\s*$", content, re.MULTILINE)
    if not m:
        raise ValueError("Missing 'Total Instructions'")
    return int(m.group(1))


def normalize_label(label: str) -> str:
    label = label.strip()
    label = re.sub(r"\s*\([^)]*\)\s*$", "", label).strip()
    return label


def extract_predictor_lines(content: str):
    predictors = {}

    pattern = re.compile(
        r"^(.+?):\s*(\d+)\s+(\d+)\s*$",
        re.MULTILINE
    )

    for m in pattern.finditer(content):
        raw_label = m.group(1).strip()
        correct = int(m.group(2))
        incorrect = int(m.group(3))

        if raw_label == "Total Instructions":
            continue
        if raw_label.endswith("statistics"):
            continue

        normalized = normalize_label(raw_label)
        predictors[normalized] = {
            "raw_label": raw_label,
            "correct": correct,
            "incorrect": incorrect,
        }

    return predictors


def parse_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(file_path)
    benchmark = extract_benchmark_name(filename)
    total_instructions = extract_total_instructions(content)
    predictors = extract_predictor_lines(content)

    row = {
        "Benchmark": benchmark,
        "Total Instructions": total_instructions,
    }

    missing = []

    for predictor in SELECTED_PREDICTORS:
        if predictor not in predictors:
            missing.append(predictor)
            continue

        correct = predictors[predictor]["correct"]
        incorrect = predictors[predictor]["incorrect"]

        row[f"{predictor} Correct"] = correct
        row[f"{predictor} Incorrect"] = incorrect

    if missing:
        available = ", ".join(sorted(predictors.keys()))
        raise ValueError(
            f"Missing predictors: {missing} | Available predictors: [{available}]"
        )

    return row


def build_headers():
    headers = ["Benchmark", "Total Instructions"]
    for predictor in SELECTED_PREDICTORS:
        headers.extend([
            f"{predictor} Correct",
            f"{predictor} Incorrect",
        ])
    return headers


def main(input_folder: str, output_csv: str):
    files = sorted(
        f for f in os.listdir(input_folder)
        if f.endswith(".out")
    )

    if not files:
        print("No .out files found in input folder.")
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

    if not rows:
        print("No rows parsed successfully.")
        sys.exit(1)

    headers = build_headers()

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCreated CSV: {output_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage:")
        print("python parse_53iii.py <input_folder> <output_csv>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_csv = sys.argv[2]
    main(input_folder, output_csv)