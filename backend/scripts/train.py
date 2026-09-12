from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from app.core.features import FeatureEngine
from app.core.fraud import FraudModel
from app.core.policy import PolicyEngine
from app.core.propensity import PropensityBank, synth_labels
from app.core.segments import SegmentModel
from app.core.stress import StressModel
from app.db import artifacts
from app.db.documents import load_document

ROOT = Path(__file__).resolve().parents[1]


def main(ensure: bool = False) -> None:
    t0 = time.time()

    fp = artifacts.fingerprint()
    if ensure and artifacts.load(fp) is not None:
        print(f"→ model {fp[:12]} already in the database, nothing to train")
        return

    fe = FeatureEngine()
    as_of = date.fromisoformat(load_document("demo_checkpoints", default={})["today"])
    X = fe.compute_all(as_of)
    print(f"features       {X.shape[0]} customers x {X.shape[1]} features")

    seg = SegmentModel(k=6).fit(X)
    sizes = pd.Series(seg.predict(X)).value_counts().sort_index()
    print("\nsegments")
    for c, n in sizes.items():
        print(f"  {seg.name(int(c)):<26} {n:>4} customers")

    y = synth_labels(X)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)
    bank = PropensityBank().fit(Xtr, ytr)
    print("\npropensity models (held-out AUC)")
    aucs = {}
    for pid in y.columns:
        pred = bank.models[pid].predict_proba(Xte)[:, 1]
        auc = roc_auc_score(yte[pid], pred) if yte[pid].nunique() > 1 else float("nan")
        aucs[pid] = round(float(auc), 3)
        print(f"  {pid:<20} AUC {auc:.3f}   base rate {ytr[pid].mean():.2f}")
    bank.fit(X, y)

    policy = PolicyEngine(ROOT / "policies" / "rules.yaml")
    stress = StressModel(policy).fit(X)
    fraud = FraudModel(policy).fit(X)
    sc = stress.score_all(X)
    print(f"\nstress         {int(sc.stressed.sum())} of {len(sc)} customers above "
          f"{policy.rules['stress']['threshold']} threshold")

    artifacts.save(
        {"segments": seg, "propensity": bank, "stress": stress, "fraud": fraud,
         "trained_at": str(as_of), "auc": aucs},
        fp=fp,
        rows_trained_on=len(fe.txns),
    )
    print(f"\nsaved          model_artifacts/{fp[:12]} in postgres "
          f"({time.time() - t0:.1f}s total)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensure", action="store_true",
                    help="no-op if this code and dataset already have a model")
    main(**vars(ap.parse_args()))
