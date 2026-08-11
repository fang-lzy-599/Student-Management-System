# 文件名：course/model.py
"""
课程模块 - 数据访问层（含选课、成绩）

职责：
- CourseModel：封装 courses 表 SQL（增删改查 + 按课程名查询，关联授课教师）
- StudentCourseModel：封装 student_course 表 SQL（学生选课/退课/成绩/查询）
依赖：common.db.Database
"""
from com.wanhe4.common.db import Database


class CourseModel:
    """课程表数据访问"""

    def get_all(self, keyword=''):
        """
        查询所有课程（关联授课教师名），可按课程名模糊查询
        :param keyword: 课程名关键字（可选）
        :return: 课程行字典列表（含 teacher_name）
        """
        sql = (
            "SELECT c.*, t.name AS teacher_name, "
            "       (SELECT COUNT(*) FROM student_course sc "
            "        WHERE sc.course_id = c.id) AS selected_count "
            "FROM courses c LEFT JOIN teachers t ON c.teacher_id = t.id "
        )
        params = []
        if keyword:
            sql += "WHERE c.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY c.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_by_id(self, course_id):
        """
        按 ID 查询课程
        :param course_id: 课程 ID
        :return: 课程行 dict；不存在返回 None
        """
        db = Database()
        try:
            return db.query_one("SELECT * FROM courses WHERE id = %s", (course_id,))
        finally:
            db.close()

    def create(self, name, credit, grade, teacher_id):
        """
        新增课程
        :return: 新课程自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO courses (name, credit, grade, teacher_id) VALUES (%s, %s, %s, %s)",
                (name, credit, grade, teacher_id)
            )
        finally:
            db.close()

    def update(self, course_id, name, credit, grade, teacher_id):
        """
        修改课程
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE courses SET name=%s, credit=%s, grade=%s, teacher_id=%s WHERE id=%s",
                (name, credit, grade, teacher_id, course_id)
            )
        finally:
            db.close()

    def get_available_by_student(self, student_id):
        """
        查询某学生还能选择的本年级课程。
        规则：课程年级 = 学生年级，并且该学生还没有选过这门课。
        """
        db = Database()
        try:
            return db.query_all(
                "SELECT c.*, t.name AS teacher_name, "
                "       (SELECT COUNT(*) FROM student_course sc "
                "        WHERE sc.course_id = c.id) AS selected_count "
                "FROM courses c "
                "JOIN students s ON s.id = %s AND c.grade = s.grade "
                "LEFT JOIN teachers t ON c.teacher_id = t.id "
                "WHERE NOT EXISTS ("
                "    SELECT 1 FROM student_course sc "
                "    WHERE sc.student_id = s.id AND sc.course_id = c.id"
                ") "
                "ORDER BY c.id",
                (student_id,)
            )
        finally:
            db.close()

    def has_selected_students_outside_grade(self, course_id, grade):
        """判断课程是否已有非目标年级学生选课。"""
        db = Database()
        try:
            row = db.query_one(
                "SELECT COUNT(*) AS cnt "
                "FROM student_course sc "
                "JOIN students s ON sc.student_id = s.id "
                "WHERE sc.course_id = %s AND s.grade <> %s",
                (course_id, grade)
            )
            return row["cnt"] > 0
        finally:
            db.close()

    def delete(self, course_id):
        """
        删除课程（同时清理选课记录，逐条执行）
        :param course_id: 课程 ID
        :return: 删除的课程行数
        """
        db = Database()
        try:
            # 两次删除放在同一事务中，避免只删掉选课记录却没删掉课程。
            with db.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM student_course WHERE course_id = %s", (course_id,)
                )
                cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                affected = cursor.rowcount
            db.conn.commit()
            return affected
        except Exception:
            db.conn.rollback()
            raise
        finally:
            db.close()


class StudentCourseModel:
    """选课表（学生选课）数据访问"""

    def get_courses_by_student(self, student_id):
        """
        查询某学生已选的课程（关联课程名和教师名）
        :param student_id: 学生 ID
        :return: 已选课程行字典列表（含 course_name/credit/course_grade/teacher_name/score）
        """
        db = Database()
        try:
            return db.query_all(
                "SELECT sc.*, c.name AS course_name, c.credit, "
                "       c.grade AS course_grade, t.name AS teacher_name "
                "FROM student_course sc "
                "JOIN courses c ON sc.course_id = c.id "
                "LEFT JOIN teachers t ON c.teacher_id = t.id "
                "WHERE sc.student_id = %s", (student_id,)
            )
        finally:
            db.close()

    def get_students_by_course(self, course_id):
        """
        查询某门课程的全部已选学生及成绩。
        :param course_id: 课程 ID
        :return: [{student_id, student_name, gender, grade, class_name, score}, ...]
        """
        db = Database()
        try:
            return db.query_all(
                "SELECT s.id AS student_id, s.name AS student_name, "
                "       s.gender, s.grade, c.name AS class_name, sc.score "
                "FROM student_course sc "
                "JOIN students s ON sc.student_id = s.id "
                "LEFT JOIN classes c ON s.class_id = c.id "
                "WHERE sc.course_id = %s "
                "ORDER BY s.id",
                (course_id,)
            )
        finally:
            db.close()

    def is_selected(self, student_id, course_id):
        """
        判断学生是否已选该课程（防止重复选课）
        :return: True 表示已选
        """
        db = Database()
        try:
            return db.query_one(
                "SELECT * FROM student_course WHERE student_id=%s AND course_id=%s",
                (student_id, course_id)
            ) is not None
        finally:
            db.close()

    def select(self, student_id, course_id):
        """
        学生选课
        :return: 新选课记录自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO student_course (student_id, course_id) VALUES (%s, %s)",
                (student_id, course_id)
            )
        finally:
            db.close()

    def unselect(self, student_id, course_id):
        """
        学生退课
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "DELETE FROM student_course WHERE student_id=%s AND course_id=%s",
                (student_id, course_id)
            )
        finally:
            db.close()

    def set_score(self, student_id, course_id, score):
        """
        登记成绩
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE student_course SET score=%s WHERE student_id=%s AND course_id=%s",
                (score, student_id, course_id)
            )
        finally:
            db.close()
