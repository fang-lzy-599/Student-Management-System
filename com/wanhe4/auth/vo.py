"""认证模块 - 请求 VO（注册/登录）"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """学生注册请求体"""
    username: str = Field(..., min_length=1, max_length=20, description="用户名（3-20位）")
    password: str = Field(..., min_length=6, max_length=20, description="密码（6-20位）")
    name: str = Field(..., max_length=50, description="角色")
    gender: str = Field("男", max_length=10, description="性别")
    age: int = Field(..., ge=10, le=100, description="年龄（10-100）")


class LoginRequest(BaseModel):
    """登录请求体"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
