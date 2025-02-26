import os
import sys
import platform
import torch
from trellis_codebase.utils import *

PORT = 8000

# -------------- Configure Logging ----------------
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m-%d-%H:%M:%S',
    handlers=[logging.StreamHandler(stream=sys.stdout)], 
)
logger = logging.getLogger("trellis")

# -------------- Print Startup Info ----------------
logger.info(f"[System Info] Python: {platform.python_version():<8} | PyTorch: {torch.__version__:<8} | CUDA: {'not available' if not torch.cuda.is_available() else torch.version.cuda}")

# -------------- CMD parameters for trellis ----------------
import argparse
parser = argparse.ArgumentParser(description="Trellis API server")

parser.add_argument("--precision", 
                    choices=["float32", "float16"], 
                    default="float16",
                    help="Set the precision for pipeline, default to float16, to save VRAM and gain performance")

parser.add_argument("--device", 
                    choices=["cuda", "dynamic"], 
                    default="dynamic",
                    help="Set the device for pipeline, default to dynamic(option which required least vram)")

cmd_args = parser.parse_args()


# -------------- Configure Env Vars ----------------
os.environ['ATTN_BACKEND'] = 'xformers'    # or 'flash-attn'
os.environ['SPCONV_ALGO'] = 'native'       # or 'auto'
os.environ['U2NET_HOME'] = REMBG_MODEL_FOLDER

# -------------- FastAPI ----------------

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from trellis_codebase.router import router
from trellis_codebase.trellis_generator import TrellisGenerator
import subprocess
import ctypes

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Try to launch the trellis generator...")
    trellis_generator = TrellisGenerator.instance(device=cmd_args.device, precision=cmd_args.precision)
    logger.info("Trellis API Server is active and listening.")
    yield
    trellis_generator.close()
    logger.info("Trellis API Server Shutdown")

app = FastAPI(title="Trellis API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# -------------- Check if the nvidia driver version meets the minimum requirements ----------------
def get_cmd_encoding():
        # Get active console code page
        code_page = ctypes.windll.kernel32.GetConsoleOutputCP()
        
        # Handle UTF-8 special case
        return "utf-8" if code_page == 65001 else f"cp{code_page}"

def check_driver_version_manifest(driver_version):
    driver_version_components = list(map(int, driver_version.split('.')))
    manifest_driver_version_components = [527, 41]
    # make sure the length of version components the same
    max_len = max(len(driver_version_components), len(manifest_driver_version_components))
    driver_version_components += [0] * (max_len - len(driver_version_components))
    manifest_driver_version_components += [0] * (max_len - len(manifest_driver_version_components))
    for i in range(max_len):
        if driver_version_components[i] > manifest_driver_version_components[i]:
            return True
        elif driver_version_components[i] < manifest_driver_version_components[i]:
            return False
    return True


def check_nvidia_driver_version():
    try:
        process = subprocess.run(
            "nvidia-smi --query-gpu=driver_version --format=csv,noheader", 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding=get_cmd_encoding(), 
            check=True
        )
        if process.returncode == 0:
            driver_version = process.stdout.strip()
            logger.info(f"Detect Nvidia Driver Version: {driver_version}")
            return check_driver_version_manifest(driver_version)
        else:
            logger.info(f"Error Check Nvidia Driver Version: {process.stderr}")
            raise Exception(process.stderr)
    except Exception as e:
            logger.info(f"Error Check Nvidia Driver Version: {e}")

# -------------- Check if the port from cmd_args is in use ----------------
def check_port_is_in_use(port):
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
            logger.info(f"Port {port} is free.")
        return False
    except socket.error:
        logger.info(f"Port {port} is in use. Attempting to identify and terminate the process.")
        return True
    
def terminate_process_on_port(port):
    import psutil
    # Iterate through all processes to find the one using the port
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            connections = proc.net_connections(kind="inet")
            for conn in connections:
                if conn.laddr.port == port:
                    logger.info(f"Process {proc.info['name']} (PID: {proc.info['pid']}) is using port {port}.")
                    proc.terminate()
                    proc.wait() 
                    logger.info(f"Process terminated.")
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
            logger.warning(f"When checking information of process {proc.info['name']} (PID: {proc.info['pid']}), an error occurred: {e}")
            continue
        except Exception as e:
            logger.warning(f"When checking information of process {proc.info['name']} (PID: {proc.info['pid']}), an unexpected error occurred: {e}")
            continue
    return False

def check_uvicorn_running_condition(port):
    if check_nvidia_driver_version():
        port_is_in_use = check_port_is_in_use(port)
        if port_is_in_use:
            terminate_res = terminate_process_on_port(port)
            if terminate_res:
                return (True, "")
            else:
                return (False, f"Uvicorn needs to be run on port 8000, but the port is taken")
        else:
            return (True, "")
    else:
        return (False, f"Nvidia Driver version is too low. You need to update it at least version 527.41")

if __name__ == "__main__":
    uvicorn_can_run, check_res_message = check_uvicorn_running_condition(port=PORT)
    if uvicorn_can_run:
        uvicorn.run(
            app=app, 
            host="127.0.0.1", 
            port=PORT
        )
    else:
        sys.exit(check_res_message)


