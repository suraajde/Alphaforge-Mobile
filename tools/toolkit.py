import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent


TOOLS = {
    "1": ("Apply Patch", "apply_patch.py"),
    "2": ("Exit", None),
}


def clear():
    print("\n" * 2)


def header():
    print("=" * 70)
    print("AlphaForge Developer Toolkit v1.0")
    print("=" * 70)
    print()


def menu():

    while True:

        clear()
        header()

        for key, value in TOOLS.items():
            print(f"{key}. {value[0]}")

        print()

        choice = input("Select option : ").strip()

        if choice == "2":
            return

        if choice == "1":

            patch = input("\nPatch file : ").strip()

            if not patch:
                continue

            patch_path = Path(patch)

            if not patch_path.exists():
                print("\nPatch not found.")
                input("\nPress ENTER...")
                continue

            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "apply_patch.py"),
                    str(patch_path),
                ]
            )

            input("\nPress ENTER...")
            continue


if __name__ == "__main__":
    menu()