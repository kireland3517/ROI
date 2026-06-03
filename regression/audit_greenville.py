import pandas as pd
from pathlib import Path

START = "2023-06-01"
END = "2026-05-31"
PATH = Path(__file__).resolve().parents[1] / "comps_output" / "Greenville-Anderson-Greer_SC.csv"


def apply_baseline_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df[df["sale_date"].notna()].copy()
    filtered = filtered[filtered["sale_date"].between(START, END)]
    filtered = filtered[filtered["sale_amount"].fillna(0) > 0]
    filtered = filtered[filtered["sqft"].fillna(0) > 0]
    filtered = filtered[filtered["property_type"] == "SFR"]
    filtered = filtered[filtered["sale_type"] == "Resale"]
    filtered = filtered[filtered["beds"].fillna(0) > 0]
    filtered = filtered[filtered["baths"].fillna(0) > 0]
    return filtered


def main() -> None:
    df = pd.read_csv(PATH)
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    print("=== GREENVILLE MVP DATA CHECK ===")
    print(f"File: {PATH.name}")
    print(f"Total rows: {len(df):,}")
    print()

    populated = df["sale_date"].notna().sum()
    print("1) sale_date populated")
    print(f"   {populated:,}/{len(df):,} ({100 * populated / len(df):.1f}%)")
    print()

    in_window = df["sale_date"].between(START, END)
    print(f"2) sale_date inside pull window ({START} to {END})")
    print(f"   {in_window.sum():,}/{len(df):,} ({100 * in_window.sum() / len(df):.1f}%)")
    if populated:
        print(f"   min date: {df['sale_date'].min().date()}")
        print(f"   max date: {df['sale_date'].max().date()}")
        out_before = (df["sale_date"] < START).sum()
        out_after = (df["sale_date"] > END).sum()
        print(f"   outside window: {out_before:,} before start, {out_after:,} after end")
    print()

    print("3) Baseline regression filters (stepwise)")
    steps = [
        ("sale_date present", df["sale_date"].notna()),
        ("in pull window", df["sale_date"].between(START, END)),
        ("sale_amount > 0", df["sale_amount"].fillna(0) > 0),
        ("sqft > 0", df["sqft"].fillna(0) > 0),
        ("property_type == SFR", df["property_type"] == "SFR"),
        ("sale_type == Resale", df["sale_type"] == "Resale"),
        ("beds > 0", df["beds"].fillna(0) > 0),
        ("baths > 0", df["baths"].fillna(0) > 0),
    ]

    mask = pd.Series(True, index=df.index)
    for name, step_mask in steps:
        mask &= step_mask
        print(f"   after {name}: {mask.sum():,}")

    usable = df[mask]
    print()
    print(
        f"USABLE ROWS AFTER BASELINE FILTERS: {len(usable):,} "
        f"({100 * len(usable) / len(df):.1f}% of raw pull)"
    )
    print()
    print("Property types in raw pull:")
    print(df["property_type"].value_counts().head(8).to_string())
    print()
    print("Sale types in raw pull:")
    print(df["sale_type"].value_counts(dropna=False).head(8).to_string())


if __name__ == "__main__":
    main()
