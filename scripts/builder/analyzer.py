import os
import shutil
from .utils import run_cmd

def get_dependencies(file_path):
    """
    Uses lddtree, libtree, scanelf, and ldd -r to find ALL dependencies.
    Returns a set of absolute file paths.
    """
    deps = set()
    
    # 1. lddtree 
    # Good for basic dependency tree walking
    out = run_cmd(f"lddtree -l {file_path}", ignore_errors=True)
    if out:
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("/") and os.path.isfile(line):
                deps.add(os.path.realpath(line))

    # 2. libtree (Visualizer Tool)
    # Often catches edge cases that lddtree might miss
    if shutil.which("libtree"):
        out = run_cmd(f"libtree -p {file_path}", ignore_errors=True)
        if out:
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("/") and os.path.isfile(line):
                    deps.add(os.path.realpath(line))

    # 3. scanelf (ELF Header Parser)
    # Reads the ELF NEEDED section directly
    if shutil.which("scanelf"):
        out = run_cmd(f"scanelf --needed --nobanner --format '%n#p' {file_path}", ignore_errors=True)
        if out:
            needed_libs = out.replace(',', ' ').split()
            # We then cross-reference with ldd to find the path
            ldd_out = run_cmd(f"ldd {file_path}", ignore_errors=True)
            if ldd_out:
                for lib in needed_libs:
                    for ldd_line in ldd_out.splitlines():
                        if lib in ldd_line and "=>" in ldd_line:
                            parts = ldd_line.split("=>")[1].split()
                            if parts and parts[0].startswith("/"):
                                deps.add(os.path.realpath(parts[0]))

    # 4. ldd -r (Symbol Resolution Check)
    # Critical for catching missing symbols/objects at runtime
    out_r = run_cmd(f"ldd -r {file_path}", ignore_errors=True)
    if out_r:
        for line in out_r.splitlines():
            # Standard ldd line: "libssl.so.3 => /usr/lib/libssl.so.3 (0x...)"
            if "=>" in line:
                parts = line.split("=>")[1].split()
                if parts and parts[0].startswith("/"):
                    deps.add(os.path.realpath(parts[0]))
    
    return deps