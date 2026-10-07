import json
import joblib

model = joblib.load("artifacts/model.pkl")
scaler = joblib.load("artifacts/scaler.pkl")
encoders = joblib.load("artifacts/encoders.pkl")

with open("artifacts/feature_columns.json", "r") as f:
    cols = json.load(f)

print("model:", type(model))
print("scaler:", type(scaler))
print("n features:", len(cols), cols)

print("encoder keys:", list(encoders.keys()))

if "Contract" in encoders:
    print("Contract classes:", list(encoders["Contract"].classes_))

if "Churn" in encoders:
    print("Churn classes:", list(encoders["Churn"].classes_))
else:
    print("Churn classes: no Churn encoder")