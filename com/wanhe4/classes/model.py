from com.wanhe4.common.db import Database


class ClassModel:
    def get_by_id(self, class_id):
        """按 ID 查询班级"""
        db = Database()
        try:
            return db.query_one("SELECT * FROM classes WHERE id=%s", (class_id,))
        finally:
            db.close()
