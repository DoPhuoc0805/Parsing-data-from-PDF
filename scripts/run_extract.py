"""
CLI entrypoint chính thức của pipeline trích xuất bảng phân công nhiệm vụ từ PDF.

Cách dùng:
    python scripts/run_extract.py --input data/raw/<file>.pdf --output data/output/tasks.csv
    python scripts/run_extract.py --input data/raw/<file>.pdf --output data/output/tasks.json
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pdf_task_extractor.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trich xuat bang phan cong nhiem vu (nhiem vu -> don vi chu tri/phoi hop) tu file PDF."
    )
    parser.add_argument("--input", required=True, help="Duong dan file PDF dau vao")
    parser.add_argument("--output", required=True, help="Duong dan file output (.csv hoac .json)")
    args = parser.parse_args()

    records = run_pipeline(args.input, args.output)
    print(f"Da xuat {len(records)} record ra {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
