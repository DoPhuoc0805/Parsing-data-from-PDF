"""Unit test cho pipeline.py: nối các tầng raw -> bronze -> silver -> gold."""

import json
from pathlib import Path

import pandas as pd

from src.task_extractor.pipeline import run_pipeline

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"


def test_run_pipeline_writes_all_three_layers(tmp_path):
    tasks = run_pipeline(str(KH277_PDF), str(tmp_path))
    name = KH277_PDF.stem

    assert len(tasks) == 33

    bronze = json.loads((tmp_path / "bronze" / f"{name}.json").read_text(encoding="utf-8"))
    assert len(bronze) == 41  # dòng thô, chưa loại dòng nhóm cha
    assert "chi_tiet" in bronze[0]

    silver = json.loads((tmp_path / "silver" / f"{name}.json").read_text(encoding="utf-8"))
    assert silver == tasks  # silver giữ dạng phẳng

    df = pd.read_csv(tmp_path / "silver" / f"{name}.csv")
    assert len(df) == 33
    assert "ma_nhiem_vu" in df.columns

    gold = json.loads((tmp_path / "gold" / f"{name}.json").read_text(encoding="utf-8"))
    assert sum(len(group["data"]) for group in gold) == len(tasks)
    for group in gold:
        assert "nhom_nhiem_vu" in group
        for task in group["data"]:
            assert "nhom_nhiem_vu" not in task


def test_run_pipeline_from_bronze_skips_reading_source(tmp_path):
    first = run_pipeline(str(CV6582_PDF), str(tmp_path))
    again = run_pipeline(str(CV6582_PDF), str(tmp_path), from_bronze=True)

    assert first == again
    assert len(again) == 12
