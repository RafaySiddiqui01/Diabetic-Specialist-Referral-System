
from pathlib import Path
import pandas as pd

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "nhanes_merged.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "diabetic_cohort.csv"
REPORT_FILE = BASE_DIR / "data" / "reports" / "diabetes_cohort_summary.csv"

# Create output folders if needed
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Loading merged NHANES dataset...")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Merged dataset not found: {INPUT_FILE}. Run Step 2 first."
    )

df = pd.read_csv(INPUT_FILE)

# Required variables
required_columns = ["SEQN", "LBXGH", "LBXGLU", "DIQ010"]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}. "
        "Check the merged dataset column names."
    )

# Convert values to numeric
for col in ["LBXGH", "LBXGLU", "DIQ010"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Evidence indicators
df["hba1c_diabetes_indicator"] = df["LBXGH"].ge(6.5).astype("int64")
df["glucose_diabetes_indicator"] = df["LBXGLU"].ge(126).astype("int64")
df["self_reported_diabetes"] = df["DIQ010"].eq(1).astype("int64")

# Count positive indicators
indicator_columns = [
    "hba1c_diabetes_indicator",
    "glucose_diabetes_indicator",
    "self_reported_diabetes"
]

df["diabetes_evidence_count"] = df[indicator_columns].sum(axis=1)

# Count how many indicators are actually available
available_columns = [
    "LBXGH",
    "LBXGLU",
    "DIQ010"
]

df["available_indicator_count"] = df[available_columns].notna().sum(axis=1)

# Classification:
# 1 = At least one positive indicator
# 0 = All three indicators available and all negative
# 2 = Insufficient information to classify
df["diabetes_status"] = 2

df.loc[
    df["diabetes_evidence_count"] > 0,
    "diabetes_status"
] = 1

df.loc[
    (df["diabetes_evidence_count"] == 0) &
    (df["available_indicator_count"] == 3),
    "diabetes_status"
] = 0

# Readable labels
df["diabetes_status_label"] = df["diabetes_status"].map({
    0: "No diabetes indicators",
    1: "Diabetes evidence present",
    2: "Indeterminate"
})

# Save cohort dataset
df.to_csv(OUTPUT_FILE, index=False)

# Generate summary
summary = (
    df["diabetes_status_label"]
    .value_counts()
    .rename_axis("diabetes_status")
    .reset_index(name="participant_count")
)

summary.to_csv(REPORT_FILE, index=False)

print("\nSTEP 3 COMPLETED")
print("------------------------------")
print(f"Total participants: {len(df)}")
print("\nDiabetes classification:")
print(summary.to_string(index=False))

print(f"\nCohort saved to: {OUTPUT_FILE}")
print(f"Summary saved to: {REPORT_FILE}")
