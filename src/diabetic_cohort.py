
import pandas as pd
import os

# =====================================
# 1. FILE PATHS
# =====================================

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "processed",
    "nhanes_merged.csv"
)

OUTPUT_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "processed",
    "diabetic_cohort.csv"
)

# =====================================
# 2. LOAD MERGED DATASET
# =====================================

df = pd.read_csv(INPUT_FILE)

print("Original dataset loaded!")
print("Total participants:", len(df))

# =====================================
# 3. CHECK REQUIRED COLUMNS
# =====================================

print("\nChecking diabetes-related columns...")

for col in df.columns:

    if any(term in col.upper() for term in
           ["LBXGH", "LBXGLU", "DIQ010"]):

        print(col)

# =====================================
# 4. IDENTIFY RELEVANT VARIABLES
# =====================================

# These names are based on standard NHANES
# variable names in the selected cycle.

hba1c_col = "LBXGH"
glucose_col = "LBXGLU"
diabetes_col = "DIQ010"

# Check whether variables exist

for col in [hba1c_col, glucose_col, diabetes_col]:

    if col not in df.columns:

        print(f"WARNING: {col} is not available.")

# =====================================
# 5. CONVERT VALUES TO NUMERIC
# =====================================

for col in [hba1c_col, glucose_col, diabetes_col]:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

# =====================================
# 6. CREATE INDIVIDUAL INDICATORS
# =====================================

# Laboratory indicators

if hba1c_col in df.columns:

    df["HBA1C_DIABETES_INDICATOR"] = (
        df[hba1c_col] >= 6.5
    ).astype("boolean")

if glucose_col in df.columns:

    df["GLUCOSE_DIABETES_INDICATOR"] = (
        df[glucose_col] >= 126
    ).astype("boolean")

# Self-reported diabetes
# DIQ010: 1 = Yes, 2 = No, 3 = Borderline
# Other values are treated as unknown.

if diabetes_col in df.columns:

    df["SELF_REPORTED_DIABETES"] = (
        df[diabetes_col] == 1
    ).astype("boolean")

# =====================================
# 7. CREATE DIABETES STATUS
# =====================================

# Status:
# 1 = Diabetes
# 0 = No diabetes
# 2 = Indeterminate

indicators = []

for col in [
    "HBA1C_DIABETES_INDICATOR",
    "GLUCOSE_DIABETES_INDICATOR",
    "SELF_REPORTED_DIABETES"
]:

    if col in df.columns:
        indicators.append(df[col])

indicator_df = pd.concat(indicators, axis=1)

# Any positive indicator identifies a
# participant for the research cohort.

has_positive = indicator_df.eq(True).any(axis=1)

# A negative classification requires all
# available indicators to be observed and negative.

has_all_negative = indicator_df.notna().all(axis=1) & indicator_df.eq(False).all(axis=1)

df["diabetes_status"] = 2

df.loc[has_positive, "diabetes_status"] = 1

df.loc[has_all_negative, "diabetes_status"] = 0

# =====================================
# 8. EXTRACT DIABETIC COHORT
# =====================================

diabetic_df = df[
    df["diabetes_status"] == 1
].copy()

# =====================================
# 9. SAVE RESULTS
# =====================================

diabetic_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# =====================================
# 10. DISPLAY SUMMARY
# =====================================

print("\n========== RESULTS ==========")

print("Total participants:", len(df))

print(
    "Diabetic participants:",
    (df["diabetes_status"] == 1).sum()
)

print(
    "Non-diabetic participants:",
    (df["diabetes_status"] == 0).sum()
)

print(
    "Indeterminate participants:",
    (df["diabetes_status"] == 2).sum()
)

print("\nDiabetic cohort saved successfully!")

print(OUTPUT_FILE)
