"""Hugging Face Inference Endpoint custom handler (task=custom, GPU >= 24GB e.g. A10G).
Expects the IDM-VTON source (src/, gradio_demo/, configs/, ckpt/) in the same repo —
scripts/deploy_hf_endpoint.py copies it in. Human-parsing mask uses a SegFormer
clothes-parser (SCHP-class); garment detail comes from IDM-VTON's IP-Adapter-style
garment attention."""
import base64, io, torch, numpy as np
from PIL import Image
from transformers import AutoModelForSemanticSegmentation, SegformerImageProcessor

# SegFormer clothes labels: 4 upper, 5 skirt, 6 pants, 7 dress, 14/15 arms (kept for limb safety)
LABELS = {"upper_body": [4], "lower_body": [5, 6], "dresses": [4, 5, 6, 7]}
SIZE = (768, 1024)

def _b64img(s): return Image.open(io.BytesIO(base64.b64decode(s))).convert("RGB")

class EndpointHandler:
    def __init__(self, path=""):
        from src.tryon_pipeline import StableDiffusionXLInpaintPipeline as Pipe
        from src.unet_hacked_tryon import UNet2DConditionModel
        from src.unet_hacked_garmnet import UNet2DConditionModel as UNetRef
        from transformers import (CLIPImageProcessor, CLIPVisionModelWithProjection,
                                  CLIPTextModel, CLIPTextModelWithProjection, AutoTokenizer)
        from diffusers import AutoencoderKL, DDPMScheduler
        base, dt = "yisol/IDM-VTON", torch.float16
        unet = UNet2DConditionModel.from_pretrained(base, subfolder="unet", torch_dtype=dt)
        self.pipe = Pipe.from_pretrained(
            base, unet=unet, vae=AutoencoderKL.from_pretrained(base, subfolder="vae", torch_dtype=dt),
            feature_extractor=CLIPImageProcessor(),
            text_encoder=CLIPTextModel.from_pretrained(base, subfolder="text_encoder", torch_dtype=dt),
            text_encoder_2=CLIPTextModelWithProjection.from_pretrained(base, subfolder="text_encoder_2", torch_dtype=dt),
            tokenizer=AutoTokenizer.from_pretrained(base, subfolder="tokenizer", use_fast=False),
            tokenizer_2=AutoTokenizer.from_pretrained(base, subfolder="tokenizer_2", use_fast=False),
            scheduler=DDPMScheduler.from_pretrained(base, subfolder="scheduler"),
            image_encoder=CLIPVisionModelWithProjection.from_pretrained(base, subfolder="image_encoder", torch_dtype=dt),
            torch_dtype=dt).to("cuda")
        self.pipe.unet_encoder = UNetRef.from_pretrained(base, subfolder="unet_encoder", torch_dtype=dt).to("cuda")
        self.seg_proc = SegformerImageProcessor.from_pretrained("mattmdjaga/segformer_b2_clothes")
        self.seg = AutoModelForSemanticSegmentation.from_pretrained("mattmdjaga/segformer_b2_clothes").to("cuda")
        from gradio_demo import apply_net
        self.apply_net = apply_net

    def _mask(self, person, category):
        inp = self.seg_proc(images=person, return_tensors="pt").to("cuda")
        with torch.no_grad():
            lg = self.seg(**inp).logits
        lg = torch.nn.functional.interpolate(lg, size=person.size[::-1], mode="bilinear")
        lab = lg.argmax(1)[0].cpu().numpy()
        m = np.isin(lab, LABELS[category]).astype(np.uint8) * 255
        m = np.array(Image.fromarray(m).filter(__import__("PIL.ImageFilter").ImageFilter.MaxFilter(15)))
        return Image.fromarray(m)  # dilated to cover garment edges; arms/hands excluded

    def _pose(self, person):
        a = self.apply_net
        args = a.create_argument_parser().parse_args(("show", "./configs/densepose_rcnn_R_50_FPN_s1x.yaml",
            "./ckpt/densepose/model_final_162be9.pkl", "dummy", "-v", "--opts", "MODEL.DEVICE", "cuda"))
        return Image.fromarray(args.func(args, np.array(person.resize(SIZE)))[:, :, ::-1])

    def __call__(self, data):
        d = data["inputs"]
        person = _b64img(d["person_image"]).resize(SIZE)
        garment = _b64img(d["garment_image"]).resize(SIZE)
        cat = d.get("category", "upper_body")
        mask = self._mask(person, cat).resize(SIZE)
        pose = self._pose(person)
        with torch.no_grad(), torch.cuda.amp.autocast():
            out = self.pipe(prompt=f"model is wearing {d.get('description', 'a garment')}",
                negative_prompt="monochrome, lowres, bad anatomy, worst quality, low quality",
                image=person, mask_image=mask, ip_adapter_image=garment, pose_img=pose,
                cloth=garment, num_inference_steps=30, guidance_scale=2.0, strength=1.0,
                height=SIZE[1], width=SIZE[0]).images[0]
        buf = io.BytesIO(); out.save(buf, "JPEG", quality=92)
        return {"image": base64.b64encode(buf.getvalue()).decode()}
