import os
from importlib import reload

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# 导入各业务模块子路由（每个模块一个 APIRouter）
from com.wanhe4.auth.router import router as auth_router
from com.wanhe4.student.router import router as student_router
from com.wanhe4.teacher.router import router as teacher_router
from com.wanhe4.course.router import router as course_router
from com.wanhe4.classes.router import router as classes_router
from com.wanhe4.stats.router import router as stats_router

# 导入公共模块（日志配置需在启动时加载，供各业务模块 logger 使用）
import com.wanhe4.common.logging
from com.wanhe4.common.exceptions import register_exception_handlers

app = FastAPI(
    title="Student Management System",
    description="学生/教师管理、选课选老师、分班、注册登录一体化 API",
    version="1.0",
)

# 项目根目录（挂载静态页用绝对路径，避免切换目录找不到）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 挂载静态页面（登录/注册/管理后台，由后端直接提供）
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# 注册全局异常处理（统一错误返回格式 {code, msg, data}）
register_exception_handlers(app)

# 挂载所有模块化路由
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(course_router)
app.include_router(classes_router)
app.include_router(stats_router)

# 根路径：重定向到登录页面
@app.get("/")
def root():
    return RedirectResponse(url="/static/login.html")


#本地直接运行入口（Windows 开发环境热重载）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000,reload=True)




