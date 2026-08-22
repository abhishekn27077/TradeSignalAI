import os
import ast
import json
import subprocess
from collections import defaultdict

def scan_imports(directory):
    imports = defaultdict(list)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=path)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports[path].append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports[path].append(node.module)
                except Exception as e:
                    print(f"Failed to parse {path}: {e}")
    return imports

def run_vulture(directory):
    try:
        result = subprocess.run(["python", "-m", "vulture", directory, "--min-confidence", "80"], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return str(e)

def generate_mermaid_architecture(directory):
    mermaid = ["graph TD"]
    modules = set()
    for root, dirs, _ in os.walk(directory):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        
        rel_path = os.path.relpath(root, directory)
        if rel_path == ".":
            continue
            
        parts = rel_path.split(os.sep)
        if len(parts) == 1:
            modules.add(parts[0])
            mermaid.append(f"  app --> {parts[0]}")
    
    return "\n".join(mermaid)

if __name__ == "__main__":
    app_dir = "app"
    
    print("=== DEPENDENCY AUDIT ===")
    imports = scan_imports(app_dir)
    print(f"Scanned {len(imports)} files for imports.")
    
    print("\n=== VULTURE DEAD CODE SCAN ===")
    dead_code = run_vulture(app_dir)
    print(dead_code[:1000] + ("\n... [truncated]" if len(dead_code) > 1000 else ""))
    
    print("\n=== ARCHITECTURE DIAGRAM (MERMAID) ===")
    print(generate_mermaid_architecture(app_dir))
    
    with open("audit_report.txt", "w") as f:
        f.write("=== DEPENDENCY AUDIT ===\n")
        f.write(json.dumps(imports, indent=2))
        f.write("\n\n=== VULTURE DEAD CODE SCAN ===\n")
        f.write(dead_code)
