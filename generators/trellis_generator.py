import ctypes
from bpy.app.translations import pgettext as _
import asyncio
import importlib
import json
import os
import subprocess
import sys
import threading
import traceback

import requests
from ..utils import absolute_path
import bpy
from ..utils import PYTHON_DEPENDENCIES_FOLDER, TRELLISGEN_OUTPUT_FOLDER


class TrellisGenerator:

    http_base_url = "http://127.0.0.1:8000"
    
    ws_base_url = "ws://127.0.0.1:8000"

    _instance = None

    PYTHON_DEPENDENCIES = ("psutil==6.1.1", "websockets==11.0")

    # make sure there is only one generator instance
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(TrellisGenerator, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    @classmethod
    def instance(cls):
        return cls()
    
    def __init__(self):
        if self.initialized:
            return
        self.output_folder = TRELLISGEN_OUTPUT_FOLDER
        self.initialized = True

    def _check_driver_version_manifest(self, driver_version):
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

    def check_nvidia_driver_manifest(self):
        try:
            process = subprocess.run(
                "nvidia-smi --query-gpu=driver_version --format=csv,noheader", 
                capture_output=True, 
                text=True, 
                encoding=self._get_cmd_encoding(), 
                check=True
            )
            driver_version = process.stdout.strip()
            return self._check_driver_version_manifest(driver_version)
        except Exception as e:
            print(f"Error Check Nvidia Driver Version: {e}")
            return False

    def check_python_dependencies(self):
        if PYTHON_DEPENDENCIES_FOLDER not in sys.path:
            sys.path.insert(0, PYTHON_DEPENDENCIES_FOLDER)
        for dep in self.PYTHON_DEPENDENCIES:
            print(f"Need python dependency: {dep}")
            dep_name = dep.split("==")[0]
            dep_version = dep.split("==")[-1]
            try:
                dist = importlib.metadata.distribution(dep_name)
                print(f"Find dependency in current environment: {dep_name}=={dist.version}")
                if(dist.version != dep_version):
                    print("Version of dependency in current environment is not equals to what is declared in addon dependencies file.")
                    return False

            except Exception as e:
                print(f"Dependency not found in current environment: {dep}")
                return False
        return True
    
    def _get_cmd_encoding(self):
        # Get active console code page
        code_page = ctypes.windll.kernel32.GetConsoleOutputCP()
        # Handle UTF-8 special case
        return "utf-8" if code_page == 65001 else f"cp{code_page}"

    def install_python_dependencies(self, operator, gen_props):
        gen_props.trellis_python_dependencies_install_status = "installing"
        for dep in self.PYTHON_DEPENDENCIES:
            gen_props.trellis_python_dependencies_install_message = _("Installing dependency: ", '*') + dep
            try:
                subprocess.run(
                    f'"{sys.executable}" -m pip install {dep} --no-cache-dir --target "{PYTHON_DEPENDENCIES_FOLDER}" --index-url https://mirrors.aliyun.com/pypi/simple',
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding=self._get_cmd_encoding(),
                    errors="replace",
                    check=True,
                )
                gen_props.trellis_python_dependencies_install_message = _("Installation of Python dependency success: ", '*') + dep
            except Exception as e:
                print(f"Error: Installing python dependency {dep} failed")
                print(traceback.format_exc())
                gen_props.trellis_python_dependencies_install_message = _("Installation of Python dependency failed: ", '*') + dep
                gen_props.trellis_python_dependencies_install_status = "installing_failed"
                gen_props.trellis_python_dependencies_installed = False
                bpy.ops.blenderai_zealo.tripo_check_python_dependencies()
                operator.end_token = True
                return 
        gen_props.trellis_python_dependencies_install_status = "installing_end"
        gen_props.trellis_python_dependencies_installed = True
        gen_props.trellis_python_dependencies_install_message = ""
        bpy.ops.blenderai_zealo.tripo_check_python_dependencies()
        operator.end_token = True
        return 
    
    def _get_process_on_8000(self):
        process_on_8000 = None
        import psutil
        for conn in psutil.net_connections(kind="inet"):
            try:
                if conn.laddr.port == 8000:
                    process_on_8000 = psutil.Process(conn.pid)
                    break
            except Exception as e:
                print(f"An unexpected error occurred when get information of connection of process. \n{traceback.format_exc()}")
                continue
        return process_on_8000


    def _check_process_on_8000_belongs_to_current_process(self, process) -> bool:
        import psutil
        current_pid = os.getpid()
        while process:
            if process.pid == current_pid:
                return True
            process = process.parent()
        return False
    
    def _check_process_on_8000_is_trellis(self, process):
        try:
            url = f"{self.http_base_url}/check_server_status"
            response = requests.get(url, timeout=2)
            response.raise_for_status()
            result = response.json()
            if result["code"] != 0:
                return False
            else:
                return True
        except Exception as e:
            print(f"An unexpected error occurred when check server status: {e}")
            return False

    def check_ready(self):
        process_on_8000 = self._get_process_on_8000()
        if process_on_8000 is None:
            return False
        else:
            process_on_8000_belongs_to_current_process = self._check_process_on_8000_belongs_to_current_process(process_on_8000)
            if process_on_8000_belongs_to_current_process:
                process_is_trellis = self._check_process_on_8000_is_trellis(process_on_8000)
                if process_is_trellis:
                    return True
                else:
                    return False
            else:
                return False
            
    def check_process_on_8000_is_on_none_self_process(self):
        process_on_8000 = self._get_process_on_8000()
        if process_on_8000 is None:
            return False
        else:
            process_on_8000_belongs_to_current_process = self._check_process_on_8000_belongs_to_current_process(process_on_8000)
            if process_on_8000_belongs_to_current_process:
                return False
            else:
                return True

    def _get_cmd_encoding(self):
        # Get active console code page
        code_page = ctypes.windll.kernel32.GetConsoleOutputCP()
        
        # Handle UTF-8 special case
        return "utf-8" if code_page == 65001 else f"cp{code_page}"

    def make_ready(self, operator, gen_props):
        try:
            RED = '\033[91m'
            GREEN = '\033[32m'
            RESET = '\033[0m' 
            gen_props.trellis_make_ready_status = "making_ready"
            gen_props.trellis_make_ready_message = _("Try to launch Trellis Generator...", '*')
            def print_stdout(pipe):
                try:
                    for line in iter(pipe.readline, ''):
                        try:
                            line = line.strip()
                            print(f"{GREEN}[Trellis Stdout] {line}{RESET}")
                        except Exception as e:
                            print(f"{GREEN}Pipe stdout readline failed since error:\n{traceback.format_exc()}{RESET}")
                            continue
                except Exception as e:
                    print(f"{GREEN}Pipe stdout terminated since error:\n{traceback.format_exc()}{RESET}")
                finally:
                    print(f"{GREEN}[Trellis Stdout Pipeline Terminated]{RESET}")

            def print_stderr(pipe):
                try:
                    check_startup_string = True
                    for line in iter(pipe.readline, ''):
                        try:
                            line = line.strip()
                            if check_startup_string:
                                gen_props.trellis_make_ready_message = line
                                if self.http_base_url in line:
                                    check_startup_string = False
                                    gen_props.trellis_make_ready_status = "making_ready_end"
                                    gen_props.trellis_ready = True
                            print(f"{RED}[Trellis Stderr] {line}{RESET}")
                        except Exception as e:
                            print(f"{RED}Pipe readline failed since error:\n{traceback.format_exc()}{RESET}")
                            continue
                except Exception as e:
                    print(f"{RED}Pipe stderr terminated since error:\n{traceback.format_exc()}{RESET}")
                finally:
                    print(f"{RED}[Trellis Stderr Pipeline Terminated]{RESET}")
                
            trellis_precision = operator.trellis_start_parameters["precision"]
            trellis_device = operator.trellis_start_parameters["device_mode"]
            with subprocess.Popen(
                f'call "{absolute_path("trellis-api/run.bat")}" --precision {trellis_precision} --device {trellis_device} --reinstall false & exit /b %ERRORLEVEL%', 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True, 
                text=True,
                encoding=self._get_cmd_encoding(), 
                errors="replace",
            ) as process:
                stderr_thread = threading.Thread(target=print_stderr, args=(process.stderr, ))
                stdout_thread = threading.Thread(target=print_stdout, args=(process.stdout, ))
                stderr_thread.start()
                stdout_thread.start()
                process.wait()
                if process.returncode != 0:
                    gen_props.trellis_make_ready_message = _("Trellis Generator exited with error", '*')
                else:
                    gen_props.trellis_make_ready_message = _("Trellis Generator exited normally", '*')
        except Exception as e:
            gen_props.trellis_make_ready_message = _("Trellis Generator exited with unexpected error", '*')
        finally:
            stderr_thread.join()
            stdout_thread.join()
            gen_props.trellis_make_ready_status = "making_ready_failed"
            gen_props.trellis_ready = False
            operator.end_token = True

    def terminate_ready_trellis_process(self, operator):
        trellis_running_on_self_process = self.check_ready()
        if trellis_running_on_self_process:
            proc = self._get_process_on_8000()
            if proc:
                print(f"Terminate trellis process...")
                proc.terminate()
                proc.wait()
                return True
            else:
                operator.report({"ERROR"}, _("No Trellis running", '*'))
                return False
        else:
            operator.report({"ERROR"}, _("No Trellis running", '*'))
            return False
        

    def _report_message(self, result, operator):
        if result.get("code") != 0:
            operator.report(
                {"ERROR"}, 
                _("Error code: ", '*') + str(result['code']) +
                _("Error message: ", '*') + result["message"] + 
                _("Suggestion: ", '*') + result["suggestion"]
            )
    
    def _upload_image(self, image_path, type):
        url = f"{self.http_base_url}/upload_image"
        try:
            # raise RuntimeError("Test Error")
            with open(image_path, 'rb') as f:
                files = {'image': (image_path, f, f'image/{type}')}
                response = requests.post(url, files=files)
                response.raise_for_status()
                result = response.json()
                return result
        except Exception as e:
            return {
                "code": -1, 
                "message": _("There is something wrong on the local machine: ", '*') + str(e), 
                "suggestion": _("Bring the code and message and contact the admin of this blender addon", '*')
            }
    
    def _create_img23d_task(self, task):
        url = f"{self.http_base_url}/img23d_task"
        data = {
            "image_type": task.image.type,
            "image_token": task.image.token, 
            "preprocess_image": task.image.preprocess_image, 
            "output_type": task.output.type, 
        }
        try:
            response = requests.post(
                url, 
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "code": -1,
                "message": _("There is something wrong on the local machine to request a connection to", '*') + url + _("since error: ", '*') + str(e), 
                "suggestion": _("Please try to do it again or contact to admin of this blender addon", '*')
            }

    async def _watch_task(self, task):
        url = f"{self.ws_base_url}/img23d_task/watch/{task.id}"
        try:
            import websockets
            async with websockets.connect(url) as websocket:
                # raise RuntimeError("Test Error")
                data = None
                while True:
                    message = await websocket.recv()
                    result = json.loads(message)
                    data = result["data"]
                    task.watch_progress = f'{data["generate_status"]}: {data["progress"]}%'
                    if result["event"] == "finalized":
                        if data["generate_status"] == "generating_failed":
                            return {
                                "code": -2, 
                                "message": _("Task generation failed since an error: ", '*') + data['generate_failed_message'], 
                                "suggestion": _("Try to re-watch the task or contact the admin of this blender addon.", '*')
                            }
                        break
                result["code"] = 0
                return result
        except websockets.exceptions.ConnectionClosed as e:
            return {
                "code": -1, 
                "message": _("Something wrong on the local machine. Code: ", '*') + str(e.code) + _("Reason: ", '*') + e.reason, 
                "suggestion": _("Try to do it again or contact the admin of this blender addon.", '*')
            }
        except Exception as e:
            return {
                "code": -1, 
                "message": _("Something wrong on the local machine: ", '*') + str(e), 
                "suggestion": _("Try to do it again or contact the admin of this blender addon.", '*')
            }

    def _get_task_output_url(self, task):
        url = f"{self.http_base_url}/img23d_task/{task.id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            return result
        except Exception as e:
            return {
                "code": -1,
                "message": f"There is an unexpected error: {e}",
                "suggestion": "Bring the code and message and contact the admin of the blender addon"
            }

    def _download_model(self, task):
        get_url_result = self._get_task_output_url(task)
        if get_url_result["code"] == 0:
            partial_url = get_url_result["data"]["output_url"]
            url = f"{self.http_base_url}{partial_url}"
            local_filepath = os.path.join(self.output_folder, f"{task.id}.glb")
            try:
                # raise RuntimeError("Test Error")
                progress = 0
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    with open(local_filepath, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
                                progress += len(chunk)
                                progress_percentage = round((progress / total_size) * 100, 2)
                                task.output.download_progress = f"{progress_percentage}%"
                    return {
                        "code": 0, 
                        "data": {
                            f"local_filepath": local_filepath
                        }
                    }
            except Exception as e:
                return {
                    "code": -1, 
                    "message": _("An unexpected error occurred: ", '*') + str(e), 
                    "suggestion": _("Bring the code and message and contact the admin of the blender addon", '*')
                }
        else:
            return get_url_result


    def image23d(self, operator, task):
        task.image.upload_status = "uploading"
        upload_image_result = self._upload_image(task.image.local_filepath, task.image.type)
        if upload_image_result["code"] != 0:
            task.image.upload_status = "uploading_failed"
            self._report_message(upload_image_result, operator)
            operator.end_token = True
        else:
            task.image.upload_status = "uploading_end"
            task.image.token = upload_image_result["data"]["image_token"]
            task.create_status = "creating"
            task_create_result = self._create_img23d_task(task)
            if task_create_result["code"] != 0:
                task.create_status = "creating_failed"
                self._report_message(task_create_result, operator)
                operator.end_token = True
            else:
                task.create_status = "creating_end"
                task.id = task_create_result["data"]["task_id"]
                task.watch_status = "watching"
                watch_task_result = asyncio.run(self._watch_task(task))
                if watch_task_result["code"] != 0:
                    task.watch_status = "watching_failed"
                    self._report_message(watch_task_result, operator)
                    operator.end_token = True
                else:
                    task.watch_status = "watching_end"

                    # download model
                    task.output.download_status = "downloading"
                    download_result = self._download_model(task)
                    if download_result["code"] == 0:
                        task.output.download_status = "downloading_end"
                        task.output.local_filepath = download_result["data"]["local_filepath"]
                    else:
                        task.output.download_status = "downloading_failed"
                        self._report_message(download_result, operator)
                    operator.end_token = True

    def rewatch_img23d_task(self, operator, task):
        task.watch_status = "watching"
        watch_task_result = asyncio.run(self._watch_task(task))
        if watch_task_result["code"] != 0:
            task.watch_status = "watching_failed"
            self._report_message(watch_task_result, operator)
            operator.end_token = True
        else:
            task.watch_status = "watching_end"            
            # download model
            task.output.download_status = "downloading"
            download_result = self._download_model(task)
            if download_result["code"] == 0:
                task.output.download_status = "downloading_end"
                task.output.local_filepath = download_result["data"]["local_filepath"]
            else:
                task.output.download_status = "downloading_failed"
                self._report_message(download_result, operator)
            operator.end_token = True


    def redownload_img23d_task(self, operator, task):
        task.output.download_status = "downloading"
        download_result = self._download_model(task)
        if download_result["code"] == 0:
            task.output.download_status = "downloading_end"
            task.output.local_filepath = download_result["data"]["local_filepath"]
        else:
            task.output.download_status = "downloading_failed"
            self._report_message(download_result, operator)
        operator.end_token = True

