from datetime import datetime, timedelta
from typing import Optional, Union
import jwt
import secrets
import uuid
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.database import get_db
from app.models.user import User, UserRole, UserSession, UserLoginLog
from app.models.auth_schemas import TokenPayload, UserProfile
import os
from dotenv import load_dotenv

load_dotenv()

# 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证
security = HTTPBearer()

class AuthService:
    """认证服务类"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "jti": str(uuid.uuid4())
        })
        
        # 确保 sub 字段是字符串
        if "sub" in to_encode:
            to_encode["sub"] = str(to_encode["sub"])
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token() -> str:
        """创建刷新令牌"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_data = TokenPayload(**payload)
            return token_data
        except jwt.ExpiredSignatureError:
            # 对于过期的令牌，仍然尝试解码但不验证过期时间
            # 这是为了处理系统时间不准确的情况
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
                token_data = TokenPayload(**payload)
                return token_data
            except Exception:
                return None
        except jwt.PyJWTError:
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_user_by_username_or_email(db: Session, username: str) -> Optional[User]:
        """通过用户名或邮箱获取用户"""
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """认证用户"""
        user = AuthService.get_user_by_username_or_email(db, username)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        return user
    
    @staticmethod
    def is_user_locked(user: User) -> bool:
        """检查用户是否被锁定"""
        if user.locked_until and datetime.now() < user.locked_until:
            return True
        return False
    
    @staticmethod
    def lock_user(db: Session, user: User):
        """锁定用户"""
        user.locked_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        db.commit()
    
    @staticmethod
    def unlock_user(db: Session, user: User):
        """解锁用户"""
        user.locked_until = None
        user.failed_login_attempts = 0
        db.commit()
    
    @staticmethod
    def increment_failed_attempts(db: Session, user: User):
        """增加失败尝试次数"""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            AuthService.lock_user(db, user)
        db.commit()
    
    @staticmethod
    def reset_failed_attempts(db: Session, user: User):
        """重置失败尝试次数"""
        user.failed_login_attempts = 0
        db.commit()
    
    @staticmethod
    def create_user_session(
        db: Session, 
        user: User, 
        refresh_token: str,
        request: Request,
        remember_me: bool = False
    ) -> UserSession:
        """创建用户会话"""
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        if remember_me:
            expires_delta = timedelta(days=30)  # 记住我30天
        
        session = UserSession(
            user_id=user.id,
            session_token=AuthService.create_access_token({"sub": user.id}),
            refresh_token=refresh_token,
            expires_at=datetime.now() + expires_delta,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def get_session_by_refresh_token(db: Session, refresh_token: str) -> Optional[UserSession]:
        """通过刷新令牌获取会话"""
        return db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True
        ).first()
    
    @staticmethod
    def invalidate_session(db: Session, session: UserSession):
        """使会话失效"""
        session.is_active = False
        db.commit()
    
    @staticmethod
    def log_login_attempt(
        db: Session,
        user_id: Optional[int],
        request: Request,
        is_success: bool,
        failure_reason: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """记录登录尝试"""
        log = UserLoginLog(
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", ""),
            is_success=is_success,
            failure_reason=failure_reason,
            session_id=session_id
        )
        db.add(log)
        db.commit()
    
    @staticmethod
    def update_last_login(db: Session, user: User):
        """更新最后登录时间"""
        user.last_login = datetime.now()
        user.login_count += 1
        db.commit()

# 依赖注入函数
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = AuthService.verify_token(token)
        if payload is None:
            raise credentials_exception
        
        user = AuthService.get_user_by_id(db, payload.sub)
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户账户已被禁用"
            )
        
        if AuthService.is_user_locked(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户账户已被锁定"
            )
        
        return user
    except Exception as e:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户未激活"
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

def require_permissions(required_permissions: list):
    """权限检查装饰器"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if current_user.is_superuser:
            return current_user
        
        # 检查用户角色权限
        if current_user.role and current_user.role.permissions:
            import json
            try:
                user_permissions = json.loads(current_user.role.permissions)
                if not all(perm in user_permissions for perm in required_permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足"
                    )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限配置错误"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return current_user
    
    return permission_checker

# 可选的认证依赖（不强制要求登录）
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = AuthService.verify_token(token)
        if payload is None:
            return None
        
        user = AuthService.get_user_by_id(db, payload.sub)
        if user is None or not user.is_active:
            return None
        
        return user
    except Exception:
        return None

# 支持游客和真实用户的认证依赖
async def get_current_user_or_guest(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户或游客"""
    # 如果没有提供认证凭据，返回游客用户
    if not credentials:
        return {
            "id": "guest",
            "username": "游客用户",
            "is_guest": True,
            "role": "guest"
        }
    
    try:
        token = credentials.credentials
        payload = AuthService.verify_token(token)
        if payload is None:
            # 如果token无效，返回游客用户而不是抛出异常
            return {
                "id": "guest",
                "username": "游客用户",
                "is_guest": True,
                "role": "guest"
            }
        
        # 检查是否是游客令牌
        if hasattr(payload, 'role') and payload.role == 'guest':
            # 返回游客信息的字典
            return {
                "id": payload.sub,
                "username": "游客用户",
                "is_guest": True,
                "role": "guest"
            }
        
        # 处理真实用户
        user = AuthService.get_user_by_id(db, payload.sub)
        if user is None:
            # 如果用户不存在，返回游客用户
            return {
                "id": "guest",
                "username": "游客用户",
                "is_guest": True,
                "role": "guest"
            }
        
        if not user.is_active:
            # 如果用户不活跃，返回游客用户
            return {
                "id": "guest",
                "username": "游客用户",
                "is_guest": True,
                "role": "guest"
            }
        
        if AuthService.is_user_locked(user):
            # 如果用户被锁定，返回游客用户
            return {
                "id": "guest",
                "username": "游客用户",
                "is_guest": True,
                "role": "guest"
            }
        
        # 返回真实用户对象，添加is_guest标识
        user.is_guest = False
        return user
        
    except Exception as e:
        # 任何异常都返回游客用户
        return {
            "id": "guest",
            "username": "游客用户",
            "is_guest": True,
            "role": "guest"
        } 