import sys
import matplotlib.pyplot as plt

ras_sizes = [4, 8, 16, 32, 48, 64]

# ΒΑΛΕ ΕΔΩ τις average miss rate τιμές σου σε %
miss_rates = [
    2.84,
    0.60,
    0.11,
    0.07,
    0.06,
    0.06
]

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 plot_ras_miss_rate.py <output_file>")
        sys.exit(1)

    output_file = sys.argv[1]

    plt.figure(figsize=(8, 5))
    plt.plot(ras_sizes, miss_rates, marker='o')
    plt.xlabel("RAS entries")
    plt.ylabel("Miss Rate (%)")
    plt.title("RAS Miss Rate vs RAS Size")
    plt.xticks(ras_sizes)
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(output_file, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()