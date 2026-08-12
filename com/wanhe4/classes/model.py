import logging
from typing import Optional, List, Dict, Any

from com.wanhe4.common.db import Database

logger = logging.getLogger(__name__)

# 班级列表基础联表SQL：LEFT JOIN 班主任 + LEFT JOIN 学生统计人数
# 通过 GROUP BY c.id 保证每班一行，且彻底走 JOIN 实现表关联（禁止任何写死数据）
_CLASS_BASE_SQL = """
    SELECT c.id, c.name, c.grade, c.head_teacher_id, c.create_time,
           t.name        AS head_teacher_name,
           COUNT(s.id)   AS student_count
    FROM classes c
             LEFT JOIN teachers t ON c.head_teacher_id = t.id
             LEFT JOIN students s ON s.class_id = c.id
"""


class ClassModel:
    """
    班级模块 - 数据访问层

    职责：封装 classes 表及关联表（teachers / students）的 SQL 操作
    说明：
      - 所有关联查询一律使用 JOIN 联表，返回动态真实数据
      - 新增使用 db.insert()，返回 MySQL 自增的真实班级主键
      - 删除班级前先解除该班学生的班级关联，避免脏数据
    依赖：common.db.Database
    """

    def get_by_id(self, cid: int) -> Optional[Dict[str, Any]]:
        """按班级ID查询单个班级（关联班主任姓名 + 班级学生数）；不存在返回 None"""
        db = Database()
        try:
            sql = _CLASS_BASE_SQL + " WHERE c.id = %s GROUP BY c.id"
            return db.query_one(sql, (cid,))
        except Exception as e:
            logger.error("查询班级异常: %s", e)

    def get_grade(self, cid: int) -> Optional[str]:
        """按班级ID查询班级年级，只查单表无 JOIN，杜绝列名冲突"""
        db = Database()
        try:
            row = db.query_one("SELECT grade FROM classes WHERE id = %s", (cid,))
            return row["grade"] if row else None
        except Exception as e:
            logger.error("查询班级年级异常: %s", e)
            raise
            raise
        finally:
            db.close()

    def get_all(self, keyword: str = "") -> List[Dict[str, Any]]:
        """查询所有班级（关联班主任姓名 + 班级学生数），可按班级名/年级关键字模糊查询"""
        db = Database()
        try:
            sql = _CLASS_BASE_SQL
            params = []
            if keyword.strip():
                sql += " WHERE c.name LIKE %s OR c.grade LIKE %s"
                param = f"%{keyword}%"
                params = [param, param]
            sql += " GROUP BY c.id ORDER BY c.id"
            return db.query_all(sql, tuple(params))
        except Exception as e:
            logger.error("班级列表查询异常: %s", e)
            raise
        finally:
            db.close()

    def teacher_exists(self, teacher_id: Optional[int]) -> bool:
        """校验班主任教师是否存在；teacher_id 为空视为合法（不设班主任）"""
        if teacher_id is None:
            return True
        db = Database()
        try:
            row = db.query_one("SELECT id FROM teachers WHERE id = %s", (teacher_id,))
            return row is not None
        except Exception as e:
            logger.error("校验班主任异常: %s", e)
            raise
        finally:
            db.close()

    def create(self, name: str, head_teacher_id: Optional[int], grade: str) -> int:
        """新增班级；返回 MySQL 自增生成的真实班级主键ID"""
        db = Database()
        try:
            sql = """
                INSERT INTO classes(name, head_teacher_id, grade)
                VALUES (%s, %s, %s)
            """
            # 必须用 db.insert()：返回 cursor.lastrowid（真实自增ID）
            # 用 db.execute() 只会拿到受影响行数(恒为1)，导致接口永远返回 id=1
            return db.insert(sql, (name, head_teacher_id, grade))
        except Exception as e:
            logger.error("新增班级异常: %s", e)
            raise
        finally:
            db.close()

    def update(self, cid: int, name: str, head_teacher_id: Optional[int], grade: str):
        """更新班级信息"""
        db = Database()
        try:
            sql = """
                UPDATE classes
                SET name=%s, head_teacher_id=%s, grade=%s
                WHERE id=%s
            """
            db.execute(sql, (name, head_teacher_id, grade, cid))
        except Exception as e:
            logger.error("修改班级异常: %s", e)
            raise
        finally:
            db.close()

    def clear_students(self, cid: int) -> int:
        """清空指定班级下所有学生（学生 class_id 置 NULL，解除班级关联）；返回处理人数"""
        db = Database()
        try:
            sql = "UPDATE students SET class_id = NULL WHERE class_id = %s"
            return db.execute(sql, (cid,))
        except Exception as e:
            logger.error("清空班级学生异常: %s", e)
            raise
        finally:
            db.close()

    def delete(self, cid: int) -> int:
        """
        删除班级：先解除该班全部学生的 class_id 关联，再删除班级本身，
        避免产生学生指向不存在班级的脏数据
        """
        db = Database()
        try:
            db.execute("UPDATE students SET class_id = NULL WHERE class_id = %s", (cid,))
            return db.execute("DELETE FROM classes WHERE id = %s", (cid,))
        except Exception as e:
            logger.error("删除班级异常: %s", e)
            raise
        finally:
            db.close()

    def get_students(self, cid: int) -> List[Dict[str, Any]]:
        """查询指定班级内所有学生（LEFT JOIN teachers 带出选课教师姓名）"""
        db = Database()
        try:
            sql = """
                SELECT s.id, s.name, s.gender, s.age, s.grade,
                       s.class_id, s.teacher_id, s.enrollment_date,
                       t.name AS teacher_name
                FROM students s
                         LEFT JOIN teachers t ON s.teacher_id = t.id
                WHERE s.class_id = %s
                ORDER BY s.id
            """
            return db.query_all(sql, (cid,))
        except Exception as e:
            logger.error("查询班级学生异常: %s", e)
            raise
        finally:
            db.close()

    def move_students(self, student_ids: List[int], target_class_id: int) -> int:
        """批量转移学生到目标班级（单条 UPDATE ... IN，原子执行）；返回转移人数"""
        db = Database()
        try:
            sid_tuple = tuple(student_ids)
            placeholders = ",".join(["%s"] * len(sid_tuple))
            sql = f"UPDATE students SET class_id=%s WHERE id IN ({placeholders})"
            return db.execute(sql, (target_class_id,) + sid_tuple)
        except Exception as e:
            logger.error("批量移班异常: %s", e)
            raise
        finally:
            db.close()
