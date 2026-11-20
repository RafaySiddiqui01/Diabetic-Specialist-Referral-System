
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "diabetic_cohort.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "diabetic_patients_features.csv"
REPORT_FILE = BASE_DIR / "data" / "reports" / "diabetic_feature_missingness.csv"

if not INPUT_FILE.exists():
    raise FileNotFoundError("Run diabetic_cohort.py first.")

df = pd.read_csv(INPUT_FILE)

if "diabetes_status" not in df.columns:
    raise ValueError("diabetes_status column is missing.")

# Keep participants with at least one diabetes indicator
diabetic_df = df[df["diabetes_status"] == 1].copy()

# Clinical features grouped by specialist
specialist_features = {
    "endocrinologist": [
        "LBXGH", "LBXGLU"
    ],
    "nephrologist": [
        "URXUMA", "URXUCR", "URDACT", "LBXSCR", "LBXSBU"
    ],
    "cardiologist": [
        "LBXTC", "LBDHDD", "LBXTLG",
        "BPXOSY1", "BPXODI1", "BMXBMI"
    ],
    "hepatologist": [
        "LBXSATSI", "LBXSASSI", "LBXSAPSI",
        "LBXSAL", "LBXSTB"
    ]
}

# Keep only variables that actually exist
available_features = sorted({
    feature
    for features in specialist_features.values()
    for feature in features
    if feature in diabetic_df.columns
})

selected_columns = ["SEQN", "diabetes_status"] + available_features
selected_columns = list(dict.fromkeys(selected_columns))

processed_df = diabetic_df[selected_columns].copy()

# Create a missingness report without filling missing values
missing_report = pd.DataFrame({
    "feature": available_features,
    "missing_count": [
        processed_df[col].isna().sum()
        for col in available_features
    ],
    "missing_percentage": [
        round(processed_df[col].isna().mean() * 100, 2)
        for col in available_features
    ]
})

# Save outputs
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

processed_df.to_csv(OUTPUT_FILE, index=False)
missing_report.to_csv(REPORT_FILE, index=False)

print("\nCLINICAL PREPROCESSING COMPLETED")
print("--------------------------------")
print("Total participants in merged data:", len(df))
print("Participants with diabetes evidence:", len(diabetic_df))
print("Selected clinical features:", len(available_features))
print("\nMissingness report:")
print(missing_report.to_string(index=False))

print("\nProcessed dataset:", OUTPUT_FILE)
print("Missingness report:", REPORT_FILE)
