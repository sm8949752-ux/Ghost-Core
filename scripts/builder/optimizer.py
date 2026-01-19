import os
import shutil
from .utils import run_cmd
from .inspector import get_apk_package_info

def copy_and_strip(lib_path, dest_dir, rootfs_path):
    """
    Copies a library from the host system to the rootfs, 
    strips it securely to reduce size, and fetches package metadata.

    Args:
        lib_path (str): Source path on host (e.g., /usr/lib/libssl.so.3)
        dest_dir (str): Destination directory in rootfs (e.g., /rootfs/usr/lib)
        rootfs_path (str): Rootfs base path (used for inspector lookup)

    Returns:
        dict: Metadata {'name': ..., 'version': ..., 'file': ...} if found, else None.
    """
    
    # 1. Validation
    if not os.path.exists(lib_path):
        # Should not happen if analyzer did its job, but safety first
        return None

    # Resolve symlinks to find the REAL file
    real_path = os.path.realpath(lib_path)
    lib_name = os.path.basename(real_path)
    dest_path = os.path.join(dest_dir, lib_name)

    # 2. Copy (Only if not already there)
    # This prevents overwriting or redundant work
    if not os.path.exists(dest_path):
        try:
            shutil.copy2(real_path, dest_path)
        except IOError as e:
            print(f"Error copying {real_path}: {e}")
            return None
        
        # 3. Secure Strip
        # We use --strip-unneeded which is safe for shared libraries (.so).
        # It removes debug symbols but keeps symbol table required for dynamic linking.
        # ignore_errors=True because sometimes strip fails on special system files, which is fine.
        run_cmd(f"strip --strip-unneeded {dest_path}", ignore_errors=True)
        
        # 4. Inspect Metadata (While we are at it)
        # We query the origin (real_path) to get accurate APK info
        pkg_name, pkg_ver = get_apk_package_info(real_path, rootfs_path)
        
        if pkg_name:
            return {
                "name": pkg_name, 
                "version": pkg_ver,
                "file": lib_name
            }
            
    # If file existed, we still might want to return metadata if needed, 
    # but for this logic, we assume processed files are handled.
    return None