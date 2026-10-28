import io
import cv2, numpy as np
from PIL import Image, ImageOps
from rembg import remove

TARGET = (768, 1024)  # 3:4

def normalize_person(data: bytes) -> bytes:
    """EXIF-fix, center-crop to 3:4, resize to 768x1024, lift low-light frames."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    img = ImageOps.fit(img, TARGET, Image.LANCZOS)
    arr = np.array(img)
    if arr.mean() < 70:  # low-light: CLAHE on luminance
        lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
        lab[..., 0] = cv2.createCLAHE(2.0, (8, 8)).apply(lab[..., 0])
        arr = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    out = io.BytesIO(); Image.fromarray(arr).save(out, "JPEG", quality=92)
    return out.getvalue()

def clean_garment(data: bytes) -> bytes:
    """Remove background, pad to square-ish 3:4 canvas on white."""
    cut = remove(Image.open(io.BytesIO(data)).convert("RGBA"))
    canvas = Image.new("RGBA", TARGET, (255, 255, 255, 255))
    cut.thumbnail((TARGET[0] - 40, TARGET[1] - 40))
    canvas.paste(cut, ((TARGET[0] - cut.width) // 2, (TARGET[1] - cut.height) // 2), cut)
    out = io.BytesIO(); canvas.convert("RGB").save(out, "JPEG", quality=92)
    return out.getvalue()
