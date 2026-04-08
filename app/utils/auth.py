from fastapi import Request, HTTPException
from jose import jwt, JWTError

from app.core.config import SUPABASE_JWT_SECRET, _DEV_USER_ID


def get_current_user(request: Request) -> str:
    """
    Extracts and verifies the Supabase JWT from the Authorization header.
    Returns the user's UUID as a string.
    Falls back to _DEV_USER_ID if no token is present and we're in dev mode.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        if _DEV_USER_ID:
            return _DEV_USER_ID
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = auth_header.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase doesn't set a standard audience
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing subject claim")
        return user_id

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")