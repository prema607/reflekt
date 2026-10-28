# Women's Dual-Mode VTO
## Run locally
1. `cp .env.example .env` and fill keys (MongoDB Atlas, Upstash Redis, Replicate, Cloudinary)
2. `pip install -r requirements.txt pytest && pytest tests`
3. `docker compose up --build`   (API :8000, worker)
4. `python scripts_seed.py`  or POST `/api/v1/admin/garments` (multipart: name, category, slot, opacity, image)
5. `./setup_frontend.sh` then `flutter run -d chrome --dart-define=API_BASE=http://localhost:8000`
## Go live checklist
- Set `AUTH_REQUIRED=true`, `ADMIN_UIDS`, lock `ALLOWED_ORIGINS` to your domain
- Deploy API+worker (Render/Fly/Cloud Run), `flutter build web` to Firebase Hosting/Netlify
- Pin the Replicate model version hash in `vto_engine.py`; budget GPU cost per render
- Add Firebase sign-in in Flutter and set `ApiService.token`

## Hugging Face GPU endpoint
```
git clone https://github.com/yisol/IDM-VTON   # download its ckpt/ weights per its README
export HUGGINGFACE_API_TOKEN=hf_xxx
python scripts/deploy_hf_endpoint.py --idm-vton-dir ./IDM-VTON
```
Put the printed `HF_ENDPOINT_URL` in `.env`. Endpoint scales to zero (first render after idle takes minutes). Firebase: fill `frontend/lib/firebase/firebase_options.dart`, set `AUTH_REQUIRED=true`.
