import gc
import os
from typing import * # type: ignore
from contextlib import contextmanager # type: ignore
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm
from easydict import EasyDict as edict
from torchvision import transforms
from PIL import Image
import rembg
from .base import Pipeline
from . import samplers
from ..modules import sparse as sp
from ..representations import Gaussian, Strivec, MeshExtractResult
from ...models import Img23DTask, SqliteImg23dTask
from ..utils import postprocessing_utils
from ...utils import absolute_path, DINOV2_FOLDER, DINOV2_PRETRAINED_MODEL_PATH, OUTPUTS_DIR
import traceback
import logging

logger = logging.getLogger("trellis")



class TrellisImageTo3DPipeline(Pipeline):
    """
    Pipeline for inferring Trellis image-to-3D models.

    Args:
        models (dict[str, nn.Module]): The models to use in the pipeline.
        sparse_structure_sampler (samplers.Sampler): The sampler for the sparse structure.
        slat_sampler (samplers.Sampler): The sampler for the structured latent.
        slat_normalization (dict): The normalization parameters for the structured latent.
        image_cond_model (str): The name of the image conditioning model.
    """
    def __init__(
        self,
        models: dict[str, nn.Module] = None,
        sparse_structure_sampler: samplers.Sampler = None,
        slat_sampler: samplers.Sampler = None,
        slat_normalization: dict = None,
        image_cond_model: str = None,
    ):
        if models is None:
            return
        super().__init__(models)
        self.sparse_structure_sampler = sparse_structure_sampler
        self.slat_sampler = slat_sampler
        self.sparse_structure_sampler_params = {}
        self.slat_sampler_params = {}
        self.slat_normalization = slat_normalization
        self.rembg_session = None
        self._init_image_cond_model(image_cond_model)

    @staticmethod
    def from_pretrained(path: str) -> "TrellisImageTo3DPipeline":
        """
        Load a pretrained model.

        Args:
            path (str): The path to the model. Can be either local path or a Hugging Face repository.
        """
        pipeline = super(TrellisImageTo3DPipeline, TrellisImageTo3DPipeline).from_pretrained(path)
        new_pipeline = TrellisImageTo3DPipeline()
        new_pipeline.__dict__ = pipeline.__dict__
        args = pipeline._pretrained_args

        new_pipeline.sparse_structure_sampler = getattr(samplers, args['sparse_structure_sampler']['name'])(**args['sparse_structure_sampler']['args'])
        new_pipeline.sparse_structure_sampler_params = args['sparse_structure_sampler']['params']

        new_pipeline.slat_sampler = getattr(samplers, args['slat_sampler']['name'])(**args['slat_sampler']['args'])
        new_pipeline.slat_sampler_params = args['slat_sampler']['params']

        new_pipeline.slat_normalization = args['slat_normalization']
        new_pipeline.rembg_session = rembg.new_session(
            model_name="birefnet-general-lite", 
            providers=["CPUExecutionProvider"]
        )
        new_pipeline._init_image_cond_model(args['image_cond_model'])
        return new_pipeline
    
    def _init_image_cond_model(self, name: str):
        """
        Initialize the image conditioning model.
        """
        dinov2_model = torch.hub.load(DINOV2_FOLDER, name, source="local", trust_repo=True, pretrained=False)
        dinov2_model.load_state_dict(torch.load(DINOV2_PRETRAINED_MODEL_PATH))
        dinov2_model.eval()
        self.models['image_cond_model'] = dinov2_model
        transform = transforms.Compose([
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.image_cond_model_transform = transform

    def preprocess_image(self, input: Image.Image) -> Image.Image:
        """
        Preprocess the input image.
        """
        # 1) Force max dimension 1024 BEFORE background removal
        if max(input.size) > 1024:
            scale = 1024 / max(input.size)
            new_w = int(input.width * scale)
            new_h = int(input.height * scale)
            input = input.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # if has alpha channel, use it directly; otherwise, remove background
        has_alpha = False
        if input.mode == 'RGBA':
            alpha = np.array(input)[:, :, 3]
            if not np.all(alpha == 255):
                has_alpha = True
        if has_alpha:
            output = input
        else:
            input = input.convert('RGB')
            # But we already clamped the size above, so no need to clamp here again
            output = rembg.remove(input, session=self.rembg_session)

        output_np = np.array(output)
        alpha = output_np[:, :, 3]
        bbox = np.argwhere(alpha > 0.8 * 255)
        bbox = np.min(bbox[:, 1]), np.min(bbox[:, 0]), np.max(bbox[:, 1]), np.max(bbox[:, 0])
        center = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
        size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        size = int(size * 1.2)
        bbox = center[0] - size // 2, center[1] - size // 2, center[0] + size // 2, center[1] + size // 2
        output = output.crop(bbox)  # type: ignore
        output = output.resize((518, 518), Image.Resampling.LANCZOS)
        output = np.array(output).astype(np.float32) / 255
        output = output[:, :, :3] * output[:, :, 3:4]
        output = Image.fromarray((output * 255).astype(np.uint8))
        return output

    @torch.no_grad()
    def encode_image(self, image: Union[torch.Tensor, list[Image.Image]]) -> torch.Tensor:
        """
        Encode the image.

        Args:
            image (Union[torch.Tensor, list[Image.Image]]): The image to encode

        Returns:
            torch.Tensor: The encoded features.
        """
        if isinstance(image, torch.Tensor):
            assert image.ndim == 4, "Image tensor should be batched (B, C, H, W)"
        elif isinstance(image, list):
            assert all(isinstance(i, Image.Image) for i in image), "Image list should be list of PIL images"
            image = [i.resize((518, 518), Image.LANCZOS) for i in image]
            image = [np.array(i.convert('RGB')).astype(np.float32) / 255 for i in image]
            desired_dtype = self.models['image_cond_model'].patch_embed.proj.weight.dtype #so it works with float16 or float32, etc.
            image = [torch.from_numpy(i).permute(2, 0, 1).to(desired_dtype) for i in image]
            image = torch.stack(image).to(self.device)
        else:
            raise ValueError(f"Unsupported type of image: {type(image)}")
        
        image = self.image_cond_model_transform(image).to(self.device)
        features = self.models['image_cond_model'](image, is_training=True)['x_prenorm']
        patchtokens = F.layer_norm(features, features.shape[-1:])
        return patchtokens
        
    def get_cond(self, image: Union[torch.Tensor, list[Image.Image]]) -> dict:
        """
        Get the conditioning information for the model.

        Args:
            image (Union[torch.Tensor, list[Image.Image]]): The image prompts.

        Returns:
            dict: The conditioning information
        """
        if self.device_mode == "dynamic":
            with MoveModelsToCuda(['image_cond_model'], self) as mm:
                cond = self.encode_image(image)
                neg_cond = torch.zeros_like(cond)
        else:
            cond = self.encode_image(image)
            neg_cond = torch.zeros_like(cond)
        return {
            'cond': cond,
            'neg_cond': neg_cond,
        }
    

    def sample_sparse_structure(
        self,
        cond: dict,
        num_samples: int = 1,
        sampler_params: dict = {},
    ) -> torch.Tensor:
        """
        Sample sparse structures with the given conditioning.
        
        Args:
            cond (dict): The conditioning information.
            num_samples (int): The number of samples to generate.
            sampler_params (dict): Additional parameters for the sampler.
        """
        # Sample occupancy latent
        if self.device_mode == "dynamic":
            with MoveModelsToCuda(model_names=['sparse_structure_flow_model', 'sparse_structure_decoder'], pipeline=self) as mm:
                flow_model = self.models['sparse_structure_flow_model']
                reso = flow_model.resolution
                desired_dtype = next(flow_model.parameters()).dtype #so that it workws with float16, float32, etc.
                noise = torch.randn(num_samples, flow_model.in_channels, reso, reso, reso, dtype=desired_dtype).to(self.device)
                sampler_params = {**self.sparse_structure_sampler_params, **sampler_params}
                z_s = self.sparse_structure_sampler.sample(
                    flow_model,
                    noise,
                    **cond,
                    **sampler_params,
                    verbose=True,
                ).samples
                
                # Decode occupancy latent
                decoder = self.models['sparse_structure_decoder']
                coords = torch.argwhere(decoder(z_s)>0)[:, [0, 2, 3, 4]].int()
                
                return coords
        else: 
            flow_model = self.models['sparse_structure_flow_model']
            reso = flow_model.resolution
            desired_dtype = next(flow_model.parameters()).dtype #so that it workws with float16, float32, etc.
            noise = torch.randn(num_samples, flow_model.in_channels, reso, reso, reso, dtype=desired_dtype).to(self.device)
            sampler_params = {**self.sparse_structure_sampler_params, **sampler_params}
            z_s = self.sparse_structure_sampler.sample(
                flow_model,
                noise,
                **cond,
                **sampler_params,
                verbose=True,
            ).samples
            
            # Decode occupancy latent
            decoder = self.models['sparse_structure_decoder']
            coords = torch.argwhere(decoder(z_s)>0)[:, [0, 2, 3, 4]].int()
            
            return coords
    
    def sample_slat(
        self,
        cond: dict,
        coords: torch.Tensor,
        sampler_params: dict = {},
    ) -> sp.SparseTensor:
        """
        Sample structured latent with the given conditioning.
        
        Args:
            cond (dict): The conditioning information.
            coords (torch.Tensor): The coordinates of the sparse structure.
            sampler_params (dict): Additional parameters for the sampler.
        """
        # Sample structured latent
        if self.device_mode == "dynamic":
            with MoveModelsToCuda(['slat_flow_model'], self) as mm:
                flow_model = self.models['slat_flow_model']
                desired_dtype = next(flow_model.parameters()).dtype #so that it workws with float16, float32, etc.
                noise = sp.SparseTensor(
                    feats=torch.randn(coords.shape[0], flow_model.in_channels, dtype=desired_dtype).to(self.device),
                    coords=coords,
                )
                sampler_params = {**self.slat_sampler_params, **sampler_params}
                slat = self.slat_sampler.sample(
                    flow_model,
                    noise,
                    **cond,
                    **sampler_params,
                    verbose=True
                ).samples

                std = torch.tensor(self.slat_normalization['std'])[None].to(slat.device)
                mean = torch.tensor(self.slat_normalization['mean'])[None].to(slat.device)
                slat = slat * std + mean
                return slat
        else:
            flow_model = self.models['slat_flow_model']
            desired_dtype = next(flow_model.parameters()).dtype #so that it workws with float16, float32, etc.
            noise = sp.SparseTensor(
                feats=torch.randn(coords.shape[0], flow_model.in_channels, dtype=desired_dtype).to(self.device),
                coords=coords,
            )
            sampler_params = {**self.slat_sampler_params, **sampler_params}
            slat = self.slat_sampler.sample(
                flow_model,
                noise,
                **cond,
                **sampler_params,
                verbose=True
            ).samples

            std = torch.tensor(self.slat_normalization['std'])[None].to(slat.device)
            mean = torch.tensor(self.slat_normalization['mean'])[None].to(slat.device)
            slat = slat * std + mean
            return slat

    
    def decode_slat(
        self,
        slat: sp.SparseTensor,
        formats: List[str] = ['mesh', 'gaussian', 'radiance_field'],
    ) -> dict:
        """
        Decode the structured latent.

        Args:
            slat (sp.SparseTensor): The structured latent.
            formats (List[str]): The formats to decode the structured latent to.

        Returns:
            dict: The decoded structured latent.
        """
        ret = {}

        if 'mesh' in formats:
            torch.cuda.synchronize() #important, to avoid Out Of Memory exceptions
            with torch.no_grad():
                if self.device_mode == "dynamic":
                    with MoveModelsToCuda(model_names=["slat_decoder_mesh"], pipeline=self) as mm:
                        ret['mesh'] = self.models['slat_decoder_mesh'](slat)
                        torch.cuda.synchronize() 
                else:
                    ret['mesh'] = self.models['slat_decoder_mesh'](slat)
                    torch.cuda.synchronize() 
        if 'gaussian' in formats:
            torch.cuda.synchronize() #important, to avoid OOM exceptions
            with torch.no_grad():
                if self.device_mode == "dynamic":
                    with MoveModelsToCuda(["slat_decoder_gs"], self) as mm:
                        ret['gaussian'] = self.models['slat_decoder_gs'](slat)
                        torch.cuda.synchronize()
                else:
                    ret['gaussian'] = self.models['slat_decoder_gs'](slat)
                    torch.cuda.synchronize()
        
        if 'radiance_field' in formats:
            torch.cuda.synchronize() #important, to avoid OOM exceptions
            with torch.no_grad():
                if self.device_mode == "dynamic":
                    with MoveModelsToCuda(["slat_decoder_rf"], self) as mm:
                        ret['radiance_field'] = self.models['slat_decoder_rf'](slat)
                        torch.cuda.synchronize()
                else:
                    ret['radiance_field'] = self.models['slat_decoder_rf'](slat)
                    torch.cuda.synchronize() 
        return ret
    
    
    @torch.no_grad()
    def run(
        self,
        image: Image.Image,
        task: Img23DTask, 
        num_samples: int = 1,
        seed: int = 42,
        sparse_structure_sampler_params: dict = {},
        slat_sampler_params: dict = {},
    ) -> dict:
        """
        Run the pipeline.

        Args:
            image (Image.Image): The image prompt.
            num_samples (int): The number of samples to generate.
            sparse_structure_sampler_params (dict): Additional parameters for the sparse structure sampler.
            slat_sampler_params (dict): Additional parameters for the structured latent sampler.
            preprocess_image (bool): Whether to preprocess the image.
        """
        try:
            from ...trellis_generator import TrellisGenerator
            trellis_generator = TrellisGenerator.instance()
            if task.output_type == "base_model":
                formats = ["mesh"]
            elif task.output_type == "model":
                formats = ["mesh", "gaussian"]
            preprocess_image = task.preprocess_image

            task.generate_status = "generating"
            trellis_generator.sqlite_img23d_task.update_item(task)
            
            if self.device_mode == "dynamic":
                with MoveModelsToCpu(list(self.models.keys()), pipeline=self) as mmc:
                    pass

            if preprocess_image:
                task.progress = 15
                trellis_generator.sqlite_img23d_task.update_item(task)
                image = self.preprocess_image(image)
            task.progress = 30
            trellis_generator.sqlite_img23d_task.update_item(task)
            cond = self.get_cond([image])
            task.progress = 45
            trellis_generator.sqlite_img23d_task.update_item(task) 

            torch.manual_seed(seed)

            coords = self.sample_sparse_structure(cond, num_samples, sparse_structure_sampler_params)
            task.progress = 65
            trellis_generator.sqlite_img23d_task.update_item(task)

            slat = self.sample_slat(cond, coords, slat_sampler_params)
            task.progress = 75
            trellis_generator.sqlite_img23d_task.update_item(task)

            decoded_slat = self.decode_slat(slat, formats)
            task.progress = 90
            trellis_generator.sqlite_img23d_task.update_item(task)
            with torch.enable_grad():
                if task.output_type == "base_model":
                    mesh = postprocessing_utils.to_glb(
                        mesh=decoded_slat["mesh"][0], 
                        get_base_model=True, 
                    )
                    glb_path = os.path.normpath(f"{OUTPUTS_DIR}/{task.tid}.glb")
                    mesh.export(glb_path)
                    task.output_url = f"/download?extension=glb&token={task.tid}"
                    task.progress = 100
                    task.generate_status = "generating_end"
                    trellis_generator.sqlite_img23d_task.update_item(task)
                if task.output_type == "model":
                    mesh = postprocessing_utils.to_glb(
                        mesh=decoded_slat["mesh"][0], 
                        get_base_model=False, 
                        app_rep=decoded_slat["gaussian"][0], 
                    )
                    glb_path = os.path.normpath(f"{OUTPUTS_DIR}/{task.tid}.glb")
                    mesh.export(glb_path)
                    task.output_url = f"/download?extension=glb&token={task.tid}"
                    task.progress = 100
                    task.generate_status = "generating_end"
                    trellis_generator.sqlite_img23d_task.update_item(task)
            gc.collect()
        except Exception as e:
            task.generate_status = "generating_failed"
            task.generate_failed_message = f"Generation failed because error happened: {e}"
            trellis_generator.sqlite_img23d_task.update_item(task)
            logger.error(traceback.format_exc())

    @contextmanager
    def inject_sampler_multi_image(
        self,
        sampler_name: str,
        num_images: int,
        num_steps: int,
        mode: Literal['stochastic', 'multidiffusion'] = 'stochastic',
    ):
        """
        Inject a sampler with multiple images as condition.
        
        Args:
            sampler_name (str): The name of the sampler to inject.
            num_images (int): The number of images to condition on.
            num_steps (int): The number of steps to run the sampler for.
        """
        sampler = getattr(self, sampler_name)
        setattr(sampler, f'_old_inference_model', sampler._inference_model)

        if mode == 'stochastic':
            if num_images > num_steps:
                print(f"\033[93mWarning: number of conditioning images is greater than number of steps for {sampler_name}. "
                    "This may lead to performance degradation.\033[0m")

            cond_indices = (np.arange(num_steps) % num_images).tolist()
            def _new_inference_model(self, model, x_t, t, cond, **kwargs):
                cond_idx = cond_indices.pop(0)
                cond_i = cond[cond_idx:cond_idx+1]
                return self._old_inference_model(model, x_t, t, cond=cond_i, **kwargs)
        
        elif mode =='multidiffusion':
            from .samplers import FlowEulerSampler
            def _new_inference_model(self, model, x_t, t, cond, neg_cond, cfg_strength, cfg_interval, **kwargs):
                if cfg_interval[0] <= t <= cfg_interval[1]:
                    preds = []
                    for i in range(len(cond)):
                        preds.append(FlowEulerSampler._inference_model(self, model, x_t, t, cond[i:i+1], **kwargs))
                    pred = sum(preds) / len(preds)
                    neg_pred = FlowEulerSampler._inference_model(self, model, x_t, t, neg_cond, **kwargs)
                    return (1 + cfg_strength) * pred - cfg_strength * neg_pred
                else:
                    preds = []
                    for i in range(len(cond)):
                        preds.append(FlowEulerSampler._inference_model(self, model, x_t, t, cond[i:i+1], **kwargs))
                    pred = sum(preds) / len(preds)
                    return pred
            
        else:
            raise ValueError(f"Unsupported mode: {mode}")
            
        sampler._inference_model = _new_inference_model.__get__(sampler, type(sampler))

        yield

        sampler._inference_model = sampler._old_inference_model
        delattr(sampler, f'_old_inference_model')

    @torch.no_grad()
    def run_multi_image(
        self,
        images: List[Image.Image],
        num_samples: int = 1,
        seed: int = 42,
        sparse_structure_sampler_params: dict = {},
        slat_sampler_params: dict = {},
        formats: List[str] = ['mesh', 'gaussian', 'radiance_field'],
        preprocess_image: bool = True,
        mode: Literal['stochastic', 'multidiffusion'] = 'stochastic',
    ) -> dict:
        """
        Run the pipeline with multiple images as condition

        Args:
            images (List[Image.Image]): The multi-view images of the assets
            num_samples (int): The number of samples to generate.
            sparse_structure_sampler_params (dict): Additional parameters for the sparse structure sampler.
            slat_sampler_params (dict): Additional parameters for the structured latent sampler.
            preprocess_image (bool): Whether to preprocess the image.
        """
        if preprocess_image:
            images = [self.preprocess_image(image) for image in images]
        cond = self.get_cond(images)
        cond['neg_cond'] = cond['neg_cond'][:1]
        torch.manual_seed(seed)
        ss_steps = {**self.sparse_structure_sampler_params, **sparse_structure_sampler_params}.get('steps')
        with self.inject_sampler_multi_image('sparse_structure_sampler', len(images), ss_steps, mode=mode):
            coords = self.sample_sparse_structure(cond, num_samples, sparse_structure_sampler_params)
        slat_steps = {**self.slat_sampler_params, **slat_sampler_params}.get('steps')
        with self.inject_sampler_multi_image('slat_sampler', len(images), slat_steps, mode=mode):
            slat = self.sample_slat(cond, coords, slat_sampler_params)
        return self.decode_slat(slat, formats)
    
    



class MoveModelsToCuda:

    def __init__(self, model_names: list[str], pipeline: TrellisImageTo3DPipeline):
        self.model_names = model_names
        self.pipeline = pipeline

    def __enter__(self):
        for name in self.model_names:
            current_device = next(self.pipeline.models[name].parameters()).device #works for DinoVision, who doesn't have 'self.device'
            target_device = torch.device("cuda")
            # Only move if current device is different from target device
            if current_device != target_device:
                self.pipeline.models[name].to(target_device)
        logger.debug(f"Move models {self.model_names} to cuda")

    def __exit__(self, exc_type, exc_value, traceback):
        for name in self.model_names:
            current_device = next(self.pipeline.models[name].parameters()).device #works for DinoVision, who doesn't have 'self.device'
            target_device = torch.device("cpu")
            # Only move if current device is different from target device
            if current_device != target_device:
                self.pipeline.models[name].to(target_device)
        torch.cuda.empty_cache()
        logger.debug(f"Move models {self.model_names} to cpu")
    
class MoveModelsToCpu:

    def __init__(self, model_names: list[str], pipeline: TrellisImageTo3DPipeline):
        self.model_names = model_names
        self.pipeline = pipeline

    def __enter__(self):
        for name in self.model_names:
            current_device = next(self.pipeline.models[name].parameters()).device #works for DinoVision, who doesn't have 'self.device'
            target_device = torch.device("cpu")
            # Only move if current device is different from target device
            if current_device != target_device:
                self.pipeline.models[name].to(target_device)

    def __exit__(self, exc_type, exc_value, traceback):
        logger.debug(f"Move models {self.model_names} to cpu")