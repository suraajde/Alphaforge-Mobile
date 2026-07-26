from pathlib import Path
import ast
import shutil
import textwrap


def find_function(source: str, function_name: str):
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node

        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == function_name:
                    return child

    return None


def main():

    print("=" * 70)
    print("AlphaForge Developer Toolkit")
    print("Replace Function v1.1")
    print("=" * 70)

    target_file = input("Python file      : ").strip()
    function_name = input("Function name    : ").strip()
    replacement_file = input("Replacement file : ").strip()

    target = Path(target_file)
    replacement = Path(replacement_file)

    if not target.exists():
        print("\nTarget file not found.")
        return

    if not replacement.exists():
        print("\nReplacement file not found.")
        return

    source = target.read_text(encoding="utf-8")

    try:
        node = find_function(source, function_name)
    except SyntaxError as ex:
        print("\nTarget file has syntax errors.")
        print(ex)
        return

    if node is None:
        print("\nFunction not found.")
        return

    replacement_source = replacement.read_text(
        encoding="utf-8"
    ).rstrip()

    replacement_source = textwrap.dedent(
        replacement_source
    )

    lines = source.splitlines(keepends=True)

    start = node.lineno - 1
    end = node.end_lineno

    indent = len(lines[start]) - len(lines[start].lstrip())

    indented = textwrap.indent(
        replacement_source,
        " " * indent,
    )

    updated = (
        "".join(lines[:start])
        + indented
        + "\n"
        + "".join(lines[end:])
    )

    try:
        ast.parse(updated)
    except SyntaxError as ex:
        print("\nReplacement would create invalid Python.")
        print(ex)
        print("\nNo changes were made.")
        return

    backup = target.with_suffix(
        target.suffix + ".bak"
    )

    shutil.copy2(
        target,
        backup,
    )

    target.write_text(
        updated,
        encoding="utf-8",
    )

    print("\nSUCCESS")
    print(f"Function '{function_name}' replaced.")
    print(f"Backup : {backup}")


if __name__ == "__main__":
    main()