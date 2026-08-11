# com/wanhe4/classes/vo.py
from pydantic import BaseModel


class ClassCreate(BaseModel):
    id: int
    name: str
    head_teacher_id: int
    count_s: int
    count_t: int
    grade: str


class ClassUpdate(BaseModel):
    name: str
    head_teacher_id: int
    count_s: int
    count_t: int
    grade: str