import sys
import matplotlib.pyplot as plt

predictors = [
    "Static-AlwaysTaken",
    "Static-BTFNT",
    "Best-2bit-FSM",
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

average_mpki = [
    50.73455338,
    20.8400853,
    7.757421094,
    9.73548857,
    4.289065942,
    5.417550184,
    7.129470406,
    13.59765554,
    7.164777743,
    4.463729691,
    2.728237079,
    2.599158712,
    2.647441028,
    2.769152572,
    4.400166435,
    7.696038496,
    2.639058323,
    2.800491108

]

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 plot_final_predictors_avg_mpki.py <output_file>")
        sys.exit(1)

    output_file = sys.argv[1]

    plt.figure(figsize=(16, 7))
    plt.bar(predictors, average_mpki)

    plt.xlabel("Predictors")
    plt.ylabel("Average MPKI")
    plt.title("Average MPKI per Predictor")
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()

    plt.savefig(output_file, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()