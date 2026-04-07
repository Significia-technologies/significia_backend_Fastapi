from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.auth_schema import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    print(f"--- REACHED REGISTER ROUTE FOR: {request.email} ---")
    user = auth_service.register_user(db, request)
    print("--- REGISTER ROUTE COMPLETED ---")
    return user

@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, http_request: Request, db: Session = Depends(get_db)):
    client_host = http_request.client.host if http_request.client else "127.0.0.1"
    ip_address = "127.0.0.1" if client_host == "testclient" else client_host
    user_agent = http_request.headers.get("user-agent", "")
    return auth_service.authenticate_user(db, request, request_ip=ip_address, user_agent=user_agent)

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_access_token(db, request.refresh_token)

@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout-others")
def logout_others(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Forcefully sign out all devices by incrementing the refresh token version.
    This will invalidate the current device's session as well.
    """
    current_user.refresh_token_version += 1
    db.commit()
    return {"message": "All other sessions have been invalidated. Please log in again."}
