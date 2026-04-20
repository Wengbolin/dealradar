import os
import shutil
from pathlib import Path

desktop = Path.home() / "Desktop"
target = desktop / "subito_system"

folders = {
    "code": [".py"],
    "data": [".db", ".json", ".txt"],
    "logs": [".log"],
    "archive": [".jpg", ".jpeg", ".png", ".pdf", ".mp4"],
}

# 创建目录
for f in folders:
    (target / f).mkdir(parents=True, exist_ok=True)

print("开始整理桌面...\n")

for item in desktop.iterdir():

    # 跳过系统目录和目标文件夹
    if item.name == "subito_system":
        continue

    if item.is_dir():
        continue

    moved = False

    for folder, exts in folders.items():
        if item.suffix.lower() in exts:
            dest = target / folder / item.name
            try:
                shutil.move(str(item), str(dest))
                print(f"移动: {item.name} → {folder}/")
                moved = True
            except Exception as e:
                print(f"跳过 {item.name}: {e}")
            break

    # 未分类文件进入 archive
    if not moved:
        dest = target / "archive" / item.name
        try:
            shutil.move(str(item), str(dest))
            print(f"归档: {item.name}")
        except Exception as e:
            print(f"跳过 {item.name}: {e}")

print("\n整理完成 ✅")
