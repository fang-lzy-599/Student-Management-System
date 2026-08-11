from fastapi import APIRouter, HTTPException
from com.wanhe4.auth.vo import RegisterRequest, LoginRequest
from com.wanhe4.auth.model import User, verify_password
import logging

from com.wanhe4.student.model import StudentModel
from com.wanhe4.common.response import success

router = APIRouter(prefix="/auth", tags=["登陆与注册模块"])

@router.post("/register")
def register(data: RegisterRequest):
    user = User()
    if user.find_one_byname(data.username):
        logging.warning("登录失败，用户:%s 已存在", data.username)
        raise HTTPException(status_code=400, detail="用户名已存在")

    student = StudentModel()
    student_id=student.create(
        name=data.name,
        gender=data.gender,
        age=data.age,
        grade='高一',
        class_id=None,
        teacher_id=None,
        enrollment_date='2025-09-01',
    )

    user.create_user(
        student_id=student_id,
        username=data.username,
        password=data.password,
        role='student',
    )

    logging.info("注册成功，用户:%s",data.username)
    return success({"student_id":student_id,"username":data.username})

@router.post("/login")
def login(data: LoginRequest):
    user=User().find_one_byname(data.username)
    if not user or not verify_password(data.password, user['password']):
        logging.warning("用户:%s,登录失败",data.username)
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    if not user['password'].startswith("$2"):
        User().update_password(user['id'], data.password)
        logging.info("用户:%s 历史明文密码已升级为 bcrypt",data.username)

    logging.info("登录成功，欢迎:%s",data.username)
    return success({"username":user['username'],
                    "role":user['role'],
                    "id":user['id']
                   })
