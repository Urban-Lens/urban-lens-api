from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from database import get_db
from config.config import settings
from modules.auth.auth_service import AuthService
from modules.auth.schema import Token, PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest, LoginRequest
from modules.users.schema import UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

# Configure OAuth2 with the login endpoint URL
# We still support form-based auth for compatibility with tools like swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/form")


# Dependency to get the current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user from the token"""
    return await AuthService.get_current_user(db, token)


# Dependency to get the current active user
async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Mock function to send password reset email
async def send_password_reset_email(email: str, token: str):
    """
    This would send an email in a real application.
    In this example, we'll just log the token.
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    print(f"Password reset token for {email}: {token}")
    print(f"Reset URL: {reset_url}")
    # In a real application, you would use an email service to send the link


@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint to get an access token"""
    user = await AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request a password reset token"""
    # We always return 202 Accepted whether the email exists or not
    # to prevent email enumeration attacks
    result = await AuthService.request_password_reset(db, request.email)
    
    if result:
        token, user = result
        # In a real app, send the email in the background
        background_tasks.add_task(send_password_reset_email, user.email, token)
    
    return {"detail": "If your email is registered, you will receive a password reset link."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Reset a password using a reset token"""
    success = await AuthService.reset_password(db, request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    return {"detail": "Password has been reset successfully."}


@router.post("/change-password", response_model=UserResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password for the authenticated user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify current password
    if not current_user.verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    password_hash = current_user.get_password_hash(request.new_password)
    updated_user = await current_user.update(db, password_hash=password_hash)
    
    return updated_user


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user = Depends(get_current_active_user)
):
    """Get information about the currently authenticated user"""
    return current_user


# Add an additional form-based login endpoint for compatibility
@router.post("/login/form", include_in_schema=False)
async def login_with_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Form-based login endpoint for OAuth2 compatibility (e.g., for Swagger UI)"""
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"} 