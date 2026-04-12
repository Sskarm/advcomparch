import sys
import matplotlib.pyplot as plt

perceptrons = [
    "M32-H4", "M32-H8", "M32-H32", "M32-H60", "M32-H72",
    "M512-H4", "M512-H8", "M512-H32", "M512-H60", "M512-H72",
    "M1024-H4", "M1024-H8", "M1024-H32", "M1024-H60", "M1024-H72"
]

average_mpki = [
    8.126336515,
    6.376531308,
    4.108917308,
    3.652626303,
    3.499823013,
    5.267207517,
    4.113567159,
    2.684376053,
    2.261039717,
    2.192813353,
    5.128276943,
    4.039539631,
    2.639715883,
    2.214692662,
    2.144729651
]

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 plot_perceptron_avg_mpki.py <output_file>")
        sys.exit(1)

    output_file = sys.argv[1]

    plt.figure(figsize=(14, 6))
    plt.bar(perceptrons, average_mpki)

    plt.xlabel("Perceptron Predictors")
    plt.ylabel("Average MPKI")
    plt.title("Average MPKI per Perceptron Predictor")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    plt.savefig(output_file, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()