"""매물 사진 화각(°) 추정 + 표준 렌즈(1x) 시야 복원.

- 추정: EfficientNet-B0 전이학습, 출력 1개(수평 화각 회귀).
  데이터: 팀이 같은 위치에서 0.5x·1x로 찍은 실내 사진 쌍. EXIF 35mm 환산 초점거리로 라벨 생성.
- 복원: 직선 투영(rectilinear) 가정 시 가운데 크롭 비율 = tan(θ_std/2) / tan(θ_est/2).
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

STD_FOV_DEG = 69.4  # 35mm 환산 26mm(스마트폰 1x)의 수평 화각


def fov_from_focal_35mm(focal_mm: float, sensor_w: float = 36.0) -> float:
    """EXIF FocalLengthIn35mmFilm → 수평 화각(°). 학습 라벨 생성용."""
    return math.degrees(2 * math.atan(sensor_w / (2 * focal_mm)))


def crop_ratio(est_fov_deg: float, std_fov_deg: float = STD_FOV_DEG) -> float:
    if est_fov_deg <= std_fov_deg:
        return 1.0  # 이미 표준 이하 → 그대로
    return math.tan(math.radians(std_fov_deg) / 2) / math.tan(math.radians(est_fov_deg) / 2)


def restore_standard_view(img: Image.Image, est_fov_deg: float) -> Image.Image:
    """가운데를 잘라 1x로 찍었을 때 보이는 범위만 남긴 뒤 원래 크기로 확대."""
    r = crop_ratio(est_fov_deg)
    w, h = img.size
    cw, ch = w * r, h * r
    box = (round((w - cw) / 2), round((h - ch) / 2), round((w + cw) / 2), round((h + ch) / 2))
    return img.crop(box).resize((w, h), Image.LANCZOS)


def wide_angle_flag(est_fov_deg: float, threshold_deg: float = 85.0) -> str:
    """허위 판정이 아니라 참고 정보로만 표시."""
    return "실제보다 넓어 보일 수 있음" if est_fov_deg >= threshold_deg else "표준 화각에 가까움"


def build_model(pretrained: bool = True):
    """EfficientNet-B0 백본 + 회귀 헤드."""
    import torch.nn as nn
    from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

    m = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT if pretrained else None)
    m.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(m.classifier[1].in_features, 1))
    return m


def exif_fov(path) -> float | None:
    """사진 EXIF의 35mm 환산 초점거리 → 화각(°). 없으면 None (학습에서 제외)."""
    focal = Image.open(path).getexif().get_ifd(0x8769).get(41989)  # FocalLengthIn35mmFilm
    return fov_from_focal_35mm(float(focal)) if focal else None


def _to_tensor(img: Image.Image):
    # 가운데 크롭을 하면 화각 자체가 바뀌므로 전체를 224×224로 줄이기만 한다 (ImageNet 정규화).
    from torchvision import transforms as T
    tf = T.Compose([T.Resize((224, 224)), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    return tf(img.convert("RGB"))


def train_fov(image_dir, epochs: int = 10, lr: float = 1e-4, batch: int = 16,
              out="models/fov.pt", pretrained: bool = True, seed: int = 42):
    """image_dir 아래 jpg 중 EXIF 초점거리가 있는 사진으로 화각 회귀 학습. 반환: (model, 검증 MAE[°])."""
    import random

    import torch

    data = [(p, f) for p in sorted(Path(image_dir).rglob("*"))
            if p.suffix.lower() in {".jpg", ".jpeg"} and (f := exif_fov(p))]
    if len(data) < 2:
        raise ValueError(f"{image_dir}: EXIF 초점거리 있는 jpg가 2장 미만")
    random.Random(seed).shuffle(data)
    n_va = max(1, len(data) // 5)
    va, tr = data[:n_va], data[n_va:]

    torch.manual_seed(seed)
    model = build_model(pretrained)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)

    def batches(rows, flip):
        for i in range(0, len(rows), batch):
            chunk = rows[i:i + batch]
            imgs = [Image.open(p) for p, _ in chunk]
            if flip:  # 좌우 반전은 화각을 안 바꿈
                imgs = [im.transpose(Image.FLIP_LEFT_RIGHT) if random.random() < 0.5 else im for im in imgs]
            yield torch.stack([_to_tensor(im) for im in imgs]), torch.tensor([f for _, f in chunk])

    for _ in range(epochs):
        model.train()
        random.shuffle(tr)
        for x, y in batches(tr, flip=True):
            loss = torch.nn.functional.l1_loss(model(x).squeeze(1) * 100, y)  # 출력 ×100 = 도(°)
            opt.zero_grad()
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        err = [abs(model(x).squeeze(1) * 100 - y) for x, y in batches(va, flip=False)]
    mae = float(torch.cat(err).mean())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out)
    return model, mae


def load_fov_model(path="models/fov.pt"):
    import torch
    m = build_model(pretrained=False)
    m.load_state_dict(torch.load(path, map_location="cpu"))
    return m.eval()


def predict_fov(model, img: Image.Image) -> float:
    import torch
    model.eval()
    with torch.no_grad():
        return float(model(_to_tensor(img).unsqueeze(0))[0, 0] * 100)
