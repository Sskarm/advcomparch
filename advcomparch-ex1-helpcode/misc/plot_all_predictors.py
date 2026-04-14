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
    44.89311949,
    21.38254876,
    7.752484646,
    12.31188467,
    4.825208964,
    6.076230662,
    7.791645341,
    15.35040148,
    9.177637157,
    5.616214624,
    3.142458303,
    2.977602624,
    2.893695114,
    3.205967328,
    5.1723116,
    7.734800373,
    2.963913744,
    3.203365717,
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