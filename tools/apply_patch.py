from pathlib import Path
import shutil
import sys


def main():

    if len(sys.argv) != 2:
        print("\nUsage:")
        print("python tools\\apply_patch.py <patch_file>")
        return

    patch_file = Path(sys.argv[1])

    if not patch_file.exists():
        print(f"\nPatch file not found:\n{patch_file}")
        return

    lines = patch_file.read_text(
        encoding="utf-8"
    ).splitlines()

    target = None
    old = []
    new = []

    mode = None

    for line in lines:

        if line.startswith("FILE:"):
            target = Path(
                line[5:].strip()
            )

        elif line == "<<<<OLD":
            mode = "old"

        elif line == ">>>>NEW":
            mode = "new"

        elif line == ">>>>END":
            mode = None

        else:

            if mode == "old":
                old.append(line)

            elif mode == "new":
                new.append(line)

    if target is None:
        print("Patch missing FILE:")
        return

    if not target.exists():
        print(f"Target file not found:\n{target}")
        return

    source = target.read_text(
        encoding="utf-8"
    )

    old_text = "\n".join(old)
    new_text = "\n".join(new)

    if old_text not in source:
        print("\nOld block not found.")
        return

    backup = target.with_suffix(
        target.suffix + ".bak"
    )

    shutil.copy2(
        target,
        backup,
    )

    source = source.replace(
        old_text,
        new_text,
        1,
    )

    target.write_text(
        source,
        encoding="utf-8",
    )

    print("\nPatch applied successfully.")
    print(f"Backup : {backup}")


if __name__ == "__main__":
    main()