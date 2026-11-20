
from pathlib import Path
import pandas as pd

# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "data" / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_DIR / "nhanes_merged.csv"

# The demographics dataset will be our master dataset.
MASTER_FILE = "demographics.xpt"

# Medication data contains multiple rows per participant.
# We will handle it separately rather than directly merging it.
EXCLUDED_FILES = {"prescription_medications.xpt"}


def load_xpt(filepath):
    """Load an NHANES XPT file."""
    df = pd.read_sas(
        filepath,
        format="xport",
        encoding="utf-8"
    )

    df.columns = df.columns.str.upper()

    if "SEQN" not in df.columns:
        raise ValueError(f"SEQN column missing in {filepath.name}")

    return df


def main():
    print("Starting NHANES dataset merging...\n")

    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw data folder not found: {RAW_DIR}")

    master_path = RAW_DIR / MASTER_FILE

    if not master_path.exists():
        raise FileNotFoundError(
            f"Master file not found: {master_path}\n"
            "Check that demographics.xpt is inside data/raw."
        )

    # Load the master demographics dataset
    merged_df = load_xpt(master_path)

    if merged_df["SEQN"].duplicated().any():
        raise ValueError("Duplicate SEQN values found in demographics.xpt.")

    print(f"Loaded demographics: {len(merged_df)} participants")

    summary = [{
        "dataset": MASTER_FILE,
        "rows": len(merged_df),
        "columns": len(merged_df.columns),
        "merge_status": "Master dataset"
    }]

    # Load and merge the remaining XPT files
    xpt_files = sorted(RAW_DIR.glob("*.xpt"))

    for filepath in xpt_files:

        if filepath.name.lower() == MASTER_FILE.lower():
            continue

        if filepath.name.lower() in EXCLUDED_FILES:
            print(f"Skipping {filepath.name} (one-to-many medication records)")
            summary.append({
                "dataset": filepath.name,
                "rows": "Not loaded",
                "columns": "Not loaded",
                "merge_status": "Skipped - requires separate processing"
            })
            continue

        print(f"\nProcessing: {filepath.name}")

        dataset = load_xpt(filepath)

        if dataset["SEQN"].duplicated().any():
            duplicate_count = dataset["SEQN"].duplicated().sum()
            raise ValueError(
                f"{filepath.name} contains {duplicate_count} duplicate SEQN "
                "records. Do not merge it until its duplicate structure is handled."
            )

        original_rows = len(dataset)

        # Avoid overwriting columns with the same names.
        # Keep the existing column name and suffix duplicate names.
        dataset_name = filepath.stem.upper()

        merged_df = merged_df.merge(
            dataset,
            on="SEQN",
            how="left",
            suffixes=("", f"_{dataset_name}"),
            validate="one_to_one"
        )

        print(f"Rows in dataset: {original_rows}")
        print(f"Total merged columns: {len(merged_df.columns)}")

        summary.append({
            "dataset": filepath.name,
            "rows": original_rows,
            "columns": len(dataset.columns),
            "merge_status": "Merged successfully"
        })

    # Save the merged dataset
    merged_df.to_csv(OUTPUT_FILE, index=False)

    # Save a merge report
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(
        REPORTS_DIR / "merge_summary.csv",
        index=False
    )

    print("\n--------------------------------")
    print("DATASET MERGING COMPLETED")
    print("--------------------------------")
    print(f"Participants: {len(merged_df)}")
    print(f"Total columns: {len(merged_df.columns)}")
    print(f"Saved merged file: {OUTPUT_FILE}")
    print(f"Saved report: {REPORTS_DIR / 'merge_summary.csv'}")

    print("\nImportant columns available:")
    for column in merged_df.columns:
        if column in ["LBXGH", "LBXGLU", "DIQ010"]:
            print(f"- {column}")

    print("\nCheck the reports folder and merged CSV before proceeding.")


if __name__ == "__main__":
    main()
