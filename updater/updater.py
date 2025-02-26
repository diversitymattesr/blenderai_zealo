import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import zipfile
from bpy.app.translations import pgettext as _
import traceback
import requests
from typing import Any, Literal, TYPE_CHECKING
from ..property_groups import UpdaterProperties
from ..utils import absolute_path, ADDON_NAME


class GithubEngine:

    user = "diversitymattesr"
    repo = "blenderai_zealo"
    RELEASE_ASSET_NAME = "release.zip"

    _instance = None

    @classmethod
    def instance(cls):
        return cls()

    # make sure there is only one generator instance
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(GithubEngine, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
        
        self.initialized = True

    def _query_all_releases(self) -> dict[str, Any]:
        url = f"https://api.github.com/repos/{self.user}/{self.repo}/releases"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            result = response.json()  # Parse the JSON response
            if result:
                return {
                    "code": 0, 
                    "data": result
                }
            else:
                print(f"No releases published yet")
                return {
                    "code": 200, 
                    "error_message": _("No releases published yet: ", '*'), 
                    "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
                } 
        except Exception as e:
            print(f"An error occurred when query all releases")
            print(traceback.format_exc())
            return {
                "code": 100, 
                "error_message": _("An error occurred when query all releases: ", '*') + str(e), 
                "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
            }
    
    def check_new_version_available(
        self, 
        current_version: tuple[int], 
    ) -> dict[str, Any]:
        query_all_releases_result = self._query_all_releases()
        if query_all_releases_result.get("code") != 0:
            return query_all_releases_result
        else:
            try:
                all_releases = query_all_releases_result.get("data")
                latest_releases = all_releases[0]
                latest_releases_version = tuple([int(comp) for comp in latest_releases.get("name")[1:].split(".")])
                if latest_releases_version > current_version:
                    return {
                        "code": 0, 
                        "data": {
                            "new_version_available": True, 
                            "new_version": list(latest_releases_version)
                        }
                    }
                else:
                    return {
                        "code": 0, 
                        "data": {
                            "new_version_available": False, 
                            "new_version": None
                        }
                    }
            except Exception as e:
                print(f"An error occurred when parse new release available")
                print(traceback.format_exc())
                return {
                    "code": 200, 
                    "error_message": _("An unexpected error occurred when check if there is new release available: ", '*') + str(e), 
                    "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
                }
    
    def _get_release_asset_url_from_all_releases(self, update_to_release_name, all_releases):
        try:
            filtered_releases = [release for release in all_releases if release.get("name") == update_to_release_name]
            if not filtered_releases:
                return {
                    "code": 300, 
                    "error_message": _("No release from all releases named: ", '*') + update_to_release_name, 
                    "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
                }
            else:
                release = filtered_releases[0]
                assets = release.get("assets")
                filtered_assets = [asset for asset in assets if asset.get("name") == self.RELEASE_ASSET_NAME]
                if not filtered_assets:
                    return {
                        "code": 400, 
                        "error_message": _("No release asset from all assets named: ", '*') + self.RELEASE_ASSET_NAME, 
                        "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
                    }
                else:
                    asset = filtered_assets[0]
                    return {
                        "code": 0, 
                        "data": {
                            "url": asset.get("browser_download_url"), 
                            "filename": self.RELEASE_ASSET_NAME, 
                        }
                    }
        except Exception as e:
            return {
                "code": 500, 
                "error_message": _("An unexpected error occurred when get latest release asset: ", '*') + str(e), 
                "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
            }



class GiteeEngine:

    _instance = None

    @classmethod
    def instance(cls):
        return cls()

    # make sure there is only one generator instance
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(GithubEngine, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
        
        self.initialized = True

    def check_new_version_available(
        self, 
        current_version: tuple[int]
    ) -> dict[str, Any]:
        pass

class BlenderAIUpdater:

    _instance = None

    CURRENT_VERSION = (1, 0, 0)

    @classmethod
    def instance(cls):
        return cls()

    # make sure there is only one generator instance
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(BlenderAIUpdater, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
        
        self.initialized = True

    def _get_engine(
        self, 
        engine_str: Literal["github", "gitee"]
    ) -> GithubEngine | GiteeEngine:
        if engine_str == "github":
            return GithubEngine.instance()
        if engine_str == "gitee":
            return GiteeEngine.instance()

    def check_update(
        self, 
        operator, 
        engine_str: str, 
        updater_props: UpdaterProperties
    ):
        updater_props.check_update_status = "checking"
        updater_props.update_to_release_name = ""
        updater_props.check_update_message = _("Checking update", '*')
        engine = self._get_engine(engine_str=engine_str)
        check_result = engine.check_new_version_available(self.CURRENT_VERSION)
        if check_result.get("code") != 0:
            updater_props.check_update_status = "checking_failed"
            updater_props.check_update_message = check_result.get("error_message")
            operator.end_token = True
        else:
            data = check_result.get("data")
            updater_props.check_update_status = "checking_end"
            if data.get("new_version_available"):
                updater_props.update_to_release_name = f'v{".".join([str(comp) for comp in data.get("new_version")])}'
                updater_props.check_update_message = "Detect new release: " + f"v{'.'.join([str(comp) for comp in data.get('new_version')])}"
            else:
                updater_props.check_update_message = _("This is the latest version: ", '*') + f"v{'.'.join([str(comp) for comp in self.CURRENT_VERSION])}"
            operator.end_token = True
    
    
    def _empty_folder(self, folder_path: str):
        success_result = {
            "code": 0
        }
        folder = Path(folder_path)
        if folder.exists() and folder.is_dir():
            # Check if directory has any content
            if any(folder.iterdir()):
                for item in folder.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink()  # Remove file/symlink
                        elif item.is_dir():
                            shutil.rmtree(item)  # Remove directory recursively
                    except Exception as e:
                        print(f"Error removing {item}")
                        print(traceback.format_exc())
                        return {
                            "code": 600, 
                            "error_message": _("Error occurred when delete the existing legacy tmp latest release folder", '*'), 
                            "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
                        }
                return success_result
            else:
                return success_result
        else:
            return success_result

    def _download_release_zip(self, url, path, updater_props):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0)) // 1024 ** 2
                print(f"File size: {total_size}Mb")
                updater_props.download_release_message = _("Downloading Release: ", '*') + f"{total_size}Mb"
                with open(path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                updater_props.download_release_message = _("Release Downloaded", '*')
                return {
                    "code": 0
                }
        except Exception as e:
            print(f"Error downloading release file to {path}")
            print(traceback.format_exc())
            return {
                "code": 700, 
                "error_message": _("Error downloading release file: ", '*') + str(e), 
                "suggestion": _("Open the blender console to self check or bring the error message to blender addon admin.", '*')
            }

    def _get_cmd_encoding(self):
        # Get active console code page
        code_page = ctypes.windll.kernel32.GetConsoleOutputCP()
        # Handle UTF-8 special case
        return "utf-8" if code_page == 65001 else f"cp{code_page}"

    def _complete_tmp_release_folder(self, release_tmp_folder, release_zip_path, updater_props):
        try:
            updater_props.download_release_message = _("Unarchive release zip to tmp folder...", '*')
            with zipfile.ZipFile(release_zip_path, 'r') as zip_ref:
                zip_ref.extractall(release_tmp_folder)
            post_release_download_script_path = os.path.normpath(os.path.join(release_tmp_folder, "updater/post_release_download_script.py"))
            RED = '\033[91m'
            GREEN = '\033[32m'
            RESET = '\033[0m' 
            updater_props.download_release_message = _("Call post release download script...", '*')
            def print_stdout(pipe):
                try:
                    for line in iter(pipe.readline, ''):
                        try:
                            line = line.strip()
                            print(f"{GREEN}[Post Script Stdout] {line}{RESET}")
                        except Exception as e:
                            print(f"{RED}[Post Script Stdout] Pipe stdout readline failed since error:\n{traceback.format_exc()}{RESET}")
                            continue
                except Exception as e:
                    print(f"{RED}[Post Script Stdout] Stdout Terminated since error:\n{traceback.format_exc()}{RESET}")
                finally:
                    print(f"{RED}[Post Script Stdout] Stdout Pipeline Terminated{RESET}")

            def print_stderr(pipe):
                try:
                    for line in iter(pipe.readline, ''):
                        try:
                            line = line.strip()
                            print(f"{RED}[Post Script Stderr] {line}{RESET}")
                        except Exception as e:
                            print(f"{RED}[Post Script Stderr] Pipe readline failed since error:\n{traceback.format_exc()}{RESET}")
                            continue
                except Exception as e:
                    print(f"{RED}[Post Script Stderr] Stderr terminated since error:\n{traceback.format_exc()}{RESET}")
                finally:
                    print(f"{RED}[Post Script Stderr] Stderr Pipeline Terminated{RESET}")
                
            with subprocess.Popen(
                f'"{sys.executable}" "{post_release_download_script_path}" & exit /b %ERRORLEVEL%', 
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
                    updater_props.download_release_message = _("Call of post release download script exited with error", '*')
                    return {
                        "code": 800, 
                        "error_message": _("Call of post release download script exited with error", '*'), 
                        "suggestion": _("Bring the code and message and contact the admin of this blender addon", '*')
                    }
                else:
                    updater_props.download_release_message = _("Call of post release download script exited normally", '*')
                    return {
                        "code": 0,
                    }
        except Exception as e:
            updater_props.download_release_message = _("Call of post release download script with unexpected error", '*')
            return {
                "code": 900, 
                "error_message": _("Call of post release download script exited with an unexpected error", '*'), 
                "suggestion": _("Bring the code and message and contact the admin of this blender addon", '*')
            }
        finally:
            stderr_thread.join()
            stdout_thread.join()

    def download_release(self, operator, engine_str, update_to_release_name, updater_props):
        updater_props.download_release_status = "downloading"
        updater_props.download_release_message = _("Query latest release information...", '*')
        updater_props.downloaded_release_name = ""
        engine = self._get_engine(engine_str)
        query_all_releases_result = engine._query_all_releases()
        if query_all_releases_result.get("code") != 0:
            updater_props.download_release_status = "downloading_failed"
            updater_props.download_release_message = query_all_releases_result.get("error_message")
            operator.end_token = True
            return 
        else:
            all_releases = query_all_releases_result.get("data")
            get_release_asset_url_result = engine._get_release_asset_url_from_all_releases(update_to_release_name, all_releases)
            if get_release_asset_url_result.get("code") != 0:
                updater_props.download_release_status = "downloading_failed"
                updater_props.download_release_message = get_release_asset_url_result.get("error_message")
                operator.end_token = True
                return 
            else:
                release_asset_url = get_release_asset_url_result.get("data").get("url")
                release_asset_filename = get_release_asset_url_result.get("data").get("filename")
                release_tmp_folder = absolute_path(f"./../{ADDON_NAME}_{update_to_release_name}")
                if os.path.exists(release_tmp_folder):
                    empty_release_tmp_folder_result = self._empty_folder(release_tmp_folder)
                    if empty_release_tmp_folder_result.get("code") != 0:
                        updater_props.download_release_status = "downloading_failed"
                        updater_props.download_release_message = empty_release_tmp_folder_result.get("error_message")
                        operator.end_token = True
                        return
                else:
                    os.mkdir(release_tmp_folder)
                release_zip_path = os.path.normpath(os.path.join(release_tmp_folder, release_asset_filename))
                download_release_zip_result = self._download_release_zip(release_asset_url, release_zip_path, updater_props)
                if download_release_zip_result.get("code") != 0:
                    updater_props.download_release_status = "downloading_failed"
                    updater_props.download_release_message = download_release_zip_result.get("error_message")
                    operator.end_token = True
                    return
                else:
                    complete_release_folder_result = self._complete_tmp_release_folder(release_tmp_folder, release_zip_path, updater_props)
                    if complete_release_folder_result.get("code") != 0:
                        updater_props.download_release_status = "downloading_failed"
                        updater_props.download_release_message = complete_release_folder_result.get("error_message")
                        operator.end_token = True
                        return
                    else:
                        updater_props.download_release_status = "downloading_end"
                        updater_props.download_release_message = _("The Release download succeeded: ", '*') + update_to_release_name
                        updater_props.downloaded_release_name = update_to_release_name
                        operator.end_token = True
                        return

