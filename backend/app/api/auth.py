from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.models.database import get_db
from app.models.user import User, UserRole, UserSession
from app.models.auth_schemas import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    TokenRefreshRequest, TokenRefreshResponse, LogoutRequest,
    UserProfile, UserPasswordUpdate, PasswordResetRequest, PasswordResetConfirm
)
from app.services.auth_service import (
    AuthService, get_current_user, get_current_active_user, security
)

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        # 查找用户
        user = AuthService.get_user_by_username_or_email(db, login_data.username)
        
        if not user:
            # 不记录失败的登录尝试，避免数据库错误
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 检查用户是否被锁定
        if AuthService.is_user_locked(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被锁定，请稍后再试"
            )
        
        # 检查用户是否激活
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户未激活"
            )
        
        # 验证密码
        if not user.verify_password(login_data.password):
            # 增加失败尝试次数
            AuthService.increment_failed_attempts(db, user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 登录成功，重置失败尝试次数
        AuthService.reset_failed_attempts(db, user)
        
        # 创建令牌
        access_token_expires = timedelta(minutes=30)
        access_token = AuthService.create_access_token(
            data={
                "sub": user.id,
                "username": user.username,
                "role": user.role.name if user.role else "user"
            },
            expires_delta=access_token_expires
        )
        
        refresh_token = AuthService.create_refresh_token()
        
        # 创建会话
        session = AuthService.create_user_session(
            db, user, refresh_token, request, login_data.remember_me
        )
        
        # 更新最后登录时间
        AuthService.update_last_login(db, user)
        
        # 构建用户资料
        user_profile = UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            department=user.department,
            position=user.position,
            avatar_url=user.avatar_url,
            role=user.role,
            last_login=user.last_login,
            created_at=user.created_at
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@router.post("/register", response_model=RegisterResponse)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(
            (User.username == register_data.username) | 
            (User.email == register_data.email)
        ).first()
        
        if existing_user:
            if existing_user.username == register_data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )
        
        # 获取默认角色（普通用户）
        default_role = db.query(UserRole).filter(UserRole.name == "user").first()
        if not default_role:
            # 如果没有默认角色，创建一个
            default_role = UserRole(
                name="user",
                display_name="普通用户",
                description="系统默认用户角色",
                permissions='["read"]'
            )
            db.add(default_role)
            db.commit()
            db.refresh(default_role)
        
        # 创建新用户
        new_user = User(
            username=register_data.username,
            email=register_data.email,
            full_name=register_data.full_name,
            phone=register_data.phone,
            role_id=default_role.id
        )
        new_user.set_password(register_data.password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return RegisterResponse(
            message="注册成功",
            user_id=new_user.id,
            username=new_user.username,
            email=new_user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        # 查找会话
        session = AuthService.get_session_by_refresh_token(db, refresh_data.refresh_token)
        
        if not session or session.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效或已过期"
            )
        
        # 获取用户
        user = AuthService.get_user_by_id(db, session.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=30)
        access_token = AuthService.create_access_token(
            data={
                "sub": user.id,
                "username": user.username,
                "role": user.role.name if user.role else "user"
            },
            expires_delta=access_token_expires
        )
        
        # 更新会话最后使用时间
        session.last_used = datetime.now()
        db.commit()
        
        return TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新令牌失败: {str(e)}"
        )

@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    try:
        # 如果提供了刷新令牌，使对应会话失效
        if logout_data.refresh_token:
            session = AuthService.get_session_by_refresh_token(db, logout_data.refresh_token)
            if session and session.user_id == current_user.id:
                AuthService.invalidate_session(db, session)
        
        # 使所有用户会话失效（可选，根据需求决定）
        # sessions = db.query(UserSession).filter(
        #     UserSession.user_id == current_user.id,
        #     UserSession.is_active == True
        # ).all()
        # for session in sessions:
        #     AuthService.invalidate_session(db, session)
        
        return {"message": "登出成功"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        department=current_user.department,
        position=current_user.position,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        last_login=current_user.last_login,
        created_at=current_user.created_at
    )

@router.put("/password")
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        # 验证当前密码
        if not current_user.verify_password(password_data.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 设置新密码
        current_user.set_password(password_data.new_password)
        db.commit()
        
        # 使所有会话失效，强制重新登录
        sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).all()
        for session in sessions:
            AuthService.invalidate_session(db, session)
        
        return {"message": "密码修改成功，请重新登录"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改密码失败: {str(e)}"
        )

@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """请求密码重置"""
    try:
        user = db.query(User).filter(User.email == reset_data.email).first()
        
        if not user:
            # 为了安全，即使用户不存在也返回成功消息
            return {"message": "如果邮箱存在，重置链接已发送"}
        
        # TODO: 实现邮件发送功能
        # 这里应该生成重置令牌并发送邮件
        
        return {"message": "如果邮箱存在，重置链接已发送"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码重置请求失败: {str(e)}"
        )

@router.post("/guest-login", response_model=LoginResponse)
async def guest_login(request: Request):
    """游客登录"""
    try:
        # 生成游客用户ID（使用时间戳的后几位作为数字ID，确保唯一性）
        import time
        timestamp = int(time.time() * 1000)
        # 使用负数ID来避免与真实用户ID冲突，并确保在合理范围内
        guest_id = -(timestamp % 2147483647)  # 使用负数避免与正数用户ID冲突
        guest_id_str = str(guest_id)
        
        # 创建游客令牌数据
        guest_data = {
            "sub": guest_id_str,
            "username": "游客用户",
            "role": "guest",
            "is_guest": True
        }
        
        # 生成游客访问令牌（有效期1小时）
        access_token_expires = timedelta(hours=1)
        access_token = AuthService.create_access_token(
            data=guest_data,
            expires_delta=access_token_expires
        )
        
        # 生成虚拟刷新令牌
        refresh_token = AuthService.create_refresh_token()
        
        # 构建游客用户资料
        guest_profile = UserProfile(
            id=guest_id,
            username="游客用户",
            email="guest@temp.com",
            full_name="游客用户",
            phone=None,
            department="游客",
            position="访客",
            avatar_url=None,
            role=UserRole(
                id=0,
                name="guest",
                display_name="游客",
                description="临时游客用户",
                permissions='["read"]',
                is_active=True,
                created_at=datetime.now(),
                updated_at=None
            ),
            last_login=None,
            created_at=datetime.now()
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user=guest_profile
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"游客登录失败: {str(e)}"
        )

@router.get("/verify")
async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """验证令牌有效性"""
    try:
        # 如果没有提供认证信息，返回无效
        if not credentials:
            return {"valid": False, "error": "未提供认证令牌"}
        
        token = credentials.credentials
        payload = AuthService.verify_token(token)
        
        if payload is None:
            return {"valid": False, "error": "令牌无效"}
        
        # 检查是否是游客令牌
        if hasattr(payload, 'role') and payload.role == 'guest':
            return {
                "valid": True, 
                "user_id": payload.sub, 
                "username": "游客用户",
                "is_guest": True,
                "expires_at": payload.exp
            }
        
        user = AuthService.get_user_by_id(db, int(payload.sub))
        if not user or not user.is_active:
            return {"valid": False, "error": "用户不存在或已被禁用"}
        
        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "is_guest": False,
            "expires_at": payload.exp
        }
        
    except Exception as e:
        return {"valid": False, "error": str(e)} 