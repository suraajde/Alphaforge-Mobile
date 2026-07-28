from pathlib import Path
import ast


def main():

    filename = input("Python file : ").strip()

    path = Path(filename)

    if not path.exists():
        print("File not found.")
        return

    source = path.read_text(encoding="utf-8")

    tree = ast.parse(source)

    for node in tree.body:

        if isinstance(node, ast.ClassDef):

            print(f"\nCLASS : {node.name}")
            print("-" * 70)

            for child in node.body:

                if isinstance(child, ast.FunctionDef):

                    print(
                        f"{child.lineno:4d} - {child.end_lineno:4d}  {child.name}"
                    )


if __name__ == "__main__":
    main()