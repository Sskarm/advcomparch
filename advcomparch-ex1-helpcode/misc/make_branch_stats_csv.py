import os
import re
import csv
import sys

PATTERNS = {
    "Total Branches": r"Total-Branches:\s*(\d+)",
    "Conditional Taken": r"Conditional-Taken-Branches:\s*(\d+)",
    "Conditional Non-Taken": r"Conditional-NotTaken-Branches:\s*(\d+)",
    "Unconditional Branches": r"Unconditional-Branches:\s*(\d+)",
    "Calls": r"Calls:\s*(\d+)",
    "Returns": r"Returns:\s*(\d+)",
}

CSV_HEADERS = [
    "Benchmark",
    "Total Branches",
    "Conditional Taken",
    "Conditional Non-Taken",
    "Unconditional Branches",
    "Calls",
    "Returns",
]


def extract_stats(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    row = {}
    for column, pattern in PATTERNS.items():
        match = re.search(pattern, content)
        if not match:
            raise ValueError(f"Δεν βρέθηκε το πεδίο '{column}' στο αρχείο: {file_path}")
        row[column] = int(match.group(1))

    # Benchmark name = filename χωρίς extension
    filename = os.path.basename(file_path)
    benchmark_name = os.path.splitext(filename)[0]
    row["Benchmark"] = benchmark_name

    return row


def main(input_folder, output_csv):
    files = sorted(
        [
            os.path.join(input_folder, f)
            for f in os.listdir(input_folder)
            if os.path.isfile(os.path.join(input_folder, f))
        ]
    )

    if not files:
        print("Δεν βρέθηκαν αρχεία στον φάκελο.")
        return

    rows = []
    for file_path in files:
        try:
            row = extract_stats(file_path)
            rows.append(row)
            print(f"OK: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"SKIP: {os.path.basename(file_path)} -> {e}")

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nΤο CSV δημιουργήθηκε: {output_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Χρήση:")
        print("python make_branch_stats_csv.py <input_folder> <output_csv>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_csv = sys.argv[2]
    main(input_folder, output_csv)