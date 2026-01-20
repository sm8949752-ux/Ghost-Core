import os
import sys
import argparse
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
                    if f.read(4) == b'\x7fELF':
                        elf_files.append(full_path)
            except Exception:
                pass

    return elf_files


def main():
    parser = argparse.ArgumentParser(description="Ghost Core Smart Builder")

    parser.add_argument("--rootfs", required=True, help="Path to rootfs directory")
    parser.add_argument("--nginx-version", required=True, help="Nginx version")
    parser.add_argument("--name", required=True, help="Application name (e.g. nginx)")
    parser.add_argument("--source-url", required=True, help="Source or download URL")
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
        print(" WARNING: No ELF files found in rootfs!")
        sys.exit(1)

    print(f"    -> Found {len(target_files)} ELF targets.")

    # 3. Resolve Dependencies
    print(">>> [Builder] Resolving dependencies...")
    all_deps = set()

    for target in target_files:
        deps = get_dependencies(target)
        all_deps.update(deps)

    print(f"    -> Found {len(all_deps)} unique libraries required.")

    # 4. Copy, Optimize & Inspect
    print(">>> [Builder] Processing libraries...")
    sbom_components = []

    for lib_path in all_deps:
        # Skip if dependency is one of the targets itself
        if any(os.path.abspath(lib_path) == os.path.abspath(t) for t in target_files):
            continue

        # Process library
        meta = copy_and_strip(lib_path, DEST_LIB, ROOTFS)
        if meta:
            sbom_components.append(meta)

        # Handle symlinks
        link_name = os.path.basename(lib_path)
        real_name = os.path.basename(os.path.realpath(lib_path))
        dest_link = os.path.join(DEST_LIB, link_name)

        if real_name != link_name:
            if os.path.lexists(dest_link):
                os.remove(dest_link)
            os.symlink(real_name, dest_link)

    # 5. Generate SBOM
    print(f">>> [Builder] Generating SBOM at {args.output_sbom}...")
    generate_sbom(
        version=args.nginx_version,
        name=args.name,
        url=args.source_url,
        components=sbom_components,
        output_path=args.output_sbom
    )

    # 6. Update ld.so.cache
    print(">>> [Builder] Updating ld.so.cache...")
    if os.path.exists("/sbin/ldconfig"):
        run_cmd(f"/sbin/ldconfig -r {ROOTFS}")

    print(">>> [Builder] Build Complete Successfully.")


if __name__ == "__main__":
    main()
