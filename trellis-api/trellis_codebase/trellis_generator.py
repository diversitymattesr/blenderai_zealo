from .utils import *
import os
import queue
import threading
from .trellis.pipelines import TrellisImageTo3DPipeline
import torch
import logging
from .models import SqliteImg23dTask
from PIL import Image
from pathlib import Path
import shutil

logger = logging.getLogger("trellis")


class TrellisGenerator:

    _instance = None

    @classmethod
    def instance(cls, device="dynamic", precision="float16"):
        if cls._instance is None:
            cls._instance = cls(device, precision)
        return cls._instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TrellisGenerator, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, device="dynamic", precision="float16"):
        if self.initialized:
            return 
        self._initial_db()
        self.img23d_pipeline = self._initial_img23d_pipeline(device, precision)
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        logger.info("Open a new thread for Trellis generator...")
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        self.initialized = True
        
    def _initial_db(self):
        self._empty_folder(DB_DIR)
        self.sqlite_img23d_task = SqliteImg23dTask.instance()
        self.sqlite_img23d_task.create_table()
        self._empty_folder(UPLOADS_IMAGE_DIR)
        self._empty_folder(OUTPUTS_DIR)

        # Ensure every time the trellis generator startup, it would get optimized vram usage
        torch.cuda.empty_cache()

    def _initial_img23d_pipeline(self, device="dynamic", precision="float16"):
        img23d_pipeline = TrellisImageTo3DPipeline.from_pretrained(TRELLIS_IMAGE_LARGE_REPO_DIR)
        if device == "cuda":
            img23d_pipeline.cuda()
        if precision == "float32":
            img23d_pipeline.to(torch.float32)
        if precision == "float16":
            img23d_pipeline.to(torch.float16)
            if "image_cond_model" in img23d_pipeline.models:
                img23d_pipeline.models['image_cond_model'].half() 
        img23d_pipeline.device_mode = device
        img23d_pipeline.precision_mode = precision
        return img23d_pipeline
    
    def _worker(self):
        """Worker thread that processes operations sequentially."""
        while True:
            operation, args, kwargs = self.queue.get()  # Wait for an operation
            try:
                task = kwargs.get("task")
                with self.lock:
                    operation(*args, **kwargs)  # Perform the operation
                self.queue.task_done()  # Mark the task as done
            except Exception as e:
                task.generate_status = "generating_failed"
                task.generate_failed_message = f"Generation failed because error happened: {e}"
                self.sqlite_img23d_task.update_item(task)
                continue
    
    def _enqueue_operation(self, operation, *args, **kwargs):
        """Enqueue an operation to be processed by the worker thread."""
        self.queue.put((operation, args, kwargs))

    @property
    def queue_size(self):
        return self.queue.qsize

    def create_img23d_task(self, task):
        try:
            task.create_status = "creating"
            image_path = os.path.normpath(os.path.join(UPLOADS_IMAGE_DIR, f"{task.image_token}.{task.image_type}"))
            image = Image.open(image_path).convert("RGBA")
            def run_img23d_task_operation(task):
                result = self.img23d_pipeline.run(
                    image=image, 
                    task=task,
                )
            self._enqueue_operation(run_img23d_task_operation, task=task)
            task.generate_status = "queued"
            task.create_status = "creating_end"
        except Exception as e:
            task.create_status = "creating_failed"
            raise e
        
    def _empty_folder(self, folder_path: str):
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
                        print(f"Error removing {item}: {e}")
                return
            else:
                return 
        else:
            return 

    def close(self):
        """Wait for all operations to complete and stop the worker thread."""
        self.queue.join()
        self.sqlite_img23d_task.drop_table()
        self._empty_folder(UPLOADS_IMAGE_DIR)
        self._empty_folder(OUTPUTS_DIR)
        
    
