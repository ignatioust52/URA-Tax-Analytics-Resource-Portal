import ast
import builtins
import sys

def check_file(filename):
    with open(filename, "r") as f:
        src = f.read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print(f"Syntax error in {filename}: {e}")
        return

    # Find imported names
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name)
                if alias.asname:
                    imported_names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.name)
                if alias.asname:
                    imported_names.add(alias.asname)
            # handle 'from module import *'
            if '*' in [alias.name for alias in node.names]:
                imported_names.add('*')

    # Find defined functions/classes/variables at module level
    defined_names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)

    # Walk all name nodes
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)

    missing = []
    builtin_names = dir(builtins)
    for name in used_names:
        if name not in imported_names and name not in defined_names and name not in builtin_names:
            if '*' not in imported_names:
                missing.append(name)
            elif name in ['st', 'pd']: # quick checks
                missing.append(name)

    if missing:
        print(f"{filename} missing names (potentially): {missing}")
    else:
        print(f"{filename} looks mostly ok (if * imports provide the rest)")

check_file('core/db_departments.py')
check_file('core/db_resources.py')
check_file('views/public_resources.py')
