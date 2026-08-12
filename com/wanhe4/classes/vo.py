"""
班级模块 - 请求体 VO（Value Object）

职责：
    定义班级接口的请求体结构。使用 Pydantic 的 BaseModel，
    FastAPI 收到请求后会自动完成：
      - 类型转换（如字符串数字 -> int）
      - 必填校验（字段无默认值即必填，缺省返回 422）
      - 长度/范围校验（Field 的 max_length 等）
    校验不通过时 FastAPI 返回 422 校验错误，无需在路由中手写判断。

说明：
    - ClassCreate 与 ClassUpdate 字段完全一致，仅语义不同：
        ClassCreate 用于「新增」，ClassUpdate 用于「修改」，
        分开定义便于后续各自演进（例如新增时未来可能加 create_time 等字段）。
    - head_teacher_id 为 Optional[int]，传 null 或省略即表示「不设置班主任」。
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ClassCreate(BaseModel):
    """
    新增班级请求体

    请求示例：
        POST /classes/add
        {
            "name": "高一(1)班",
            "grade": "高一",
            "head_teacher_id": 1          // 可选，null/缺省 = 不设班主任
        }
    """
    name: str = Field(..., max_length=50, description="班级名称，例如：高一(1)班")
    grade: str = Field(..., max_length=20, description="年级")
    head_teacher_id: Optional[int] = Field(None, description="班主任教师ID，可为空")


class ClassUpdate(BaseModel):
    """
    修改班级请求体

    请求示例：
        PUT /classes/update/1
        {
            "name": "高一(1)班",
            "grade": "高一",
            "head_teacher_id": 2          // 传 null 表示移除班主任
        }
    """
    name: str = Field(..., max_length=50, description="班级名称，例如：高一(1)班")
    grade: str = Field(..., max_length=20, description="年级")
    head_teacher_id: Optional[int] = Field(None, description="班主任教师ID，可为空")


# 新增：批量转移学生 VO
class MoveStudentVO(BaseModel):
    """
    批量转移学生请求体（学生 -> 目标班级）

    请求示例：
        POST /classes/move_students
        {
            "student_ids": [1, 2, 3],
            "target_class_id": 2
        }
    """
    student_ids: List[int] = Field(..., description="学生ID列表")
    target_class_id: int = Field(..., description="目标班级ID")
