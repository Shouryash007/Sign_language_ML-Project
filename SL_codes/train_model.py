# train_model.py

import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils import resample

# CONFIGURATION 
DATA_DIR        = "data"
MODEL_DIR       = "models"
PIPELINE_PATH   = os.path.join(MODEL_DIR, "gesture_pipeline.pkl")

FEATURE_NAMES = [
    "flex1", "flex2", "flex3", "flex4", "flex5",
    "accelX", "accelY", "accelZ",
    "gyroX",  "gyroY",  "gyroZ"
]

# LOAD & CLEAN THE DATA
def load_gesture_data(data_dir: str) -> pd.DataFrame:
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    dfs = []
    for fname in csv_files:
        path = os.path.join(data_dir, fname)
        df = pd.read_csv(path)

        # Drop timestamp if present
        if "timestamp" in df.columns:
            df = df.drop(columns=["timestamp"])

        # Ensure columns match expected
        expected_cols = FEATURE_NAMES + ["label"]
        if list(df.columns) != expected_cols:
            df.columns = expected_cols

        dfs.append(df)

    if not dfs:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    return pd.concat(dfs, ignore_index=True)

print("\n Loading gesture data…")
full_df = load_gesture_data(DATA_DIR)
print("Label distribution before balancing:")
print(full_df["label"].value_counts())

# BALANCE THE DATASET 
min_count = full_df["label"].value_counts().min()
balanced_parts = []
for lab in full_df["label"].unique():
    subset = full_df[full_df["label"] == lab]
    down = resample(
        subset,
        replace=False,
        n_samples=min_count,
        random_state=42
    )
    balanced_parts.append(down)

balanced_df = pd.concat(balanced_parts, ignore_index=True)
print("\n Label distribution after balancing:")
print(balanced_df["label"].value_counts())

# TRAIN/TEST SPLIT 
X = balanced_df[FEATURE_NAMES]
y = balanced_df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    stratify=y,
    random_state=42
)

# BUILD PIPELINE 
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestClassifier(n_estimators=100, random_state=42))
])

# CROSS‐VALIDATION 
print("\n Performing 5‐fold CV on training set…")
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5)
print(f"CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# FINAL TRAINING 
print("\n Training final model on full training set…")
pipeline.fit(X_train, y_train)

# EVALUATE ON HELD‐OUT TEST 
y_pred = pipeline.predict(X_test)
print("\n Test set classification report:\n")
print(classification_report(y_test, y_pred))

# confusion matrix
cm = confusion_matrix(y_test, y_pred, labels=y.unique())
print(" Confusion Matrix:")
print(pd.DataFrame(cm, index=y.unique(), columns=y.unique()))

# SAVE PIPELINE 
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(pipeline, PIPELINE_PATH)
print(f"\n Saved gesture pipeline to '{PIPELINE_PATH}'\n")