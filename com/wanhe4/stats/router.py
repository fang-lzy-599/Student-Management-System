from fastapi import APIRouter, HTTPException
from com.wanhe4.stats.model import StatsModel
from com.wanhe4.common.response import success
import logging


router = APIRouter(prefix="/stats", tags=["信息总览"])

@router.get("/class-count")
def class_count():
    logging.info("班级人数统计")
    return success({"items": StatsModel().class_count()})


@router.get("/grade-count")
def grade_count():
    logging.info("年级人数统计")
    return success({"items": StatsModel().grade_distribution()})


@router.get("/stu-gender-ratio")
def stu_gender_ratio():
    logging.info("学生性别比例分析")
    return success({"items": StatsModel().stu_gender_part()})


@router.get("/tea-gender-ratio")
def tea_gender_ratio():
    logging.info("老师性别比例分析")
    return success({"items": StatsModel().tea_gender_part()})


@router.get("/course-avg")
def course_avg():
    logging.info("各课程成绩平均分与及格率")
    return success({"items": StatsModel().get_avg()})

@router.get("/student-count")
def student_count():
    logging.info("在校学生总数统计")
    return success({"items": StatsModel().count_all_students()})

@router.get("/teacher-count")
def teacher_count():
    logging.info("在校老师总数统计")
    return success({"items": StatsModel().count_all_teachers()})

@router.get("/class-count-total")
def class_count_total():
    logging.info("班级总数统计")
    return success({"items": StatsModel().count_all_classes()})