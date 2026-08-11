from pydantic import BaseModel, Field
from typing import Optional, List


class ClassCreate(BaseModel):
    """新增班级请求体"""
    name: str = Field(..., max_length=50, description="班级名称，例如：高一(1)班")
    grade: str = Field(..., max_length=20, description="年级")
    head_teacher_id: Optional[int] = Field(None, description="班主任教师ID，可为空")


class ClassUpdate(BaseModel):
    """修改班级请求体"""
    name: str = Field(..., max_length=50, description="班级名称，例如：高一(1)班")
    grade: str = Field(..., max_length=20, description="年级")
    head_teacher_id: Optional[int] = Field(None, description="班主任教师ID，可为空")


# 新增：批量转移学生VO
class MoveStudentVO(BaseModel):
    student_ids: List[int] = Field(..., description="学生ID列表")
    target_class_id: int = Field(..., description="目标班级ID")