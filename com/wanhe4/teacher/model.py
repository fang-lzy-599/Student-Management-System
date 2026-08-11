from com.wanhe4.common.db import Database


class TeacherModel:
    def get_by_id(self, teacher_id):
        """按 ID 查询教师"""
        db = Database()
        try:
            return db.query_one("SELECT * FROM teachers WHERE id=%s", (teacher_id,))
        finally:
            db.close()
