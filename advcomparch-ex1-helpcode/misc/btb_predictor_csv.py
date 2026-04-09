import os
import re
import csv
import sys

BTB_ORDER = [
    "BTB-512-1",
    "BTB-512-2",
    "BTB-256-2",
    "BTB-256-4",
    "BTB-128-2",
    "BTB-128-4",
    "BTB-64-4",
    "BTB-64-8",
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
    match = re.search(r"^Total Instructions:\s*(\d+)\s*$", content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find 'Total Instructions'")
    return int(match.group(1))


def extract_btb_data(content: str):
    lines = content.splitlines()
    inside_btb_section = False
    btb_data = {}

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("BTB Predictors:"):
            inside_btb_section = True
            continue

        if not inside_btb_section:
            continue

        if stripped == "":
            continue

        match = re.match(r"^(BTB-\d+-\d+):\s+(\d+)\s+(\d+)\s+(\d+)\s*$", stripped)
        if match:
            btb_name = match.group(1)
            correct = int(match.group(2))
            incorrect = int(match.group(3))
            target_correct = int(match.group(4))

            btb_data[btb_name] = {
                "Correct": correct,
                "Incorrect": incorrect,
                "TargetCorrect": target_correct,
            }
        else:
            if inside_btb_section and not stripped.startswith("BTB-"):
                break

    return btb_data


def parse_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(file_path)
    benchmark = extract_benchmark_name(filename)
    total_instructions = extract_total_instructions(content)
    btb_data = extract_btb_data(content)

    if not btb_data:
        raise ValueError("No BTB predictor data found")

    row = {"benchmark": benchmark}

    for btb in BTB_ORDER:
        if btb in btb_data:
            row[f"{btb} Correct"] = btb_data[btb]["Correct"]
            row[f"{btb} Incorrect"] = btb_data[btb]["Incorrect"]
            row[f"{btb} TargetCorrect"] = btb_data[btb]["TargetCorrect"]
        else:
            row[f"{btb} Correct"] = ""
            row[f"{btb} Incorrect"] = ""
            row[f"{btb} TargetCorrect"] = ""

    row["Total Instructions"] = total_instructions
    return row


def build_headers():
    headers = ["benchmark"]
    for btb in BTB_ORDER:
        headers.extend([
            f"{btb} Correct",
            f"{btb} Incorrect",
            f"{btb} TargetCorrect",
        ])
    headers.append("Total Instructions")
    return headers


def benchmark_sort_key(name: str):
    m = re.match(r"^(\d+)\.", name)
    if m:
        return (0, int(m.group(1)), name)
    return (1, name)


def main(input_folder: str, output_csv: str):
    files = sorted(
        [f for f in os.listdir(input_folder) if f.endswith(".out")]
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
        print("No benchmark rows parsed successfully.")
        sys.exit(1)

    rows.sort(key=lambda r: benchmark_sort_key(r["benchmark"]))
    headers = build_headers()

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCreated CSV: {output_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage:")
        print("python parse_btb_wide.py <input_folder> <output_csv>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_csv = sys.argv[2]
    main(input_folder, output_csv)