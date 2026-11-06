import os
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv


def main():
    load_dotenv()

    data_dir = os.getenv("SUTELLITE_DATA_DIR")

    if not data_dir:
        raise SystemExit("ERROR: SUTELLITE_DATA_DIR is not configured.")

    raw_dir = Path(data_dir)

    if not raw_dir.is_dir():
        raise SystemExit(f"ERROR: Data directory not found: {raw_dir}")

    inventory = defaultdict(lambda: {"files": 0, "bytes": 0})

    csv_files = list(raw_dir.rglob("*.csv"))

    for file_path in csv_files:
        relative_path = file_path.relative_to(raw_dir)
        folder = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"

        inventory[folder]["files"] += 1
        inventory[folder]["bytes"] += file_path.stat().st_size

    print("SUTELLITE - DATA INVENTORY")
    print("=" * 55)
    print(f"Data directory: {raw_dir}")
    print(f"Total CSV files: {len(csv_files)}")

    print("\nFILES BY FOLDER")
    print("-" * 55)

    for folder, stats in sorted(inventory.items()):
        size_gb = stats["bytes"] / (1024 ** 3)

        print(f"\n{folder} ({stats['files']} files, {size_gb:.3f} GB)")

        folder_path = raw_dir / folder

        for file_path in sorted(folder_path.glob("*.csv")):
            print(f"    {file_path.name}")

    total_bytes = sum(item["bytes"] for item in inventory.values())

    print("-" * 55)
    print(f"TOTAL SIZE: {total_bytes / (1024 ** 3):.3f} GB")


if __name__ == "__main__":
    main()