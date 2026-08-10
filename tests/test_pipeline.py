"""Unit test cho pipeline.py: nối Bước 1-2-3 và xuất file."""

import json
from pathlib import Path

import pandas as pd

from src.pdf_task_extractor.pipeline import run_pipeline

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"


def test_run_pipeline_exports_json(tmp_path):
    output_path = tmp_path / "kh277.json"
    records = run_pipeline(str(KH277_PDF), str(output_path))

    assert len(records) == 33
    with open(output_path, encoding="utf-8") as f:
        exported = json.load(f)
    assert exported == records


def test_run_pipeline_exports_csv(tmp_path):
    output_path = tmp_path / "cv6582.csv"
    records = run_pipeline(str(CV6582_PDF), str(output_path))

    assert len(records) == 12
    df = pd.read_csv(output_path)
    assert len(df) == 12
    assert "ma_nhiem_vu" in df.columns
