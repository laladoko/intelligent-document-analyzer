from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
from .database import Base

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRole(Base):
    """用户角色表"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, comment="角色名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="角色描述")
    permissions = Column(Text, comment="权限列表，JSON格式")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 关系
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<UserRole(id={self.id}, name='{self.name}')>"

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    email = Column(String(100), nullable=False, unique=True, comment="邮箱")
    full_name = Column(String(100), comment="全名")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    
    # 角色和状态
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=False, comment="角色ID")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_verified = Column(Boolean, default=False, comment="是否验证邮箱")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    
    # 登录相关
    last_login = Column(DateTime(timezone=True), comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    failed_login_attempts = Column(Integer, default=0, comment="失败登录次数")
    locked_until = Column(DateTime(timezone=True), comment="锁定到期时间")
    
    # 个人信息
    avatar_url = Column(String(500), comment="头像URL")
    phone = Column(String(20), comment="手机号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 关系
    role = relationship("UserRole", back_populates="users")
    login_logs = relationship("UserLoginLog", back_populates="user")
    knowledge_items = relationship("KnowledgeBase", back_populates="creator")
    
    # 索引
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role_id'),
        Index('idx_users_active', 'is_active'),
    )
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str):
        """设置密码"""
        self.hashed_password = pwd_context.hash(password)
    
    @property
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until:
            from datetime import datetime
            return datetime.now() < self.locked_until
        return False
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class UserLoginLog(Base):
    """用户登录日志表"""
    __tablename__ = "user_login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    login_time = Column(DateTime(timezone=True), server_default=func.now(), comment="登录时间")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    login_method = Column(String(20), default="password", comment="登录方式")
    is_success = Column(Boolean, default=True, comment="是否成功")
    failure_reason = Column(String(200), comment="失败原因")
    session_id = Column(String(100), comment="会话ID")
    logout_time = Column(DateTime(timezone=True), comment="登出时间")
    
    # 关系
    user = relationship("User", back_populates="login_logs")
    
    # 索引
    __table_args__ = (
        Index('idx_login_logs_user', 'user_id'),
        Index('idx_login_logs_time', 'login_time'),
        Index('idx_login_logs_ip', 'ip_address'),
    )
    
    def __repr__(self):
        return f"<UserLoginLog(id={self.id}, user_id={self.user_id})>"

class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    session_token = Column(String(255), nullable=False, unique=True, comment="会话令牌")
    refresh_token = Column(String(255), comment="刷新令牌")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    last_used = Column(DateTime(timezone=True), comment="最后使用时间")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    
    # 关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_sessions_token', 'session_token'),
        Index('idx_sessions_user', 'user_id'),
        Index('idx_sessions_expires', 'expires_at'),
    )
    
    @property
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        from datetime import datetime
        return datetime.now() > self.expires_at
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>" 