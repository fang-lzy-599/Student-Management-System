"""
班级模块 - 路由层

职责：
    定义 /classes 前缀下的全部 HTTP 端点（增删改查 + 清空班级 + 批量移班），
    统一执行「参数/存在性校验 → 委托 ClassModel → 返回统一成功响应」。

分层说明：
    - 路由层（本文件）：只做 HTTP 解析、业务校验、日志记录、响应封装；
    - 数据访问层（model.py）：负责全部 SQL 与数据库连接，路由层不直接触碰 Database；
    - 请求体（vo.py）：使用 Pydantic 模型自动完成类型转换、必填/长度校验，
      校验不通过时由 FastAPI 自动返回 422。

校验与响应约定：
    - 资源不存在（班级/教师）        -> HTTP 404
    - 请求参数不合法（如空列表）      -> HTTP 400
    - 校验通过后统一 success() 包装   -> {"code": 0, "msg": "...", "data": ...}
      前端以 code == 0 判定成功。
"""
import logging

from fastapi import APIRouter, HTTPException

from com.wanhe4.classes.model import ClassModel
from com.wanhe4.classes.vo import ClassCreate, ClassUpdate, MoveStudentVO
from com.wanhe4.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由：统一接口前缀（/classes）与文档标签（Swagger 分组）
router = APIRouter(prefix="/classes", tags=["班级模块"])

# 模块级单例 Model 实例（路由只依赖这一实例，不重复创建连接/对象）
_model = ClassModel()


# ---------------------------------------------------------------------
# 查：班级列表
# ---------------------------------------------------------------------
@router.get("/all")
def list_classes(keyword: str = ""):
    """
    获取所有班级（含班主任姓名、班级学生数）。

    :param keyword: 查询字符串参数，可选；按「班级名称 / 年级」模糊匹配，如 ?keyword=高一
    :return: success(data=班级列表)
    """
    return success(_model.get_all(keyword))


# ---------------------------------------------------------------------
# 查：单个班级详情
# ---------------------------------------------------------------------
@router.get("/one/{class_id}")
def get_class(class_id: int):
    """
    按 ID 获取单个班级（含班主任姓名、班级学生数）。

    :param class_id: 路径参数，班级ID
    :raises HTTPException 404: 班级不存在
    :return: success(data=班级行)
    """
    cls = _model.get_by_id(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(cls)


# ---------------------------------------------------------------------
# 增：新增班级
# ---------------------------------------------------------------------
@router.post("/add")
def add_class(data: ClassCreate):
    """
    新增班级（校验班主任教师存在；返回数据库自增的真实班级ID）。

    流程：
      1. 若传了班主任，先校验该教师存在（不存在 -> 404）；
      2. 调 model.create() 写入，拿到自增主键；
      3. 记录日志并返回 {"code":0, "data":{"id": 新班级ID}}。

    :param data: 请求体 JSON，如 {"name": "高一(3)班", "grade": "高一", "head_teacher_id": 1}
    :raises HTTPException 404: 班主任教师不存在
    :return: success(data={"id": new_id}, msg="新增成功")
    """
    # 校验班主任教师合法性（None 表示不设置班主任，天然合法）
    if not _model.teacher_exists(data.head_teacher_id):
        raise HTTPException(status_code=404, detail="班主任教师不存在")

    new_id = _model.create(
        name=data.name,
        head_teacher_id=data.head_teacher_id,
        grade=data.grade
    )
    logger.info("新增班级 id:%s 名称:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")


# ---------------------------------------------------------------------
# 改：修改班级
# ---------------------------------------------------------------------
@router.put("/update/{class_id}")
def update_class(class_id: int, data: ClassUpdate):
    """
    修改班级信息（校验班级存在 + 班主任教师存在）。

    流程：
      1. 班级必须存在（不存在 -> 404）；
      2. 新的班主任教师必须存在（不存在 -> 404）；
      3. model.update() 执行 UPDATE。

    :param class_id: 路径参数，班级ID
    :param data: 请求体 JSON（含新的名称/年级/班主任）
    :raises HTTPException 404: 班级不存在 / 班主任教师不存在
    :return: success(msg="修改成功")
    """
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


# ---------------------------------------------------------------------
# 删：删除班级
# ---------------------------------------------------------------------
@router.delete("/del/{class_id}")
def delete_class(class_id: int):
    """
    删除班级（自动解除该班学生关联，避免脏数据）。

    说明：model.delete() 内部会先将该班学生 class_id 置 NULL，再删除班级记录，
          因此学生不会残留指向已删除班级的引用。

    :param class_id: 路径参数，班级ID
    :raises HTTPException 404: 班级不存在
    :return: success(msg="删除成功")
    """
    if _model.get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    _model.delete(class_id)
    logger.info("删除班级 id:%s", class_id)
    return success(msg="删除成功")


# ---------------------------------------------------------------------
# 清空班级（班级保留，仅解除学生关联）
# ---------------------------------------------------------------------
@router.post("/clear_students/{class_id}")
def clear_class_students(class_id: int):
    """
    清空指定班级下所有学生（学生 class_id 置空，班级本身保留）。

    :param class_id: 路径参数，班级ID
    :raises HTTPException 404: 班级不存在
    :return: success(msg=f"已清空班级下所有学生，共计{affected}人")
    """
    if _model.get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")

    affected = _model.clear_students(class_id)
    logger.info("清空班级%s学生，共处理%s人", class_id, affected)
    return success(msg=f"已清空班级下所有学生，共计{affected}人")


# ---------------------------------------------------------------------
# 查：班级内学生列表
# ---------------------------------------------------------------------
@router.get("/{class_id}/students")
def get_class_students(class_id: int):
    """
    获取指定班级内所有学生（JOIN 带出选课教师姓名）。

    注意：该路由声明在 /move_students 之前，路径两段式（/{id}/students），
          与单段路径（/all、/add 等）互不冲突；FastAPI 按注册顺序匹配。

    :param class_id: 路径参数，班级ID
    :raises HTTPException 404: 班级不存在
    :return: success(data=学生列表)
    """
    if _model.get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")

    student_list = _model.get_students(class_id)
    logger.info("查询班级%s学生，共%s人", class_id, len(student_list))
    return success(data=student_list)


# ---------------------------------------------------------------------
# 批量转移学生到目标班级
# ---------------------------------------------------------------------
@router.post("/move_students")
def move_students(data: MoveStudentVO):
    """
    批量转移学生到目标班级（校验目标班级存在）。

    :param data: 请求体 JSON，如 {"student_ids": [1, 2, 3], "target_class_id": 2}
    :raises HTTPException 404: 目标班级不存在
    :raises HTTPException 400: 学生ID列表不能为空
    :return: success(msg=f"成功转移{affected}名学生")
    """
    if _model.get_by_id(data.target_class_id) is None:
        raise HTTPException(status_code=404, detail="目标班级不存在")
    if not data.student_ids:
        raise HTTPException(status_code=400, detail="学生ID列表不能为空")

    affected = _model.move_students(data.student_ids, data.target_class_id)
    logger.info("批量移班：学生%s 移入班级%s，共%d人", data.student_ids, data.target_class_id, affected)
    return success(msg=f"成功转移{affected}名学生")
