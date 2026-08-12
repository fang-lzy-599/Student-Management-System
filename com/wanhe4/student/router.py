import logging

from fastapi import APIRouter,HTTPException

from com.wanhe4.student.model import StudentModel
from com.wanhe4.student.vo import StudentCreate,StudentUpdate, ClassAssign, TeacherAssign, BatchDeleteRequest, CourseSelect
from com.wanhe4.classes.model import ClassModel
from com.wanhe4.teacher.model import TeacherModel
from com.wanhe4.course.model import CourseModel
from com.wanhe4.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由：统一接口前缀、文档标签
router = APIRouter(prefix="/student", tags=["学生模块"])


@router.post("/add")  # 路由装饰器：注册 POST 新增接口
def add_student(data: StudentCreate):
    """增：新增学生（若指定班级，校验年级匹配；若指定教师，校验存在）"""
    # 若指定了班级/教师，先验证存在
    if data.class_id:
        cls_grade = ClassModel().get_grade(data.class_id)
        if cls_grade is None:
            raise HTTPException(status_code=404, detail="班级不存在")
        if cls_grade != data.grade:
            raise HTTPException(status_code=400, detail=f"学生年级({data.grade})与班级年级({cls_grade})不匹配")
    if data.teacher_id and TeacherModel().get_by_id(data.teacher_id) is None:
        raise HTTPException(status_code=404, detail="教师不存在")

    new_id = StudentModel().create(
        name=data.name,
        gender=data.gender,
        age=data.age,
        grade=data.grade,
        class_id=data.class_id,
        teacher_id=data.teacher_id,
        enrollment_date=data.enrollment_date,
    )
    logger.info("新增学生 id:%s 姓名:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")


@router.delete("/del/{student_id}")  # 路由装饰器：注册 DELETE 删除接口
def delete_student(student_id: int):
    """删：删除学生（连带清理选课记录和账号"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    StudentModel().delete(student_id)
    logger.info("删除学生 id:%s", student_id)
    return success(msg="删除成功")


@router.put("/update/{student_id}")  # 路由装饰器：注册 PUT 修改接口
def update_student(student_id: int, data: StudentUpdate):
    """改：修改学生基本信息"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    StudentModel().update(student_id, data.name, data.gender, data.age, data.grade)
    logger.info("修改学生 id:%s", student_id)
    return success(msg="修改成功")


@router.get("/one/{student_id}")  # 路由装饰器：注册 GET 查询接口
def get_student(student_id: int):
    """查：按 ID 获取单个学生"""
    student = StudentModel().get_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return success(student)


@router.get("/all")  # 路由装饰器：注册 GET 查询接口
def list_students(keyword: str = ""):
    """查：获取所有学生（含班级名、教师名、选课数），可按姓名模糊查询"""
    return success(StudentModel().get_all(keyword))


@router.put("/assign-class/{student_id}")  # 路由装饰器：注册 PUT 修改接口
def assign_class(student_id: int, data: ClassAssign):
    """分班：把学生安排到指定班级（校验年级匹配）"""
    student = StudentModel().get_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    cls_grade = ClassModel().get_grade(data.class_id)
    if cls_grade is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if student.get("grade") != cls_grade:
        raise HTTPException(status_code=400, detail=f"学生年级({student.get('grade')})与班级年级({cls_grade})不匹配，不能分班")
    StudentModel().change_class(student_id, data.class_id)
    logger.info("学生分班 id:%s → 班级%s", student_id, data.class_id)
    return success(msg="分班成功")


@router.put("/assign-teacher/{student_id}")  # 路由装饰器：注册 PUT 修改接口
def assign_teacher(student_id: int, data: TeacherAssign):
    """选老师：把学生分配给指定教师"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if TeacherModel().get_by_id(data.teacher_id) is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    StudentModel().change_teacher(student_id, data.teacher_id)
    logger.info("学生选老师 id:%s → 教师%s", student_id, data.teacher_id)
    return success(msg="选老师成功")


@router.get("/page")  # 路由装饰器：注册 GET 查询接口
def list_students_page(page: int = 1, page_size: int = 10, keyword: str = ""):
    """查：学生分页列表，返回 {"total", "items"}，支持关键字查询和翻页"""
    return success(StudentModel().get_page(page, page_size, keyword))


# ==================== 新增功能 ====================

@router.post("/batch-delete")
def batch_delete_students(data: BatchDeleteRequest):
    """批量删除：根据ID列表批量删除学生（连带清理选课记录和账号）"""
    # 校验每个学生是否存在
    not_found = []
    for sid in data.ids:
        if StudentModel().get_by_id(sid) is None:
            not_found.append(sid)
    if not_found:
        raise HTTPException(status_code=404, detail=f"以下学生不存在: {not_found}")

    deleted_count = StudentModel().batch_delete(data.ids)
    logger.info("批量删除学生 ids:%s 共%d条", data.ids, deleted_count)
    return success({"deleted_count": deleted_count}, msg=f"批量删除成功，共删除 {deleted_count} 名学生")


@router.get("/{student_id}/courses")
def get_student_courses(student_id: int):
    """查：获取某个学生的选课详情（课程名、学分、授课教师、成绩）"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    courses = StudentModel().get_courses(student_id)
    return success(courses, msg=f"查询到 {len(courses)} 门课程")


# ==================== 学生选课 ====================

@router.get("/{student_id}/available-courses")
def get_available_courses(student_id: int):
    """查：获取某学生可选的本年级课程（排除已选课程）"""
    student = StudentModel().get_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    courses = StudentModel().get_available_courses(student_id)
    return success(courses, msg=f"可选课程共 {len(courses)} 门")


@router.post("/{student_id}/select-course")
def select_course(student_id: int, data: CourseSelect):
    """选课：学生选一门本年级课程（不可重复选）"""
    student = StudentModel().get_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    course = CourseModel().get_by_id(data.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if student.get("grade") != course.get("grade"):
        raise HTTPException(status_code=400,
                            detail=f"学生年级({student.get('grade')})与课程年级({course.get('grade')})不匹配，不能选课")
    if StudentModel().is_selected(student_id, data.course_id):
        raise HTTPException(status_code=400, detail="该课程已选过，不能重复选")
    StudentModel().select_course(student_id, data.course_id)
    logger.info("学生选课 学生id:%s → 课程%s", student_id, data.course_id)
    return success(msg="选课成功")


@router.delete("/{student_id}/unselect-course")
def unselect_course(student_id: int, data: CourseSelect):
    """退课：学生退选一门已选课程"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if CourseModel().get_by_id(data.course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not StudentModel().is_selected(student_id, data.course_id):
        raise HTTPException(status_code=400, detail="未选该课程，无法退课")
    StudentModel().unselect_course(student_id, data.course_id)
    logger.info("学生退课 学生id:%s 课程%s", student_id, data.course_id)
    return success(msg="退课成功")

