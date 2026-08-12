import logging
from typing import Optional, List, Dict, Any

from com.wanhe4.common.db import Database

logger = logging.getLogger(__name__)


# =====================================================================
# 班级列表「基础联表 SQL」（公共查询片段，供 get_by_id / get_all 复用）
# =====================================================================
# 查询思路：
#   - 以 classes 表为驱动主表（别名 c），LEFT JOIN 两张关联表：
#       1) teachers t —— 通过 c.head_teacher_id = t.id 带出「班主任姓名」
#       2) students s —— 通过 s.class_id = c.id 统计「班级学生数」
#   - 为什么用 LEFT JOIN 而不是 INNER JOIN？
#       · 班主任可能未设置（head_teacher_id 为 NULL）——LEFT JOIN 保证班级仍能查出，班主任名为 NULL；
#       · 班级可能还没有学生——LEFT JOIN 保证该班仍出现，且 COUNT(s.id) = 0。
#   - COUNT(s.id) 只统计 s.id 非空的记录（即真实存在的学生）；
#   - 后续统一接上 GROUP BY c.id，保证「一个班级一行」的统计粒度；
#   - 所有数据一律来自真实联表，禁止任何写死的班级/学生/教师数据。
# =====================================================================
_CLASS_BASE_SQL = """
    SELECT c.id, c.name, c.grade, c.head_teacher_id, c.create_time,
           t.name        AS head_teacher_name,   -- 班主任姓名（未设置班主任时为 NULL）
           COUNT(s.id)   AS student_count        -- 班级学生数
    FROM classes c
             LEFT JOIN teachers t ON c.head_teacher_id = t.id
             LEFT JOIN students s ON s.class_id = c.id
"""


