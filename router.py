import logging
from fastapi import APIRouter, HTTPException
from com.wanhe4.classes.model import ClassInfo
from com.wanhe4.classes.vo import ClassCreate, ClassUpdate
from com.wanhe4.common.db import get_db_conn
from com.wanhe4.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由
router = APIRouter(prefix="/classes", tags=["班级模块"])


def _teacher_exists(teacher_id: int) -> bool:
    """
    校验班主任教师是否存在
    说明：teacher 模块尚未就绪，此处直接在数据层校验，避免跨模块依赖
    """
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM teachers WHERE id = %s", (teacher_id,))
        row = cur.fetchone()
        return row is not None
    finally:
        cur.close()
        conn.close()


@router.get("/all")  # 路由装饰器：注册 GET 查询接口
def list_classes(keyword: str = ""):
    """查：获取所有班级（含班主任姓名），可按班级名模糊查询"""
    return success(ClassInfo().get_all(keyword))


@router.get("/one/{class_id}")  # 路由装饰器：注册 GET 查询接口
def get_class(class_id: int):
    """查：按 ID 获取单个班级"""
    cls = ClassInfo().get_by_id(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(cls)


@router.post("/add")  # 路由装饰器：注册 POST 新增接口
def add_class(data: ClassCreate):
    """增：新增班级（若指定班主任，先验证教师存在）"""
    # 校验班主任是否存在
    if data.head_teacher_id and not _teacher_exists(data.head_teacher_id):
        raise HTTPException(status_code=404, detail="班主任教师不存在")
    # 校验班级ID不能重复
    if ClassInfo().get_by_id(data.id) is not None:
        raise HTTPException(status_code=400, detail="班级ID已存在，不可重复创建")

    # 补齐全部6个字段：id,name,head_teacher_id,count_s,count_t,grade
    new_id = ClassInfo().create(
        cid=data.id,
        name=data.name,
        head_teacher_id=data.head_teacher_id,
        count_s=data.count_s,
        count_t=data.count_t,
        grade=data.grade
    )
    logger.info("新增班级 id:%s 名称:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")


@router.put("/update/{class_id}")  # 路由装饰器：注册 PUT 修改接口
def update_class(class_id: int, data: ClassUpdate):
    """改：修改班级信息"""
    if ClassInfo().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if data.head_teacher_id and not _teacher_exists(data.head_teacher_id):
        raise HTTPException(status_code=404, detail="班主任教师不存在")

    ClassInfo().update(
        cid=class_id,
        name=data.name,
        head_teacher_id=data.head_teacher_id,
        count_s=data.count_s,
        count_t=data.count_t,
        grade=data.grade
    )
    logger.info("修改班级 id:%s", class_id)
    return success(msg="修改成功")


@router.delete("/del/{class_id}")  # 路由装饰器：注册 DELETE 删除接口
def delete_class(class_id: int):
    """删：删除班级"""
    if ClassInfo().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    ClassInfo().delete(class_id)
    logger.info("删除班级 id:%s", class_id)
    return success(msg="删除成功")