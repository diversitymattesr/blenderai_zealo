import os

ROOT_DIR = os.path.normpath(os.path.dirname(os.path.dirname(__file__)))

ADDON_DIR = os.path.normpath(os.path.dirname(ROOT_DIR))

def absolute_path(subpath):
    return os.path.normpath(os.path.join(ROOT_DIR, subpath))

def absolute_path_based_on_addon(subpath):
    return os.path.normpath(os.path.join(ADDON_DIR, subpath))


TRELLIS_IMAGE_LARGE_REPO_DIR = absolute_path_based_on_addon("venv/trellis-api/TRELLIS-image-large")
REMBG_MODEL_FOLDER = absolute_path_based_on_addon("venv/trellis-api/rembg")
DINOV2_FOLDER = absolute_path_based_on_addon("venv/trellis-api/facebookresearch_dinov2")
DINOV2_PRETRAINED_MODEL_PATH = absolute_path_based_on_addon("venv/trellis-api/facebookresearch_dinov2/checkpoints/dinov2_vitl14_reg4_pretrain.pth")


UPLOADS_IMAGE_DIR = absolute_path_based_on_addon("user_data/trellis-api/uploads/images")
os.makedirs(UPLOADS_IMAGE_DIR, exist_ok=True)
OUTPUTS_DIR = absolute_path_based_on_addon("user_data/trellis-api/outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
DB_DIR = absolute_path_based_on_addon("user_data/trellis-api/db")
os.makedirs(DB_DIR, exist_ok=True)
