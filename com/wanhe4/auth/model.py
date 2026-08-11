"""认证模块 - 数据访问层：users 表操作 + bcrypt 密码哈希"""
import bcrypt

from com.wanhe4.common.db import Database


def hash_password(password: str) -> str:
    """bcrypt 加密明文密码,返回可入库的 60 字符哈希串"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored: str) -> bool:
    """校验明文是否匹配存储值;存储值非合法 bcrypt 时回退明文比较(兼容历史明文)"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
    except (ValueError, TypeError):
        return password == stored


class User:
    def find_one_byname(self,username):
        db = Database()
        sql = "SELECT * FROM users WHERE username = %s"
        try:
            return db.get_one(sql, (username,))
        finally:
            db.close()

    def create_user(self,username,password,role,student_id=None):
        db = Database()
        sql="INSERT INTO users (username, password, role, student_id) VALUES (%s, %s, %s, %s)"
        try:
            return db.insert(sql, (username, hash_password(password), role, student_id))
        finally:
            db.close()

    def update_password(self, user_id, password):
        """历史明文账号登录成功后原地升级为 bcrypt 哈希"""
        db = Database()
        sql="UPDATE users SET password=%s WHERE id=%s"
        try:
            return db.execute(sql, (hash_password(password), user_id))
        finally:
            db.close()