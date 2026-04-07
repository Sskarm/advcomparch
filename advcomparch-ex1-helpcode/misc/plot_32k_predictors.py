import sys
import matplotlib.pyplot as plt

predictors = [
    "1-bit",
    "FSM 1",
    "FSM 2",
    "FSM 3",
    "FSM 4",
    "FSM 5",
    "4-bit"
]

average_mpki = [
    12.22795,
    7.768728753,
    10.07954,
    7.9395837,
    7.9018725,
    10.140103,
    7.781311
]

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 plot_avg_mpki.py <output_file>")
        sys.exit(1)

    output_file = sys.argv[1]

    plt.figure(figsize=(10, 6))
    plt.bar(predictors, average_mpki)

    plt.xlabel("Predictors")
    plt.ylabel("Average MPKI")
    plt.title("Average MPKI per Predictor")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(output_file, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()