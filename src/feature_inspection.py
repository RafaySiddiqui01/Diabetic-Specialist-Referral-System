
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "nhanes_merged.csv"
REPORT_DIR = BASE_DIR / "data" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

# Correct NHANES 2021-2023 variable names
clinical_variables = {
    "HbA1c": "LBXGH",
    "Fasting Glucose": "LBXGLU",
    "Urine Albumin": "URXUMA",
    "Urine Creatinine": "URXUCR",
    "Urine Albumin Creatinine Ratio": "URDACT",
    "Total Cholesterol": "LBXTC",
    "HDL Cholesterol": "LBDHDD",
    "Triglycerides": "LBXTLG",
    "BMI": "BMXBMI",
    "Systolic Blood Pressure": "BPXOSY1",
    "Diastolic Blood Pressure": "BPXODI1",
    "Serum Creatinine": "LBXSCR",
    "ALT": "LBXSATSI",
    "AST": "LBXSASSI",
    "ALP": "LBXSAPSI",
    "Serum Albumin": "LBXSAL",
    "Total Bilirubin": "LBXSTB",
    "Blood Urea Nitrogen": "LBXSBU"
}

results = []

for feature, variable in clinical_variables.items():
    available = variable in df.columns

    results.append({
        "clinical_feature": feature,
        "nhanes_variable": variable,
        "available": available,
        "missing_count": (
            df[variable].isna().sum() if available else None
        ),
        "missing_percentage": (
            round(df[variable].isna().mean() * 100, 2)
            if available else None
        )
    })

report = pd.DataFrame(results)

report.to_csv(
    REPORT_DIR / "clinical_feature_availability.csv",
    index=False
)

print("\nCLINICAL FEATURE INSPECTION")
print("---------------------------")
print(report.to_string(index=False))

print("\nAvailable:", report["available"].sum())
print("Unavailable:", (~report["available"]).sum())

print("\nReport saved to:", REPORT_DIR)
