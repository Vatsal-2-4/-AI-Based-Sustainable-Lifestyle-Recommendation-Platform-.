from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "dataset"

def load_emission_factors():
    return pd.read_csv(DATA_DIR / "emission_factors.csv")

def load_actions():
    return pd.read_csv(DATA_DIR / "actions.csv")
