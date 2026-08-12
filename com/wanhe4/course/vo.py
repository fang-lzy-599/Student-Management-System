from typing import Literal

from pydantic import BaseModel, Field


CourseGrade = Literal["高一", "高二", "高三"]


class CourseCreate(BaseModel):
    """新增课程请求体。"""

    name: str = Field(..., max_length=50, description="课程名称")
    credit: int = Field(1, ge=1, le=5, description="学分（1-5分）")
    grade: CourseGrade = Field(..., description="所属年级：高一/高二/高三")
    teacher_id: int | None = Field(None, description="授课教师ID（可空）")

class CourseUpdate(BaseModel):
    """修改课程请求体。"""

    name: str = Field(..., max_length=50, description="课程名称")
    credit: int = Field(1, ge=1, le=5, description="学分（1-5分）")
    grade: CourseGrade = Field(..., description="所属年级：高一/高二/高三")
    teacher_id: int | None = Field(None, description="授课教师ID（可空）")


class CourseSelect(BaseModel):
    """选课请求体。"""

    course_id: int = Field(..., description="要选的课程ID")


class ScoreUpdate(BaseModel):
    """登记成绩请求体。"""

    course_id: int = Field(..., description="课程ID")
    score: float = Field(..., ge=0, le=100, description="成绩：0-100")
