import logging
import os
import uuid
from fastapi import APIRouter, Body, Path, UploadFile, File, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from typing import Annotated
from .models import *
from .utils import absolute_path, UPLOADS_IMAGE_DIR, OUTPUTS_DIR
from .trellis_generator import TrellisGenerator
import asyncio

logger = logging.getLogger("trellis")


router = APIRouter()

@router.get("/check_server_status")
async def check_server_status():
    return {
        "code": 0, 
        "data": {
            "status": "ok"
        }
    }

@router.get("/get_queue_size")
async def get_queue_size():
    try:
        trellis_generator = TrellisGenerator.instance()
        queue_size = trellis_generator.queue_size
        return {
            "code": 0, 
            "data": {
                "queue_size": queue_size
            }
        }
    except Exception as e:
        return {
            "code": 100, 
            "message": f"There is a problem when query the queue size: {e}", 
            "suggestion": "Try do it again or contact the admin of this blender addon"
        }
    

@router.post("/upload_image")
async def upload_image(
    image: Annotated[
        UploadFile,
        File()
    ]
):
    image_extension = image.filename.split(".")[-1]
    if image_extension not in ["png", "jpeg"]:
        return {
            "code": 100, 
            "message": "Only support PNG and JPEG format of image.", 
            "suggestion": "Please convert the image to png or jpeg format."
        }
    else:
        try:
            image_token = uuid.uuid4().hex
            image_path = os.path.normpath(f"{UPLOADS_IMAGE_DIR}/{image_token}.{image_extension}")
            with open(image_path, "wb") as buffer:
                buffer.write(await image.read())
            logger.info(f"Save image to {image_path}")
            return {
                "code": 0, 
                "data": {
                    "image_token": image_token
                }
            }
        except Exception as e:
            logger.warning(f"Error when saving image to uploads/images/{image_token}.{image_extension}: {e}")
            return {
                "code": 200, 
                "message": f"There is a problem when saving the image to {image_path}: {e}", 
                "suggestion": "Try upload it again or contact the admin of this blender addon"
            }
        


@router.post("/img23d_task")
async def create_img_23d_task(
    task_in: Annotated[
        Img23DTaskIn, 
        Body(), 
    ]
):  
    referred_image_path = os.path.normpath(f"{UPLOADS_IMAGE_DIR}/{task_in.image_token}.{task_in.image_type}")
    if not os.path.exists(referred_image_path):
        return {
            "code": 100, 
            "message": f"The received image specified by token and type {task_in.image_token}.{task_in.image_type} is not stored in server.", 
            "suggestion": "Try to upload the image again or send me the correct image token and type."
        }
    trellis_generator = TrellisGenerator.instance()
    try:
        tid = uuid.uuid4().hex
        task = Img23DTask(
            **task_in.model_dump(), 
            tid=tid
        )
        trellis_generator.sqlite_img23d_task.create_item(task)
        trellis_generator.create_img23d_task(task)
        trellis_generator.sqlite_img23d_task.update_item(task)
        return {
            "code": 0, 
            "data": {
                "task_id": tid
            }
        }
    except Exception as e:
        return {
            "code": 200, 
            "message": f"There is a problem when creating task: {e}", 
            "suggestion": "Try upload it again or contact the admin of this blender addon"
        }

@router.get("/img23d_task/{tid}")
async def get_img23d_task_info(
    tid: Annotated[
        str, 
        Path()
    ]
) -> Img23DTask | dict:
    try:
        trellis_generator = TrellisGenerator.instance()
        task = trellis_generator.sqlite_img23d_task.read_item(tid)
        if task is None:
            return {
                "code": 100, 
                "message": "The task id is not in our server.", 
                "suggestion": "Try to create a new image to 3d task and pass us a correct task id."
            }
        else:
            return {
                "code": 0,
                "data": task.model_dump()
            }
    except Exception as e:
        return {
            "code": 200, 
            "message": f"An unexpect error occurred in our server: {e}", 
            "suggestion": "Try to do it again or contact the admin of blender addon."
        }
    
@router.get("/download")
async def download_file(
    extension: Annotated[
        Literal["glb", "ply"], 
        Query()
    ], 
    token: Annotated[
        str, 
        Query()
    ]
):
    try:
        filepath = os.path.normpath(f"{OUTPUTS_DIR}/{token}.{extension}")
        if not os.path.exists(filepath):
            return {
                "code": 100, 
                "message": f"The file you request via {token}.{extension} doesn't exist.", 
                "suggestion": "Try to request a correct file."
            }
        else:
            return FileResponse(filepath)
    except Exception as e:
        return {
            "code": 200, 
            "message": f"An unexpect error occurred in our server: {e}", 
            "suggestion": "Try to do it again or contact the admin of blender addon."
        }



@router.websocket("/img23d_task/watch/{tid}")
async def get_img23d_task_ws(
    websocket: WebSocket, 
    tid: Annotated[
        str, 
        Path(), 
    ]
):
    trellis_generator = TrellisGenerator.instance()
    task = trellis_generator.sqlite_img23d_task.read_item(tid)
    if task is None:
        await websocket.close(code=1008, reason="The task id is not in our server.")
        return 
    await websocket.accept()
    try:
        while True:
            task = trellis_generator.sqlite_img23d_task.read_item(tid)
            ret = {
                "event": "update" if task.generate_status in ["queued", "generating"] else "finalized", 
                "data": task.model_dump()
            }
            await websocket.send_json(ret)
            if ret["event"] == "finalized":
                break
            else:
                await asyncio.sleep(0.5)
    except WebSocketDisconnect as e:
        logger.info("Client Disconnected")