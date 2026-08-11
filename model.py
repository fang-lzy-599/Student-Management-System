# com/wanhe4/classes/model.py
import pymysql
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# 建议：数据库连接抽离到 common.db，这里先预留兼容
def get_db_conn():
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="123456",
        database="shool_db",
        charset="utf8mb4"
    )
    # 设置返回字典格式，替代元组
    conn.cursor = pymysql.cursors.DictCursor
    return conn


class ClassInfo:
    def __init__(self, id=None, name=None, head_teacher_id=None, count_s=None, count_t=None, grade=None):
        self.id = id
        self.name = name
        self.head_teacher_id = head_teacher_id
        self.count_s = count_s
        self.count_t = count_t
        self.grade = grade

    def get_by_id(self, cid: int) -> Optional[Dict[str, Any]]:
        """根据班级ID查询单个班级"""
        conn = get_db_conn()
        cur = conn.cursor()
        try:
            sql = """
                SELECT id, name, head_teacher_id, count_s, count_t, grade
                FROM Class WHERE id = %s
            """
            cur.execute(sql, (cid,))
            return cur.fetchone()
        except Exception as e:
            logger.error("查询班级异常: %s", e)
            raise
        finally:
            cur.close()
            conn.close()

    def get_all(self, keyword: str = "") -> List[Dict[str, Any]]:
        """关键字模糊查询所有班级"""
        conn = get_db_conn()
        cur = conn.cursor()
        try:
            if keyword.strip():
                sql = """
                    SELECT id, name, head_teacher_id, count_s, count_t, grade
                    FROM Class
                    WHERE name LIKE %s OR grade LIKE %s
                """
                param = f"%{keyword}%"
                cur.execute(sql, (param, param))
            else:
                sql = """
                    SELECT id, name, head_teacher_id, count_s, count_t, grade
                    FROM Class
                """
                cur.execute(sql)
            return cur.fetchall()
        except Exception as e:
            logger.error("班级列表查询异常: %s", e)
            raise
        finally:
            cur.close()
            conn.close()

    def create(self, cid: int, name: str, head_teacher_id: Optional[int],
               count_s: int, count_t: int, grade: str) -> int:
        """新增班级"""
        conn = get_db_conn()
        cur = conn.cursor()
        try:
            sql = """
                INSERT INTO Class(id, name, head_teacher_id, count_s, count_t, grade)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (cid, name, head_teacher_id, count_s, count_t, grade)
            cur.execute(sql, params)
            conn.commit()
            return cid
        except Exception as e:
            conn.rollback()
            logger.error("新增班级异常: %s", e)
            raise
        finally:
            cur.close()
            conn.close()

    def update(self, cid: int, name: str, head_teacher_id: Optional[int],
               count_s: int, count_t: int, grade: str):
        """更新班级"""
        conn = get_db_conn()
        cur = conn.cursor()
        try:
            sql = """
                UPDATE Class
                SET name=%s, head_teacher_id=%s, count_s=%s, count_t=%s, grade=%s
                WHERE id=%s
            """
            params = (name, head_teacher_id, count_s, count_t, grade, cid)
            cur.execute(sql, params)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("修改班级异常: %s", e)
            raise
        finally:
            cur.close()
            conn.close()

    def delete(self, cid: int):
        """删除班级"""
        conn = get_db_conn()
        cur = conn.cursor()
        try:
            sql = "DELETE FROM Class WHERE id = %s"
            cur.execute(sql, (cid,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("删除班级异常: %s", e)
            raise
        finally:
            cur.close()
            conn.close()