# 文件名：teacher/vo.py
"""
教师模块 - 请求 VO

职责：定义教师新增/修改请求体的字段与校验规则
依赖：pydantic（BaseModel / Field）
"""
from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    """新增教师请求体"""
    name: str = Field(..., max_length=50, description="姓名")
    gender: str = Field('男', max_length=10, description="性别")
    age: int = Field(..., ge=20, le=70, description="年龄")
    subject: str = Field(..., max_length=50, description="教授科目")
    phone: str = Field('', max_length=20, description="联系电话")


class TeacherUpdate(BaseModel):
    """修改教师信息请求体（字段与新增一致）"""
    name: str = Field(..., max_length=50, description="姓名")
    gender: str = Field('男', max_length=10, description="性别")
    age: int = Field(..., ge=20, le=70, description="年龄")
    subject: str = Field(..., max_length=50, description="教授科目")
    phone: str = Field('', max_length=20, description="联系电话")
