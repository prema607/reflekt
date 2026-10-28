# Phase 4 – QA & Security Matrix
| Area | Test | Expected |
|---|---|---|
| Ghosting/clipping | Hands crossing torso, wrists near sleeves | Exclude SCHP arm/hand labels from garment mask |
| Low light | Webcam <50 lux | CLAHE/gamma pre-pass; warn user on low luminance |
| Size inclusivity | S to 3XL photos | Mask scales to SCHP body area, no fixed template |
| Sheer fabric | Net/organza dupatta | Opacity 0.3-0.7 shows layers beneath |
| Saree pallu | Rotate shoulders | Anchor follows keypoint 11 |
| Indexes | Catalog query | explain() shows IXSCAN on (target_audience, apparel_type, category) |
| Upload security | .exe renamed .jpg; >10MB | 415 / 413 |
| Rate limit | 6 snapshots/min | 429 on the 6th |
| CORS | Unlisted origin | Blocked |
| Job lifecycle | Kill worker mid-job | Add timeout sweeper for stuck PROCESSING |
