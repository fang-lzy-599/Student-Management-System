import logging

from fastapi import APIRouter, HTTPException

from com.wanhe4.common.response import success
from com.wanhe4.course.model import CourseModel, StudentCourseModel
from com.wanhe4.course.vo import CourseCreate, CourseSelect, CourseUpdate, ScoreUpdate
from com.wanhe4.student.model import StudentModel
from com.wanhe4.teacher.model import TeacherModel


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["课程模块"])


def _validate_student_course_grade(student, course):
    """学生只能选择自己年级对应的课程。"""
    if student.get("grade") != course.get("grade"):
        raise HTTPException(status_code=400, detail="该学生只能选择本年级课程")


# ---------- 课程管理 ----------

@router.get("/all")
def list_courses(keyword: str = ""):
    """查：获取所有课程（含授课教师名、选课人数），可按课程名模糊查询。"""
    return success(CourseModel().get_all(keyword))


@router.get("/one/{course_id}")
def get_course(course_id: int):
    """查：按 ID 获取单个课程。"""
    course = CourseModel().get_by_id(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return success(course)


@router.post("/add")
def add_course(data: CourseCreate):
    """增：新增课程。"""
    if data.teacher_id and TeacherModel().get_by_id(data.teacher_id) is None:
        raise HTTPException(status_code=404, detail="授课教师不存在")
    new_id = CourseModel().create(data.name, data.credit, data.grade, data.teacher_id)
    logger.info(
        "新增课程 id:%s 名称:%s 学分:%s 年级:%s",
        new_id, data.name, data.credit, data.grade
    )
    return success({"id": new_id}, msg="新增成功")


@router.put("/update/{course_id}")
def update_course(course_id: int, data: CourseUpdate):
    """改：修改课程。"""
    if CourseModel().get_by_id(course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if data.teacher_id and TeacherModel().get_by_id(data.teacher_id) is None:
        raise HTTPException(status_code=404, detail="授课教师不存在")
    if CourseModel().has_selected_students_outside_grade(course_id, data.grade):
        raise HTTPException(status_code=400, detail="该课程已有其他年级学生选课，不能修改为该年级")
    CourseModel().update(course_id, data.name, data.credit, data.grade, data.teacher_id)
    logger.info("修改课程 id:%s 学分:%s 年级:%s", course_id, data.credit, data.grade)
    return success(msg="修改成功")


@router.delete("/del/{course_id}")
def delete_course(course_id: int):
    """删：删除课程（连带清理选课记录）。"""
    if CourseModel().get_by_id(course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    CourseModel().delete(course_id)
    logger.info("删除课程 id:%s", course_id)
    return success(msg="删除成功")


# ---------- 学生选课 ----------

@router.get("/student/{student_id}")
def get_student_courses(student_id: int):
    """查：查询某学生已选的课程。"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return success(StudentCourseModel().get_courses_by_student(student_id))


@router.get("/available/{student_id}")
def get_available_courses(student_id: int):
    """查：查询某学生可以选择的本年级课程（排除已选课程）。"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return success(CourseModel().get_available_by_student(student_id))


@router.get("/{course_id}/students")
def get_course_students(course_id: int):
    """查：查询某门课程的全部已选学生及成绩。"""
    if CourseModel().get_by_id(course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return success(StudentCourseModel().get_students_by_course(course_id))


@router.post("/select/{student_id}")
def select_course(student_id: int, data: CourseSelect):
    """选课：学生选一门课程，不能重复选，且只能选本年级课程。"""
    student = StudentModel().get_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    course = CourseModel().get_by_id(data.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _validate_student_course_grade(student, course)
    if StudentCourseModel().is_selected(student_id, data.course_id):
        raise HTTPException(status_code=400, detail="该课程已选过，不能重复选")
    StudentCourseModel().select(student_id, data.course_id)
    logger.info("学生选课 学生id:%s -> 课程%s", student_id, data.course_id)
    return success(msg="选课成功")


@router.delete("/unselect/{student_id}")
def unselect_course(student_id: int, data: CourseSelect):
    """退课：学生退掉一门课程。"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if CourseModel().get_by_id(data.course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not StudentCourseModel().is_selected(student_id, data.course_id):
        raise HTTPException(status_code=400, detail="未选该课程，无法退课")
    StudentCourseModel().unselect(student_id, data.course_id)
    logger.info("学生退课 学生id:%s 课程%s", student_id, data.course_id)
    return success(msg="退课成功")


@router.put("/score/{student_id}")
def set_score(student_id: int, data: ScoreUpdate):
    """成绩：为某学生的某门课登记成绩。"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if CourseModel().get_by_id(data.course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not StudentCourseModel().is_selected(student_id, data.course_id):
        raise HTTPException(status_code=400, detail="该学生未选此课程")
    StudentCourseModel().set_score(student_id, data.course_id, data.score)
    logger.info("成绩登记 学生id:%s 课程%s 成绩%s", student_id, data.course_id, data.score)
    return success(msg="成绩登记成功")
