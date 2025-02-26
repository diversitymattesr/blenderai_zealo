import ctypes
import traceback
from bpy.app.translations import pgettext as _
import os
import json
import sys
import importlib.metadata
import requests
import subprocess
import asyncio
from ..utils import *
import bpy
from ..utils import PYTHON_DEPENDENCIES_FOLDER,TRIPOGEN_OUTPUT_FOLDER


class TripoGenerator:

    http_base_url = "https://api.tripo3d.ai/v2/openapi"

    ws_base_url = "wss://api.tripo3d.ai/v2/openapi"

    PYTHON_DEPENDENCIES = ("websockets==11.0", )

    _instance = None

    # make sure there is only one generator instance
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(TripoGenerator, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    @classmethod
    def instance(cls):
        return cls()
    
    def __init__(self):
        if self.initialized:
            return
        self.output_folder = TRIPOGEN_OUTPUT_FOLDER
        self.initialized = True

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
        gen_props.tripo_python_dependencies_install_status = "installing"
        for dep in self.PYTHON_DEPENDENCIES:
            gen_props.tripo_python_dependencies_install_message = _("Installing ", '*') + dep
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
                gen_props.tripo_python_dependencies_install_message = _("Installation of this dep success: ", '*') + dep
            except Exception as e:
                print(f"Error: Installing python dependency {dep} failed")
                print(traceback.format_exc())
                gen_props.tripo_python_dependencies_install_message = _("Installation of this dep failed: ", '*') + dep 
                gen_props.tripo_python_dependencies_install_status = "installing_failed"
                gen_props.tripo_python_dependencies_installed = False
                bpy.ops.blenderai_zealo.trellis_check_python_dependencies()
                operator.end_token = True
                return 
        gen_props.tripo_python_dependencies_install_status = "installing_end"
        gen_props.tripo_python_dependencies_install_message = ""
        gen_props.tripo_python_dependencies_installed = True
        bpy.ops.blenderai_zealo.trellis_check_python_dependencies()
        operator.end_token = True
        return 
    
    def check_ready(self, operator, api_key, gen_props):
        try:
            gen_props.tripo_check_ready_status = "checking"
            gen_props.tripo_check_ready_message = _("Checking Tripo API Key: ", '*') + api_key
            url = f"{self.http_base_url}/user/balance"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result["code"] == 0:
                gen_props.tripo_ready = True
                gen_props.tripo_check_ready_status = "checking_end"
                gen_props.tripo_check_ready_message = _("Tripo API Key Correct.", '*') + _("User Balance: ", '*') + str(result['data']['balance'])
            else:
                gen_props.tripo_ready = False
                gen_props.tripo_check_ready_status = "checking_failed"
                gen_props.tripo_check_ready_message = _("Tripo API Key Incorrect Since Error: ", '*') + result['message']
            operator.end_token = True
        except Exception as e:
            gen_props.tripo_ready = False
            gen_props.tripo_check_ready_status = "checking_failed"
            gen_props.tripo_check_ready_message = _("Tripo API Key Incorrect Since Error: ", '*') + str(e)
            operator.end_token = True
            


    def _create_txt23d_task(self, task, api_key):
        url = f"{self.http_base_url}/task"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        output_type_mapping = {
            "base_model": {
                "texture": False, 
                "pbr": False
            }, 
            "model": {
                "texture": True,
                "pbr": False 
            }, 
            "pbr_model": {
                "texture": True, 
                "pbr": True, 
            }
        }
        data = {
            "type": "text_to_model",
            "model_version": task.model_version, 
            "prompt": task.prompt, 
            **output_type_mapping[task.output.type]
        }
        try:
            # raise RuntimeError("test error")
            response = requests.post(
                url, 
                headers=headers, 
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "code": -1,
                "message": f"There is something wrong on the local machine to request a connection to {url}. This is the error string value: {str(e)}", 
                "suggestion": "Please try to do it again or contact to admin of this blender addon"
            }
        
    
    async def _watch_task(self, task, api_key):
        url = f"{self.ws_base_url}/task/watch/{task.id}"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        try:
            # raise RuntimeError("Test Error")
            import websockets
            async with websockets.connect(url, extra_headers=headers) as websocket:
                data = None
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    result = data["data"]
                    task.watch_progress = f'{result["status"]}: {result["progress"]}%'
                    print(f"Result of watching task {task.id}: \nWatch Progress: {task.watch_progress}")
                    if data["event"] == "finalized":
                        if result["status"] != "success":
                            return {
                                "code": -2, 
                                "message": _("Something wrong on the task. The finalized status of this task is: ", '*') + result['status'], 
                                "suggestion": _("Try to do it again or contact the admin of this blender addon.", '*')
                            }
                        break
                data["code"] = 0
                return data
        except websockets.exceptions.ConnectionClosed as e:
            return {
                "code": -1, 
                "message": "Something wrong on the local machine. Code: " + str(e.code) + "Reason: " + e.reason, 
                "suggestion": "Try to do it again or contact the admin of this blender addon."
            }
        except Exception as e:
            return {
                "code": -1, 
                "message": _("Something wrong on the local machine: ", '*') + str(e), 
                "suggestion": _("Try to do it again or contact the admin of this blender addon.", '*')
            }

    def _get_task_output_url(self, task, api_key):
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        url = f"{self.http_base_url}/task/{task.id}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result
        except Exception as e:
            return {
                "code": -1,
                "message": f"There is an unexpected error: {e}",
                "suggestion": "Bring the code and message and contact the admin of the blender addon"
            }

    def _download_model(self, task, api_key):
        type = task.output.type
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        get_url_result = self._get_task_output_url(task, api_key)
        if get_url_result["code"] == 0:
            url = get_url_result["data"]["output"][type]
            local_filepath = os.path.join(self.output_folder, f"{task.id}_{type}.{get_url_result['data']['result'][type]['type']}")
            try:
                # raise RuntimeError("Test Error")
                progress = 0
                with requests.get(url, stream=True, headers=headers) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    with open(local_filepath, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
                                progress += len(chunk)
                                progress_percentage = round((progress / total_size) * 100, 2)
                                setattr(task.output, f"{type}_download_progress", f"{progress_percentage}%")
                    return {
                        "code": 0, 
                        "data": {
                            f"{type}_local_filepath": local_filepath
                        }
                    }
            except Exception as e:
                return {
                    "code": -1, 
                    "message": f"An unexpected error occurred: {str(e)}", 
                    "suggestion": "Bring the code and message and contact the admin of the blender addon"
                }
        else:
            return get_url_result


    def text23d(self, task, api_key, operator):
        create_task_result = self._create_txt23d_task(task, api_key)
        if create_task_result["code"] != 0:
            task.create_status = "creating_failed"
            self._report_message(create_task_result, operator)
            operator.end_token = True
        else:
            task.create_status = "creating_end"
            task.id = create_task_result["data"]["task_id"]
            task.watch_status = "watching"
            result_watch = asyncio.run(self._watch_task(task , api_key))
            if result_watch["code"] != 0:
                task.watch_status = "watching_failed"
                self._report_message(result_watch, operator)
                operator.end_token = True
            else:
                task.watch_status = "watching_end"

                # download model
                setattr(task.output, f"{task.output.type}_download_status", "downloading")
                download_result = self._download_model(task, api_key=api_key)
                if download_result["code"] == 0:
                    setattr(task.output, f"{task.output.type}_download_status", "downloading_end")
                    setattr(task.output, f"{task.output.type}_local_filepath", download_result["data"][f"{task.output.type}_local_filepath"])
                else:
                    setattr(task.output, f"{task.output.type}_download_status", "downloading_failed")
                    self._report_message(download_result, operator)
                operator.end_token = True

    def rewatch_txt23d_task(self, task, api_key, operator):
        task.watch_status = "watching"
        result_watch = asyncio.run(self._watch_task(task , api_key))
        if result_watch["code"] != 0:
            task.watch_status = "watching_failed"
            self._report_message(result_watch, operator)
            operator.end_token = True
        else:
            task.watch_status = "watching_end"

            # download model
            setattr(task.output, f"{task.output.type}_download_status", "downloading")
            download_result = self._download_model(task, api_key=api_key)
            if download_result["code"] == 0:
                setattr(task.output, f"{task.output.type}_download_status", "downloading_end")
                setattr(task.output, f"{task.output.type}_local_filepath", download_result["data"][f"{task.output.type}_local_filepath"])
            else:
                setattr(task.output, f"{task.output.type}_download_status", "downloading_failed")
                self._report_message(download_result, operator)
            operator.end_token = True

    def redownload_txt23d_task(self, task, api_key, operator):
        setattr(task.output, f"{task.output.type}_download_status", "downloading")
        download_result = self._download_model(task, api_key=api_key)
        if download_result["code"] == 0:
            setattr(task.output, f"{task.output.type}_download_status", "downloading_end")
            setattr(task.output, f"{task.output.type}_local_filepath", download_result["data"][f"{task.output.type}_local_filepath"])
        else:
            setattr(task.output, f"{task.output.type}_download_status", "downloading_failed")
            self._report_message(download_result, operator)
        operator.end_token = True

    def _upload_image(self, image_path, type, api_key):
        url = f"{self.http_base_url}/upload"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        try:
            # raise RuntimeError("Test Error")
            with open(image_path, 'rb') as f:
                files = {'file': (image_path, f, f'image/{type}')}
                response = requests.post(url, headers=headers, files=files)
                response.raise_for_status()
                result = response.json()
                return result
        except Exception as e:
            return {
                "code": -1, 
                "message": f"There is something wrong on the local machine: {str(e)}", 
                "suggestion": f"Bring the code and message and contact the admin of this blender addon"
            }

    def _report_message(self, result, operator):
        if result.get("code") != 0:
            operator.report(
                {"ERROR"}, 
                _("Error code: ", '*') + str(result['code']) +
                _("Error message: ", '*') + result["message"] + 
                _("Suggestion: ", '*') + result["suggestion"]
            )

    def _create_img23d_task(self, task, api_key):
        url = f"{self.http_base_url}/task"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        output_type_mapping = {
            "base_model": {
                "texture": False, 
                "pbr": False
            }, 
            "model": {
                "texture": True,
                "pbr": False 
            }, 
            "pbr_model": {
                "texture": True, 
                "pbr": True, 
            }
        }
        data = {
            "type": "image_to_model",
            "model_version": task.model_version, 
            "file": {
                "type": task.image.type, 
                "file_token": task.image.token
            }, 
            **output_type_mapping[task.output.type]
        }
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "code": -1,
                "message": f"There is something wrong on the local machine to request a connection to {url}. This is the error string value: {str(e)}", 
                "suggestion": "Please try to do it again or contact to admin of this blender addon"
            }

    def image23d(self, task, api_key, operator):
        task.image.upload_status = "uploading"
        upload_image_result = self._upload_image(task.image.local_filepath, task.image.type, api_key)
        if upload_image_result["code"] != 0:
            task.image.upload_status = "uploading_failed"
            self._report_message(upload_image_result, operator)
            operator.end_token = True
        else:
            task.image.upload_status = "uploading_end"
            task.image.token = upload_image_result["data"]["image_token"]
            task.create_status = "creating"
            task_create_result = self._create_img23d_task(task, api_key)
            if task_create_result["code"] != 0:
                task.create_status = "creating_failed"
                self._report_message(task_create_result, operator)
                operator.end_token = True
            else:
                task.create_status = "creating_end"
                task.id = task_create_result["data"]["task_id"]
                task.watch_status = "watching"
                watch_task_result = asyncio.run(self._watch_task(task, api_key))
                if watch_task_result["code"] != 0:
                    task.watch_status = "watching_failed"
                    self._report_message(watch_task_result, operator)
                    operator.end_token = True
                else:
                    task.watch_status = "watching_end"
                    
                    # download model
                    setattr(task.output, f"{task.output.type}_download_status", "downloading")
                    download_result = self._download_model(task, api_key=api_key)
                    if download_result["code"] == 0:
                        setattr(task.output, f"{task.output.type}_download_status", "downloading_end")
                        setattr(task.output, f"{task.output.type}_local_filepath", download_result["data"][f"{task.output.type}_local_filepath"])
                    else:
                        setattr(task.output, f"{task.output.type}_download_status", "downloading_failed")
                        self._report_message(download_result, operator)
                    operator.end_token = True

                    
    def rewatch_img23d_task(self, task, api_key, operator):
        task.watch_status = "watching"
        watch_task_result = asyncio.run(self._watch_task(task, api_key))
        if watch_task_result["code"] != 0:
            task.watch_status = "watching_failed"
            self._report_message(watch_task_result, operator)
            operator.end_token = True
        else:
            task.watch_status = "watching_end"
            
            # download model
            setattr(task.output, f"{task.output.type}_download_status", "downloading")
            download_result = self._download_model(task, api_key=api_key)
            if download_result["code"] == 0:
                setattr(task.output, f"{task.output.type}_download_status", "downloading_end")
                setattr(task.output, f"{task.output.type}_local_filepath", download_result["data"][f"{task.output.type}_local_filepath"])
            else:
                setattr(task.output, f"{task.output.type}_download_status", "downloading_failed")
                self._report_message(download_result, operator)
            operator.end_token = True


    def redownload_img23d_task(self, task, api_key, operator):
        setattr(task.output, f"{task.output.type}_download_status", "downloading")
        download_result = self._download_model(task, api_key=api_key)
        if download_result["code"] == 0:
            setattr(task.output, f"{task.output.type}_download_status", "downloading_end")
            setattr(task.output, f"{task.output.type}_local_filepath", download_result["data"][f"{task.output.type}_local_filepath"])
        else:
            setattr(task.output, f"{task.output.type}_download_status", "downloading_failed")
            self._report_message(download_result, operator)
        operator.end_token = True




