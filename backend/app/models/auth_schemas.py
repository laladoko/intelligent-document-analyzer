from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum

# 基础模式
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 用户角色模式
class UserRoleBase(BaseSchema):
    name: str = Field(..., max_length=50, description="角色名称")
    display_name: str = Field(..., max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="角色描述")
    permissions: Optional[str] = Field(None, description="权限列表")
    is_active: bool = Field(True, description="是否启用")

class UserRoleCreate(UserRoleBase):
    pass

class UserRoleUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    permissions: Optional[str] = None
    is_active: Optional[bool] = None

class UserRole(UserRoleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# 用户模式
class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role_id: int = Field(..., description="角色ID")
    is_active: bool = Field(True, description="是否启用")
    is_verified: bool = Field(False, description="是否验证邮箱")
    is_superuser: bool = Field(False, description="是否超级管理员")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含至少一个字母')
        return v

class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserPasswordUpdate(BaseSchema):
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含至少一个字母')
        return v

class User(UserBase):
    id: int
    role_id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    role: Optional[UserRole] = None

class UserProfile(BaseSchema):
    """用户个人资料（不包含敏感信息）"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    is_guest: Optional[bool] = Field(False, description="是否为游客用户")

# 认证相关模式
class LoginRequest(BaseSchema):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")

class LoginResponse(BaseSchema):
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user: UserProfile = Field(..., description="用户信息")

class TokenRefreshRequest(BaseSchema):
    refresh_token: str = Field(..., description="刷新令牌")

class TokenRefreshResponse(BaseSchema):
    access_token: str = Field(..., description="新的访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")

class LogoutRequest(BaseSchema):
    refresh_token: Optional[str] = Field(None, description="刷新令牌")

# 注册相关模式
class RegisterRequest(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含至少一个字母')
        return v

class RegisterResponse(BaseSchema):
    message: str = Field(..., description="注册结果消息")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")

# 密码重置相关模式
class PasswordResetRequest(BaseSchema):
    email: EmailStr = Field(..., description="邮箱")

class PasswordResetConfirm(BaseSchema):
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v

# 用户登录日志模式
class UserLoginLogBase(BaseSchema):
    ip_address: Optional[str] = Field(None, max_length=45, description="IP地址")
    user_agent: Optional[str] = Field(None, max_length=500, description="用户代理")
    login_method: str = Field("password", description="登录方式")
    is_success: bool = Field(True, description="是否成功")
    failure_reason: Optional[str] = Field(None, max_length=200, description="失败原因")

class UserLoginLog(UserLoginLogBase):
    id: int
    user_id: int
    login_time: datetime
    session_id: Optional[str] = None
    logout_time: Optional[datetime] = None

# 用户会话模式
class UserSessionBase(BaseSchema):
    ip_address: Optional[str] = Field(None, max_length=45, description="IP地址")
    user_agent: Optional[str] = Field(None, max_length=500, description="用户代理")

class UserSession(UserSessionBase):
    id: int
    user_id: int
    session_token: str
    expires_at: datetime
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool

# 用户列表和搜索模式
class UserListRequest(BaseSchema):
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    role_id: Optional[int] = Field(None, description="角色筛选")
    is_active: Optional[bool] = Field(None, description="状态筛选")
    department: Optional[str] = Field(None, description="部门筛选")

class UserListResponse(BaseSchema):
    users: List[User]
    total: int
    page: int
    page_size: int
    total_pages: int

# 用户统计模式
class UserStats(BaseSchema):
    total_users: int = Field(description="总用户数")
    active_users: int = Field(description="活跃用户数")
    new_users_today: int = Field(description="今日新增用户")
    new_users_week: int = Field(description="本周新增用户")
    login_count_today: int = Field(description="今日登录次数")
    online_users: int = Field(description="在线用户数")

# JWT令牌载荷模式
class TokenPayload(BaseSchema):
    sub: Union[int, str] = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    role: Optional[str] = Field(None, description="角色")
    is_guest: Optional[bool] = Field(None, description="是否游客")
    exp: int = Field(..., description="过期时间戳")
    iat: int = Field(..., description="签发时间戳")
    jti: str = Field(..., description="JWT ID")
    
    @validator('sub', pre=True)
    def convert_sub_to_int(cls, v):
        """将字符串类型的sub转换为整数"""
        if isinstance(v, str):
            return int(v)
        return v 