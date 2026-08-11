import logging
from typing import Optional, List, Dict, Any
from com.wanhe4.common.db import Database

logger = logging.getLogger(__name__)


class ClassModel:
    def __init__(self):
        pass

    def get_by_id(self, cid: int) -> Optional[Dict[str, Any]]:
        """根据班级ID查询单个班级"""
        db = Database()
        try:
            sql = """
                SELECT id, name, grade, head_teacher_id, create_time
                FROM classes WHERE id = %s
            """
            return db.query_one(sql, (cid,))
        except Exception as e:
            logger.error("查询班级异常: %s", e)
            raise
        finally:
            db.close()

    def get_all(self, keyword: str = "") -> List[Dict[str, Any]]:
        """关键字模糊查询所有班级（关联查询班主任姓名）"""
        db = Database()
        try:
            base_sql = """
                SELECT c.id, c.name, c.grade, c.head_teacher_id, c.create_time,
                       t.name AS head_teacher_name
                FROM classes c
                LEFT JOIN teachers t ON c.head_teacher_id = t.id
            """
            if keyword.strip():
                sql = base_sql + " WHERE c.name LIKE %s OR c.grade LIKE %s"
                param = f"%{keyword}%"
                return db.query_all(sql, (param, param))
            else:
                return db.query_all(base_sql)
        except Exception as e:
            logger.error("班级列表查询异常: %s", e)
            raise
        finally:
            db.close()

    def create(self, name: str, head_teacher_id: Optional[int], grade: str) -> int:
        """新增班级，数据库自增主键"""
        db = Database()
        try:
            sql = """
                INSERT INTO classes(name, head_teacher_id, grade)
                VALUES (%s, %s, %s)
            """
            params = (name, head_teacher_id, grade)
            insert_id = db.execute(sql, params)
            return insert_id
        except Exception as e:
            logger.error("新增班级异常: %s", e)
            raise
        finally:
            db.close()

    def update(self, cid: int, name: str, head_teacher_id: Optional[int], grade: str):
        """更新班级"""
        db = Database()
        try:
            sql = """
                UPDATE classes
                SET name=%s, head_teacher_id=%s, grade=%s
                WHERE id=%s
            """
            params = (name, head_teacher_id, grade, cid)
            db.execute(sql, params)
        except Exception as e:
            logger.error("修改班级异常: %s", e)
            raise
        finally:
            db.close()

    def delete(self, cid: int):
        """删除班级"""
        db = Database()
        try:
            sql = "DELETE FROM classes WHERE id = %s"
            db.execute(sql, (cid,))
        except Exception as e:
            logger.error("删除班级异常: %s", e)
            raise
        finally:
            db.close()