class ClassModel:
    """
    班级模块 - 数据访问层（Model 层）

    职责：
        封装 classes 表及关联表（teachers / students）的全部 SQL 操作。
        路由层（router.py）只负责 HTTP 请求解析、参数校验与响应封装，不直接触碰 SQL；
        数据访问层负责拼 SQL、绑定参数、执行并返回结果。

    设计约定：
      1. 所有关联查询一律使用 JOIN 联表，返回动态真实数据，杜绝硬编码假数据；
      2. 新增必须用 db.insert()：返回 cursor.lastrowid，即 MySQL 自增生成的「真实班级主键」；
         若误用 db.execute() 只会拿到受影响行数（恒为 1），会导致接口永远返回 id=1 的错误；
      3. 删除 / 清空班级前，先把该班学生的 class_id 置为 NULL（解除关联），
         避免产生「学生指向不存在班级」的脏数据；
      4. 每个方法都遵循「独立连接 + try/finally 关闭」模式：
         无论执行成功还是抛异常，finally 都会调用 db.close() 释放数据库连接，防止连接泄漏。

    依赖：com.wanhe4.common.db.Database
    """

    def get_by_id(self, cid: int) -> Optional[Dict[str, Any]]:
        """
        按班级ID查询单个班级（关联班主任姓名 + 班级学生数）。

        :param cid: 班级ID（主键）
        :return: 班级行 dict，包含 id / name / grade / head_teacher_id / create_time
                 / head_teacher_name / student_count；
                 若班级不存在则返回 None（调用方据此判断 404）。
        :raises: 数据库异常向上抛出，由全局异常处理器统一转为错误响应。
        """
        db = Database()  # 每方法独立创建连接，保证线程安全、无跨请求复用
        try:
            # 复用公共基础 SQL，追加 WHERE 定位单条班级，再按班级分组
            sql = _CLASS_BASE_SQL + " WHERE c.id = %s GROUP BY c.id"
            return db.query_one(sql, (cid,))  # query_one：只取第一行，无结果返回 None
        except Exception as e:
            # 记录日志后原样抛出，交给上层（全局异常处理）统一处理
            logger.error("查询班级异常: %s", e)
            raise
        finally:
            # 无论成功/失败都必须关闭连接，避免连接池泄漏
            db.close()

    def get_all(self, keyword: str = "") -> List[Dict[str, Any]]:
        """
        查询所有班级（关联班主任姓名 + 班级学生数），可按班级名/年级关键字模糊查询。

        :param keyword: 模糊搜索关键字（可选），匹配「班级名称」或「年级」，如"高一"、"1班"；
                        传空字符串则查询全部班级。
        :return: 班级行 dict 列表，按班级ID升序排列。
        """
        db = Database()
        try:
            sql = _CLASS_BASE_SQL
            params = []
            # 有关键字才拼接 WHERE（用 OR 同时匹配班级名与年级两列）
            if keyword.strip():
                sql += " WHERE c.name LIKE %s OR c.grade LIKE %s"
                param = f"%{keyword}%"  # 前后通配符 %xxx% 实现「包含」匹配
                params = [param, param]  # 两个占位符复用同一关键字
            # GROUP BY 保证每班一行（COUNT 统计正确）；ORDER BY 保证列表顺序稳定
            sql += " GROUP BY c.id ORDER BY c.id"
            return db.query_all(sql, tuple(params))
        except Exception as e:
            logger.error("班级列表查询异常: %s", e)
            raise
        finally:
            db.close()

    def teacher_exists(self, teacher_id: Optional[int]) -> bool:
        """
        校验班主任教师是否存在（新增/修改班级时使用）。

        :param teacher_id: 教师ID；None 表示「不设置班主任」，视为合法直接放行
        :return: True = 合法（不存在班主任 / 班主任教师存在）；False = 教师不存在，应拒绝操作
        """
        if teacher_id is None:
            return True  # 未设置班主任是允许的，无需查库
        db = Database()
        try:
            # 只查 id 是否命中，存在即返回该行；query_one 无结果返回 None
            row = db.query_one("SELECT id FROM teachers WHERE id = %s", (teacher_id,))
            return row is not None
        except Exception as e:
            logger.error("校验班主任异常: %s", e)
            raise
        finally:
            db.close()

    def create(self, name: str, head_teacher_id: Optional[int], grade: str) -> int:
        """
        新增班级。

        :param name:             班级名称，如"高一(1)班"
        :param head_teacher_id:  班主任教师ID（可 None）
        :param grade:            年级，如"高一"
        :return: MySQL 自增生成的真实班级主键ID
        """
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
        """
        更新班级信息。

        :param cid:              要更新的班级ID
        :param name:             新的班级名称
        :param head_teacher_id:  新的班主任教师ID（可 None = 移除班主任）
        :param grade:            新的年级
        :return: 受影响行数（正常为 1；0 表示目标班级不存在，由调用方预先校验）
        """
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
        """
        清空指定班级下所有学生（仅解除学生与班级的关联，班级本身保留）。

        场景：班级还在，但要把班内学生全部移出（例如重新分班前先清空）。

        :param cid: 班级ID
        :return: 被处理（解除关联）的学生人数
        """
        db = Database()
        try:
            # 学生 class_id 置 NULL：表示「未分班」，避免残留对班级的引用
            sql = "UPDATE students SET class_id = NULL WHERE class_id = %s"
            return db.execute(sql, (cid,))
        except Exception as e:
            logger.error("清空班级学生异常: %s", e)
            raise
        finally:
            db.close()

    def delete(self, cid: int) -> int:
        """
        删除班级。

        执行顺序（关键）：
          1. 先把该班全部学生的 class_id 置为 NULL —— 解除关联；
          2. 再删除班级记录本身。
        先解除再删除，避免产生「学生指向已删除班级」的脏数据。
        两步都在同一个数据库连接内顺序执行（非显式事务），但解关联操作失败时
        删除不会发生，从而保证不会留下悬空引用。

        :param cid: 班级ID
        :return: 删除的班级行数（1 表示删除成功）
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
        """
        查询指定班级内所有学生（LEFT JOIN teachers 带出选课教师姓名）。

        :param cid: 班级ID
        :return: 学生行 dict 列表，每行含 id / name / gender / age / grade
                 / class_id / teacher_id / enrollment_date / teacher_name；
                 按学生ID升序排列。
        """
        db = Database()
        try:
            sql = """
                SELECT s.id, s.name, s.gender, s.age, s.grade,
                       s.class_id, s.teacher_id, s.enrollment_date,
                       t.name AS teacher_name     -- 该学生选的指导教师姓名（未选则为 NULL）
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
        """
        批量转移学生到目标班级。

        实现：把多个学生ID拼进一条 UPDATE ... WHERE id IN (...) 语句，
              用单条 SQL 原子完成全部转移，避免逐条执行带来的多次网络往返。

        :param student_ids:     要转移的学生ID列表（非空，调用方已校验）
        :param target_class_id: 目标班级ID
        :return: 实际转移成功的学生人数
        """
        db = Database()
        try:
            sid_tuple = tuple(student_ids)
            # 按学生个数动态生成占位符串，如 [1,2,3] -> "%s,%s,%s"
            placeholders = ",".join(["%s"] * len(sid_tuple))
            sql = f"UPDATE students SET class_id=%s WHERE id IN ({placeholders})"
            # 参数顺序：先是目标班级ID，再展开学生ID列表（位置参数与占位符一一对应）
            return db.execute(sql, (target_class_id,) + sid_tuple)
        except Exception as e:
            logger.error("批量移班异常: %s", e)
            raise
        finally:
            db.close()
