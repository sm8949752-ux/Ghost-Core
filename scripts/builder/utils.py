import subprocess
import shutil
import platform
import os

def run_cmd(cmd, ignore_errors=False):
    """Executes a shell command and returns the output string."""
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            # print(f"Warning: Command failed: {cmd}\n{e.output.decode('utf-8')}")
            pass
        return None

def ensure_tools():
    """Downloads and setups necessary tools like libtree and lddtree."""
    if not shutil.which("lddtree"):
        run_cmd("wget -qO /usr/bin/lddtree https://raw.githubusercontent.com/ncopa/lddtree/master/lddtree.sh")
        run_cmd("chmod +x /usr/bin/lddtree")

    if not shutil.which("libtree"):
        arch = platform.machine()
        version = "v3.1.1"
        base_url = f"https://github.com/haampie/libtree/releases/download/{version}"
        url = ""
        
        if arch == "x86_64":
            url = f"{base_url}/libtree_x86_64"
        elif arch == "aarch64":
            url = f"{base_url}/libtree_aarch64"
            
        if url:
            run_cmd(f"wget -qO /usr/bin/libtree {url}")
            run_cmd("chmod +x /usr/bin/libtree")