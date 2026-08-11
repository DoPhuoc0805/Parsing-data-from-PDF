"""
CLI entrypoint chính thức của pipeline trích xuất bảng phân công nhiệm vụ.

Cách dùng:
    python scripts/run_extract.py --input "data/raw/<file>.pdf"
    python scripts/run_extract.py --input "data/raw/<file>.pdf" --from-bronze

Kết quả ghi ra 3 tầng, dùng chung tên file gốc:
    data/bronze/<ten>.json   dòng thô đọc được, chưa diễn giải
    data/silver/<ten>.csv    bảng phẳng, mở bằng Excel
    data/silver/<ten>.json   bảng phẳng, dùng cho code
    data/gold/<ten>.json     gộp theo nhóm nhiệm vụ
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from task_extractor.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trich xuat bang phan cong nhiem vu (nhiem vu -> don vi chu tri/phoi hop) tu van ban."
    )
    parser.add_argument("--input", required=True, help="Duong dan file nguon (.pdf)")
    parser.add_argument(
        "--data-dir", default="data", help="Thu muc goc chua cac tang du lieu (mac dinh: data)"
    )
    parser.add_argument(
        "--from-bronze",
        action="store_true",
        help="Chay lai tu tang bronze da co, khong doc lai file nguon (dung khi debug)",
    )
    args = parser.parse_args()

    tasks = run_pipeline(args.input, args.data_dir, from_bronze=args.from_bronze)
    name = Path(args.input).stem
    print(f"Da xuat {len(tasks)} nhiem vu -> {args.data_dir}/{{bronze,silver,gold}}/{name}", file=sys.stderr)


if __name__ == "__main__":
    main()
