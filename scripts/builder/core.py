import os
import sys
import argparse
import glob
from .utils import ensure_tools, run_cmd
from .analyzer import get_dependencies
from .optimizer import copy_and_strip
from .sbom import generate_sbom

def find_elf_files(root_dir):
    """Recursively find all ELF files (binaries and libraries) in root_dir."""
    elf_files = []
    print(f">>> [Auto-Discovery] Scanning {root_dir} for ELF files...")
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.islink(full_path):
                continue
            
            try:
                with open(full_path, 'rb') as f:
                    header = f.read(4)
                    if header == b'\x7fELF':
                        elf_files.append(full_path)
            except:
                pass
    return elf_files

def main():
    parser = argparse.ArgumentParser(description="Ghost Core Smart Builder")
    parser.add_argument("--rootfs", required=True, help="Path to rootfs directory")
    parser.add_argument("--nginx-version", required=True, help="Nginx Version")
    parser.add_argument("--output-sbom", required=True, help="Path to save SBOM JSON")
    
    args = parser.parse_args()
    
    ROOTFS = args.rootfs
    DEST_LIB = os.path.join(ROOTFS, "usr/lib")
    DEST_SBIN = os.path.join(ROOTFS, "usr/sbin")
    
    # 1. Setup Environment
    print(">>> [Builder] Setting up tools...")
    os.makedirs(DEST_LIB, exist_ok=True)
    os.makedirs(DEST_SBIN, exist_ok=True)
    ensure_tools()
    
    # 2. Auto-Discover Targets
    target_files = find_elf_files(ROOTFS)
    if not target_files:
        print("⚠️  WARNING: No ELF files found in rootfs!")
        sys.exit(1)

    print(f"    -> Found {len(target_files)} ELF targets.")

    # 3. Resolve Dependencies
    print(f">>> [Builder] Resolving dependencies...")
    all_deps = set()
    
    for target in target_files:
        deps = get_dependencies(target)
        all_deps.update(deps)

    print(f"    -> Found {len(all_deps)} unique libraries required.")

    # 4. Copy, Optimize & Inspect
    print(">>> [Builder] Processing libraries...")
    sbom_components = []
    
    for lib_path in all_deps:
        # Skip if the dependency is one of the targets itself
        is_target = False
        for target in target_files:
            if os.path.abspath(target) == os.path.abspath(lib_path):
                is_target = True
                break
        if is_target:
            continue
            
        # Process library
        meta = copy_and_strip(lib_path, DEST_LIB, ROOTFS)
        if meta:
            sbom_components.append(meta)
        
        # Handle Symlinks
        link_name = os.path.basename(lib_path)
        lib_name = os.path.basename(os.path.realpath(lib_path))
        dest_link = os.path.join(DEST_LIB, link_name)
        
        if lib_name != link_name:
            if os.path.lexists(dest_link):
                os.remove(dest_link)
            os.symlink(lib_name, dest_link)

    # 5. Generate SBOM
    print(f">>> [Builder] Generating SBOM at {args.output_sbom}...")
    generate_sbom(args.nginx_version, sbom_components, args.output_sbom)
    
    # 6. Update Cache
    print(">>> [Builder] Updating ld.so.cache...")
    if os.path.exists("/sbin/ldconfig"):
        run_cmd(f"/sbin/ldconfig -r {ROOTFS}")
        
    print(">>> [Builder] Build Complete Successfully.")

if __name__ == "__main__":
    main()