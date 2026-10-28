from fastapi import Depends, HTTPException, Header
from backend.config import settings

_ready = False
def _init():
    global _ready
    if _ready: return
    import firebase_admin
    from firebase_admin import credentials
    firebase_admin.initialize_app(credentials.Certificate(settings.firebase_credentials))
    _ready = True

async def current_uid(authorization: str | None = Header(None)) -> str:
    """AUTH_REQUIRED=false -> 'anon' (local dev); true -> verifies Firebase ID token."""
    if not settings.auth_required:
        return "anon"
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    try:
        _init()
        from firebase_admin import auth
        return auth.verify_id_token(authorization[7:])["uid"]
    except Exception:
        raise HTTPException(401, "Invalid token")

async def admin_uid(uid: str = Depends(current_uid)) -> str:
    if settings.auth_required and uid not in [a for a in settings.admin_uids.split(",") if a]:
        raise HTTPException(403, "Admins only")
    return uid
