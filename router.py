"""
班级模块 - 路由层

职责：定义 /classes 前缀下端点，存在性/参数校验后统一委托 ClassModel
说明：
  - 所有 SQL 均收敛到 model.py，路由层不再直接触碰 Database
  - 新增/修改班级前校验班主任教师ID合法性
  - 删除班级前由 model 自动解除学生关联，避免脏数据
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from com.wanhe4.classes.model import ClassModel
from com.wanhe4.classes.vo import ClassCreate, ClassUpdate, MoveStudentVO
from com.wanhe4.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由
router = APIRouter(prefix="/classes", tags=["班级模块"])

_model = ClassModel()


@router.get("/all")
def list_classes(keyword: str = ""):
    """查：获取所有班级（含班主任姓名、班级学生数），可按班级名/年级关键字模糊查询"""
    return success(_model.get_all(keyword))


@router.get("/one/{class_id}")
def get_class(class_id: int):
    """查：按 ID 获取单个班级（含班主任姓名、班级学生数）"""
    cls = _model.get_by_id(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(cls)


@router.post("/add")
def add_class(data: ClassCreate):
    """增：新增班级（校验班主任教师存在；返回数据库自增的真实班级ID）"""
    if not _model.teacher_exists(data.head_teacher_id):
        raise HTTPException(status_code=404, detail="班主任教师不存在")

    new_id = _model.create(
        name=data.name,
        head_teacher_id=data.head_teacher_id,
        grade=data.grade
    )
    logger.info("新增班级 id:%s 名称:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")


@router.put("/update/{class_id}")
def update_class(class_id: int, data: ClassUpdate):
    """改：修改班级信息（校验班级存在 + 班主任教师存在）"""
    if _model.get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if not _model.teacher_exists(data.head_teacher_id):
        raise HTTPException(status_code=404, detail="班主任教师不存在")

    _model.update(
        cid=class_id,
        name=data.name,
        head_teacher_id=data.head_teacher_id,
        grade=data.grade
    )
    logger.info("修改班级 id:%s", class_id)
    return success(msg="修改成功")


@router.delete("/del/{class_id}")
def delete_class(class_id: int):
    """删：删除班级（自动解除该班学生关联，避免脏数据）"""
    if _model.get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    _model.delete(class_id)
    logger.info("删除班级 id:%s", class_id)
    return success(msg="删除成功")


@router.post("/clear_students/{class_id}")
def clear_class_students(class_id: int):
    """清空指定班级下所有学生（学生 class_id 置空，班级本身保留）"""
    if _model.get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")

    affected = _model.clear_students(class_id)
    logger.info("清空班级%s学生，共处理%s人", class_id, affected)
    return success(msg=f"已清空班级下所有学生，共计{affected}人")


@router.get("/{class_id}/students")
def get_class_students(class_id: int):
    """查：获取指定班级内所有学生（JOIN 带出选课教师姓名）"""
    if _model.get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")

    student_list = _model.get_students(class_id)
    logger.info("查询班级%s学生，共%s人", class_id, len(student_list))
    return success(data=student_list)


@router.post("/move_students")
def move_students(data: MoveStudentVO):
    """批量转移学生到目标班级（校验目标班级存在）"""
    if _model.get_by_id(data.target_class_id) is None:
        raise HTTPException(status_code=404, detail="目标班级不存在")
    if not data.student_ids:
        raise HTTPException(status_code=400, detail="学生ID列表不能为空")

    affected = _model.move_students(data.student_ids, data.target_class_id)
    logger.info("批量移班：学生%s 移入班级%s，共%d人", data.student_ids, data.target_class_id, affected)
    return success(msg=f"成功转移{affected}名学生")
