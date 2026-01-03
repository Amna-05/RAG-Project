"""
Cookie-based authentication endpoints (Production approach).
File: src/rag/api/v1/auth.py

HOW IT WORKS:
- Tokens stored in httpOnly cookies (secure)
- Frontend never sees or handles tokens
- Automatic refresh on expired access token
- Seamless user experience
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from rag.core.database import get_db
from rag.core.rate_limiter import limiter, get_remote_address
from rag.api.deps import get_current_user, get_current_user_optional
from rag.models.user import User
from rag.schemas.user import UserCreate, UserResponse
from rag.schemas.auth import LoginRequest, PasswordChange
from rag.services import auth_service
from rag.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """
    Set authentication cookies in response.
    
    httpOnly=True: JavaScript cannot access (prevents XSS attacks)
    secure=True: Only sent over HTTPS (in production)
    samesite='lax': CSRF protection
    """
    # Access token cookie (short-lived)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # JavaScript cannot access
        secure=not settings.debug,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=settings.access_token_expire_minutes * 60,  # 30 minutes
        path="/"
    )
    
    # Refresh token cookie (long-lived)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,  # 7 days
        path="/"
    )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies (logout)."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute", key_func=get_remote_address)
async def register(
    request: Request,
    user_data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Register new user and auto-login (set cookies)."""
    try:
        # This returns BOTH user AND tokens
        user, tokens = await auth_service.register_new_user(db, user_data)
        
        # Set cookies (user auto-logged in)
        set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=UserResponse)
@limiter.limit("5/minute", key_func=get_remote_address)
async def login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and set auth cookies.
    """
    # Authenticate
    user = await auth_service.authenticate_user(
        db,
        credentials.email,  # ← NEW: Use email
        credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Get client info
    device_info = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    
    # Create tokens
    tokens = await auth_service.create_user_tokens(
        db, user, device_info=device_info, ip_address=ip_address
    )
    
    # Set cookies
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    
    return user


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user - clear cookies and revoke refresh token.
    
    Frontend just calls this endpoint, cookies cleared automatically.
    
    Frontend usage:
    ```javascript
    await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include'
    });
    // Redirect to login page
    ```
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token and current_user:
        # Revoke refresh token in database
        await auth_service.logout_user(db, refresh_token)
    
    # Clear cookies
    clear_auth_cookies(response)
    
    return {"message": "Successfully logged out"}


@router.post("/refresh")
@limiter.limit("5/minute", key_func=get_remote_address)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token from cookie.
    
    Frontend can call this manually, OR it happens automatically
    when access token expires (handled by middleware/interceptor).
    
    This endpoint is usually called by axios interceptor:
    ```javascript
    axios.interceptors.response.use(
        response => response,
        async error => {
            if (error.response?.status === 401) {
                // Auto-refresh token
                await axios.post('/api/v1/auth/refresh', {}, {credentials: 'include'});
                // Retry original request
                return axios(error.config);
            }
            return Promise.reject(error);
        }
    );
    ```
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Get client info
    device_info = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    
    # Refresh tokens
    new_tokens = await auth_service.refresh_user_tokens(
        db, refresh_token, device_info=device_info, ip_address=ip_address
    )
    
    if not new_tokens:
        # Refresh token invalid/expired
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Set new cookies
    set_auth_cookies(response, new_tokens.access_token, new_tokens.refresh_token)
    
    return {"message": "Token refreshed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    
    Protected endpoint - requires valid cookie.
    
    Frontend usage:
    ```javascript
    const response = await fetch('/api/v1/auth/me', {
        credentials: 'include'  // Sends cookies
    });
    const user = await response.json();
    ```
    """
    return current_user


@router.get("/check")
async def check_auth(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Check if user is authenticated.
    
    Useful for:
    - App initialization (check if user logged in)
    - Conditional rendering (show login vs dashboard)
    
    Frontend usage:
    ```javascript
    const {authenticated, user} = await fetch('/api/v1/auth/check', {
        credentials: 'include'
    }).then(r => r.json());
    
    if (authenticated) {
        // Show dashboard
    } else {
        // Show login
    }
    ```
    """
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
                "email": current_user.email
            }
        }
    
    return {"authenticated": False, "user": None}


@router.post("/logout-all")
async def logout_all_sessions(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout from all devices."""
    count = await auth_service.logout_all_sessions(db, current_user.id)
    
    # Clear current cookies
    clear_auth_cookies(response)
    
    return {"message": f"Logged out from {count} session(s)"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """Change password and logout all sessions."""
    from rag.core.security import verify_password, get_password_hash
    from sqlalchemy import update
    
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Update password
    new_hashed_password = get_password_hash(password_data.new_password)
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(hashed_password=new_hashed_password)
    )
    await db.commit()
    
    # Logout all sessions
    await auth_service.logout_all_sessions(db, current_user.id)
    
    # Clear cookies
    if response:
        clear_auth_cookies(response)
    
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
@limiter.limit("3/hour", key_func=get_remote_address)
async def forgot_password(
    request: Request,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email.

    **Flow:**
    1. User submits email
    2. We send reset email (if user exists)
    3. Return generic response (security: don't reveal if email exists)

    **Rate limit:** 3 per hour per IP (prevent abuse)

    **Frontend usage:**
    ```javascript
    const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: 'user@example.com'})
    });

    // Redirect to email confirmation page
    ```
    """
    from sqlalchemy import select
    from rag.services.email_service import send_password_reset_email
    from rag.core.logging import get_logger

    logger = get_logger(__name__)

    # Find user by email (safely - don't reveal if user exists)
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    # Generic response (same whether user exists or not)
    response_msg = "If an account exists with this email, we've sent a password reset link."

    if user:
        # Create reset link (in production, add token validation)
        # For now, simple link to frontend with email
        reset_link = f"{settings.frontend_url}/reset-password?email={email}"

        # Send email
        success = await send_password_reset_email(
            email=user.email,
            reset_link=reset_link,
            username=user.username
        )

        if success:
            logger.info(
                "password_reset_requested",
                user_id=str(user.id),
                email=user.email
            )
        else:
            logger.error(
                "password_reset_email_failed",
                user_id=str(user.id),
                email=user.email
            )

    return {"message": response_msg}
