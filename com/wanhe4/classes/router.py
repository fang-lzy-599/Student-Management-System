import logging
from typing import Optional
from fastapi import APIRouter, HTTPException

from com.wanhe4.classes.model import ClassModel
from com.wanhe4.classes.vo import ClassCreate, ClassUpdate, MoveStudentVO
from com.wanhe4.common.db import Database
from com.wanhe4.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由
router = APIRouter(prefix="/classes", tags=["班级模块"])


def _teacher_exists(teacher_id: Optional[int]) -> bool:
    """校验班主任教师是否存在"""
    if teacher_id is None:
        return True
    db = Database()
    try:
        row = db.query_one("SELECT id FROM teachers WHERE id = %s", (teacher_id,))
        return row is not None
    finally:
        db.close()


@router.get("/all")
def list_classes(keyword: str = ""):
    """查：获取所有班级（含班主任姓名），可按班级名模糊查询"""
    return success(ClassModel().get_all(keyword))


@router.get("/one/{class_id}")
def get_class(class_id: int):
    """查：按 ID 获取单个班级"""
    cls = ClassModel().get_by_id(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(cls)


@router.post("/add")
def add_class(data: ClassCreate):
    """增：新增班级（若指定班主任，先验证教师存在）"""
    # 校验班主任
    if not _teacher_exists(data.head_teacher_id):
        raise HTTPException(status_code=404, detail="班主任教师不存在")

    new_id = ClassModel().create(
        name=data.name,
        head_teacher_id=data.head_teacher_id,
        grade=data.grade
    )
    logger.info("新增班级 id:%s 名称:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")


@router.put("/update/{class_id}")
def update_class(class_id: int, data: ClassUpdate):
    """改：修改班级信息"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if not _teacher_exists(data.head_teacher_id):
        raise HTTPException(status_code=404, detail="班主任教师不存在")

    ClassModel().update(
        cid=class_id,
        name=data.name,
        head_teacher_id=data.head_teacher_id,
        grade=data.grade
    )
    logger.info("修改班级 id:%s", class_id)
    return success(msg="修改成功")


@router.delete("/del/{class_id}")
def delete_class(class_id: int):
    """删：删除班级"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    ClassModel().delete(class_id)
    logger.info("删除班级 id:%s", class_id)
    return success(msg="删除成功")


@router.post("/clear_students/{class_id}")
def clear_class_students(class_id: int):
    """
    清空指定班级下所有学生（学生class_id置空）
    """
    # 校验班级是否存在
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")

    db = Database()
    try:
        sql = "UPDATE students SET class_id = NULL WHERE class_id = %s"
        affected = db.execute(sql, (class_id,))
        logger.info("清空班级%s学生，共处理%s人", class_id, affected)
    except Exception as e:
        logger.error("清空班级学生异常：%s", e)
        raise HTTPException(status_code=500, detail="操作失败")
    finally:
        db.close()

    return success(msg=f"已清空班级下所有学生，共计{affected}人")


# ============ 新增接口 1：查询班级内学生 ============
@router.get("/{class_id}/students")
def get_class_students(class_id: int):
    """获取指定班级内所有学生"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")

    db = Database()
    try:
        sql = "SELECT * FROM students WHERE class_id = %s"
        student_list = db.query_all(sql, (class_id,))
    except Exception as e:
        logger.error("查询班级学生异常：%s", e)
        raise HTTPException(status_code=500, detail="查询失败")
    finally:
        db.close()
    return success(data=student_list)


# ============ 新增接口 2：批量转移学生 ============
@router.post("/move_students")
def move_students(data: MoveStudentVO):
    """批量转移学生到目标班级"""
    if ClassModel().get_by_id(data.target_class_id) is None:
        raise HTTPException(status_code=404, detail="目标班级不存在")
    if not data.student_ids:
        raise HTTPException(status_code=400, detail="学生ID列表不能为空")

    db = Database()
    try:
        db.conn.autocommit(False)
        sid_tuple = tuple(data.student_ids)
        placeholders = ",".join(["%s"] * len(sid_tuple))
        sql = f"UPDATE students SET class_id=%s WHERE id IN ({placeholders})"
        params = [data.target_class_id] + list(sid_tuple)
        affected = db.execute(sql, params)
        db.conn.commit()
        logger.info("批量移班：学生%s 移入班级%s，共%d人", data.student_ids, data.target_class_id, affected)
    except Exception as e:
        db.conn.rollback()
        logger.error("批量移班失败：%s", e)
        raise HTTPException(status_code=500, detail="移班失败，操作已回滚")
    finally:
        db.close()

    return success(msg=f"成功转移{affected}名学生")