"""
学生模块 - 数据访问层

职责：封装 students 表及相关联表（classes/teachers/student_course）的 SQL 操作
包含：增删改查、分班、选老师、关键字查询、分页查询、级联删除（逐条执行）
依赖：common.db.Database
"""

from com.wanhe4.common.db import Database


class StudentModel:

    def create(self,name,gender,age,grade,class_id,teacher_id,enrollment_date):
       """
       :param self: 
       :param name: 
       :param gender: 
       :param age: 
       :param grade: 
       :param class_id: 
       :param teacher_id: 
       :param enrollment_date: 
       :return: 新学生自增 ID
       """""
       db = Database()
       try:
            return db.insert(
                "INSERT INTO students(name,gender,age,grade,class_id,teacher_id,enrollment_date) VALUES (%s,%s,%s,%s,%s,%s,%s) ",
                (name,gender,age,grade,class_id,teacher_id,enrollment_date)
            )
       finally:
           db.close()

    def delete(self,student_id):
        """
        删除学生（同时清理其选课记录和账号，逐条执行（级联删除））
        :param student_id:
        :return: 删除的学生行数
        """
        db = Database()
        try:
            db.execute("DELETE FROM student_course WHERE student_id=%s",(student_id,))
            db.execute("DELETE FROM users WHERE student_id=%s",(student_id,))
            return db.execute("DELETE FROM students WHERE id=%s",(student_id,))
        finally:
            db.close()

    def update(self,student_id,name,gender,age,grade):
        """
        修改学生基本信息（姓名/性别/年龄/年级）
        :param student_id:
        :param name:
        :param gender:
        :param age:
        :param grade:
        :return:受影响的行数
        """
        db = Database()
        try:
            return db.execute("UPDATE students SET name=%s, gender=%s, age=%s, grade=%s WHERE id=%s",
                              (name,gender,age,grade,student_id)
            )
        finally:
            db.close()

    def get_by_id(self,student_id):
        """
        按 ID 查询学生（含班级名、教师名）
        :param student_id:
        :return:
        """
        db = Database()
        try:
            return db.query_one(
                "SELECT s.*,c.name AS class_name,t.name AS teacher_name "
                "FROM students s "
                "LEFT JOIN classes c ON s.class_id=c.id "
                "LEFT JOIN teachers t ON s.teacher_id=t.id "
                "WHERE s.id=%s ",(student_id,))
        finally:
            db.close()

    def get_all(self, keyword=''):
        """
        查询所有学生（关联班级名、教师名、选课数），可按姓名模糊查询
        :param keyword: 姓名关键字，可选，不传则查询全部
        :return: 学生列表
        """
        db = Database()
        try:
            # 1. 基础联表SQL
            base_sql = """
                       SELECT s.*,
                              c.name       AS class_name,
                              t.name       AS teacher_name,
                              count(sc.id) AS 选课数
                       FROM students s
                                LEFT JOIN classes c ON s.class_id = c.id
                                LEFT JOIN teachers t ON s.teacher_id = t.id
                                LEFT JOIN student_course sc ON s.id = sc.student_id
                       """
            params = []

            # 2. 有姓名关键字就拼接模糊查询条件
            if keyword:
                base_sql += " WHERE s.name LIKE %s "
                params.append(f"%{keyword}%")

            # 3. 按学生ID分组，保证每个学生对应一条统计结果
            base_sql += " GROUP BY s.id "

            return db.query_all(base_sql, tuple(params))
        finally:
            db.close()

    def change_class(self, student_id, class_id):
        """分班：把学生安排到指定班级"""
        db = Database()
        try:
            return db.execute(
                "UPDATE students SET class_id=%s WHERE id=%s",
                (class_id, student_id)
            )
        finally:
            db.close()

    def change_teacher(self, student_id, teacher_id):
        """选老师：把学生分配给指定教师"""
        db = Database()
        try:
            return db.execute(
                "UPDATE students SET teacher_id=%s WHERE id=%s",
                (teacher_id, student_id)
            )
        finally:
            db.close()

    def get_page(self, page=1, page_size=10, keyword=''):
        """
        分页查询学生列表（含班级名、教师名、选课数），支持关键字模糊搜索
        :param page:      页码，从1开始，默认第1页
        :param page_size: 每页条数，默认10条
        :param keyword:   姓名关键字，可选
        :return: {"total": 总记录数, "items": 当前页数据列表}
        """
        db = Database()
        try:
            offset = (page - 1) * page_size

            # 1. 基础查询（与 get_all 保持一致结构）
            base_sql = """
                       SELECT s.*,
                              c.name        AS class_name,
                              t.name        AS teacher_name,
                              count(sc.id)  AS 选课数
                       FROM students s
                                LEFT JOIN classes c ON s.class_id = c.id
                                LEFT JOIN teachers t ON s.teacher_id = t.id
                                LEFT JOIN student_course sc ON s.id = sc.student_id
                       """
            count_sql = "SELECT count(*) AS total FROM students s"
            params = []

            # 2. 关键字模糊搜索
            if keyword:
                where = " WHERE s.name LIKE %s"
                base_sql += where
                count_sql += where
                params.append(f"%{keyword}%")

            # 3. 分组 + 分页
            base_sql += " GROUP BY s.id LIMIT %s, %s"

            # 4. 分别查总数和当前页
            total_row = db.query_one(count_sql, tuple(params))
            items = db.query_all(base_sql, tuple(params + [offset, page_size]))

            return {
                "total": total_row["total"] if total_row else 0,
                "page": page,
                "page_size": page_size,
                "items": items,
            }
        finally:
            db.close()

    # ==================== 新增功能 ====================

    def batch_delete(self, ids):
        """
        批量删除学生（连同其选课记录和账号，逐条执行）
        :param ids: 学生ID列表，如 [1, 2, 3]
        :return: 总共删除的学生行数
        """
        db = Database()
        try:
            total = 0
            for sid in ids:
                db.execute("DELETE FROM student_course WHERE student_id=%s", (sid,))
                db.execute("DELETE FROM users WHERE student_id=%s", (sid,))
                rows = db.execute("DELETE FROM students WHERE id=%s", (sid,))
                total += rows
            return total
        finally:
            db.close()

    def get_courses(self, student_id):
        """
        查询某个学生的选课详情（课程名、学分、授课教师、成绩）
        :param student_id: 学生ID
        :return: 选课列表，每项包含课程信息和成绩
        """
        db = Database()
        try:
            return db.query_all(
                "SELECT sc.id AS sc_id, c.name AS course_name, c.credit, "
                "t.name AS teacher_name, sc.score "
                "FROM student_course sc "
                "LEFT JOIN courses c ON sc.course_id = c.id "
                "LEFT JOIN teachers t ON c.teacher_id = t.id "
                "WHERE sc.student_id = %s",
                (student_id,)
            )
        finally:
            db.close()






