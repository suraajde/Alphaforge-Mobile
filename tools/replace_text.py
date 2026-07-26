from pathlib import Path
import shutil
import sys

print("=" * 70)
print("AlphaForge Developer Toolkit")
print("Replace Text Utility")
print("=" * 70)

file_path = input("Python file : ").strip()

if not file_path:
    print("No file specified.")
    sys.exit(1)

path = Path(file_path)

if not path.exists():
    print(f"\nERROR : {path} not found.")
    sys.exit(1)

print("\nEnter OLD text.")
print("Finish by typing a single line containing:")
print("END")
print("-" * 70)

old_lines = []

while True:
    line = input()

    if line == "END":
        break

    old_lines.append(line)

old_text = "\n".join(old_lines)

print("\nEnter NEW text.")
print("Finish by typing:")
print("END")
print("-" * 70)

new_lines = []

while True:
    line = input()

    if line == "END":
        break

    new_lines.append(line)

new_text = "\n".join(new_lines)

source = path.read_text(encoding="utf-8")

if old_text not in source:
    print("\nOld text was NOT found.")
    sys.exit(1)

backup = path.with_suffix(path.suffix + ".bak")

shutil.copy2(path, backup)

source = source.replace(old_text, new_text, 1)

path.write_text(
    source,
    encoding="utf-8",
)

print("\nReplacement completed successfully.")
print(f"Backup created : {backup}")
