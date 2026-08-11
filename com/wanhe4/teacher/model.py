# 文件名：teacher/model.py
"""
教师模块 - 数据访问层

职责：封装 teachers 表 SQL 操作（增删改查 + 按姓名关键字查询）
依赖：common.db.Database
"""
from com.wanhe4.common.db import Database


class TeacherModel:
    """教师表数据访问"""

    def get_all(self, keyword='', page=1, page_size=5):
        """
        查询所有教师，可按姓名模糊查询
        :param keyword: 姓名关键字（可选）
        查询教师，支持模糊查询 + 分页
        :param page_size: 每页条数
        :return:分页数据列表
        """
        sql = "SELECT * FROM teachers "
        params = []
        if keyword:
            sql += "WHERE name LIKE %s "
            params.append(f"%{keyword}%")
        # sql += "ORDER BY id LIMIT %s, %s"
        sql += " ORDER BY id LIMIT %s, %s"
        offset = (page - 1) * page_size
        params.append(offset)
        params.append(page_size)

        # 调试打印，看真实生成的sql
        print("【DEBUG_SQL】", repr(sql))
        print("【DEBUG_PARAMS】", params)

        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_by_id(self, teacher_id):
        """
        按 ID 查询教师
        :param teacher_id: 教师 ID
        :return: 教师行 dict；不存在返回 None
        """
        db = Database()
        try:
            return db.query_one("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
        finally:
            db.close()

    def get_total_count(self, keyword=''):
        """获取总记录条数，用于分页计算总页数"""
        sql = "SELECT COUNT(*) AS total FROM teachers"
        params = []
        if keyword:
            sql += " WHERE name LIKE %s"
            params.append(f"%{keyword}%")
        db = Database()
        try:
            return db.query_one(sql, tuple(params))["total"]
        finally:
            db.close()



    def create(self, name, gender, age, subject, phone):
        """
        新增教师
        :return: 新教师自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO teachers (name, gender, age, subject, phone) "
                "VALUES (%s, %s, %s, %s, %s)",
                (name, gender, age, subject, phone)
            )
        finally:
            db.close()

    def update(self, teacher_id, name, gender, age, subject, phone):
        """
        修改教师信息
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE teachers SET name=%s, gender=%s, age=%s, "
                "subject=%s, phone=%s WHERE id=%s",
                (name, gender, age, subject, phone, teacher_id)
            )
        finally:
            db.close()

    def delete(self, teacher_id):
        """
        删除教师
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
        finally:
            db.close()

    # 新增方法，根据姓名查询教师是否存在
    def exist_by_name(self, name, phone):
        """根据教师姓名判断是否已经存在"""
        db = Database()

        try:
            return db.query_one("SELECT id FROM teachers WHERE name = %s and phone = %s", (name, phone,))
        finally:
            db.close()


    # 新增排序功能
    # def order(self):
    #     db = Database()
    #     try:
    #         sql = "SELECT * FROM teachers order by age desc"
    #         return db.query_all(sql)
    #     finally:
    #         db.close()