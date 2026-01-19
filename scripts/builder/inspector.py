import os
from .utils import run_cmd

def get_apk_package_info(file_path, rootfs_path):
    """
    Finds which APK package owns the given file.
    It maps the file path from the temporary rootfs back to the host system 
    so 'apk info' can query the database correctly.
    
    Args:
        file_path (str): The path to the file (e.g., /rootfs/usr/lib/libssl.so.3)
        rootfs_path (str): The rootfs mount point (e.g., /rootfs)
        
    Returns:
        tuple: (package_name, package_version) or (None, None)
    """
    try:
        # 1. Map path back to host
        # Example: /rootfs/usr/lib/libssl.so.3 -> /usr/lib/libssl.so.3
        real_path_on_host = file_path
        if real_path_on_host.startswith(rootfs_path):
             basename = os.path.basename(file_path)
             # Libraries in Wolfi/Alpine are usually in /usr/lib, /lib, or /usr/local/lib
             candidates = [f"/usr/lib/{basename}", f"/lib/{basename}", f"/usr/local/lib/{basename}"]
             found = False
             for c in candidates:
                 if os.path.exists(c):
                     real_path_on_host = c
                     found = True
                     break
             
             # If not found in standard paths, assume it doesn't exist on host (maybe generated)
             if not found:
                 return None, None

        # 2. Query APK Database
        # apk info --who-owns returns: "/usr/lib/libssl.so.3 is owned by openssl-3.1.4-r0"
        pkg_info = run_cmd(f"apk info --who-owns {real_path_on_host}", ignore_errors=True)
        
        if pkg_info and " is owned by " in pkg_info:
            pkg_name = pkg_info.split(" is owned by ")[1].strip()
            
            # 3. Get detailed version
            # apk info -v returns: "openssl-3.1.4-r0"
            full_pkg_info = run_cmd(f"apk info -v {pkg_name}", ignore_errors=True)
            version = "unknown"
            
            if full_pkg_info:
                # Parsing logic: package-name-1.2.3-r0 -> extract 1.2.3-r0
                # We split by '-' from the right side to isolate version and release
                parts = pkg_name.rsplit('-', 2)
                if len(parts) >= 2:
                    version = parts[1] 
                    if len(parts) > 2: # add release (r0, r1) if exists
                         version += f"-{parts[2]}"
            
            return pkg_name, version
            
    except Exception:
        # Fail silently to avoid breaking the build process
        pass
        
    return None, None