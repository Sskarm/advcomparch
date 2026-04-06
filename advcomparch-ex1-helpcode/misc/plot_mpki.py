import sys
import pandas as pd
import matplotlib.pyplot as plt


def main(input_csv, output_png="mpki_plot.png"):
    df = pd.read_csv(input_csv)

    if "Total Instructions" not in df.columns:
        raise ValueError("Missing column: 'Total Instructions'")

    # Βρίσκει predictors από στήλες τύπου "XYZ Incorrect"
    incorrect_cols = [c for c in df.columns if c.endswith(" Incorrect")]

    if not incorrect_cols:
        raise ValueError("No predictor 'Incorrect' columns found.")

    predictor_mpki_means = {}

    for inc_col in incorrect_cols:
        predictor = inc_col[:-len(" Incorrect")]
        mpki_col = f"{predictor} MPKI"

        if mpki_col in df.columns:
            df[mpki_col] = pd.to_numeric(df[mpki_col], errors="coerce")
        else:
            df[inc_col] = pd.to_numeric(df[inc_col], errors="coerce")
            df["Total Instructions"] = pd.to_numeric(df["Total Instructions"], errors="coerce")
            df[mpki_col] = (df[inc_col] / df["Total Instructions"]) * 1000

        predictor_mpki_means[predictor] = df[mpki_col].mean()

    plot_df = pd.DataFrame({
        "Predictor": list(predictor_mpki_means.keys()),
        "Average MPKI": list(predictor_mpki_means.values())
    }).sort_values("Average MPKI")

    plt.figure(figsize=(10, 6))
    plt.bar(plot_df["Predictor"], plot_df["Average MPKI"])
    plt.xlabel("Predictor")
    plt.ylabel("Average MPKI")
    plt.title("Average MPKI per Predictor")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_png, dpi=200)
    plt.show()

    print(f"Saved plot to: {output_png}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("python plot_mpki.py <input_csv> [output_png]")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_png = sys.argv[2] if len(sys.argv) > 2 else "mpki_plot.png"
    main(input_csv, output_png)