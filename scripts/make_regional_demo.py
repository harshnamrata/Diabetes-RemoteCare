from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "sample" / "synthetic_diabetes_2019.csv"
OUT = ROOT / "data" / "sample" / "SYNTHETIC_regional_demo.csv"

rng = np.random.default_rng(7)
df = pd.read_csv(SRC).drop(columns=["Diabetic"])
sample = df.sample(n=400, random_state=7).reset_index(drop=True).astype(object)
regions = rng.choice(["Region A", "Region B", "Region C", "Region D", "Region E", "Region F"],
                     size=len(sample), p=[0.25, 0.20, 0.20, 0.15, 0.12, 0.08])
sample.insert(0, "Region", regions)

sample.loc[10, "BMI"] = "abc"
sample.loc[25, "Gender"] = "Male"
sample.loc[25, "Pregnancies"] = 2
sample.loc[40, "Region"] = ""
sample.loc[80, "Stress"] = "Never"
sample.loc[120, "Age"] = 200
sample.loc[150, "BMI"] = 45.0
sample.loc[60] = sample.loc[5]

sample.to_csv(OUT, index=False)
print(f"Wrote {OUT.name}: {len(sample)} data rows")
