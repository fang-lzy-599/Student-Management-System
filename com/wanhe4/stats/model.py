import logging
from com.wanhe4.common.db import Database



class StatsModel():
    def count_all_students(self):
        db = Database()
        try:
            sql="select count(*) 总数 from students"
            rows=db.query_all(sql)
            logging.info("当前在校学生%s人",len(rows))
            return rows
        finally:
            db.close()

    def count_all_teachers(self):
        db = Database()
        try:
            sql="select count(*) as 人数 from teachers"
            rows=db.query_all(sql)
            logging.info("当前在校老师%s人",len(rows))
            return rows
        finally:
            db.close()

    def count_all_classes(self):
        db = Database()
        try:
            sql="select count(*) as 班级数量 from classes"
            rows=db.query_all(sql)
            logging.info("当前开设班级%s个",len(rows))
            return rows
        finally:
            db.close()

    def stu_gender_part(self):
        """统计学生"""
        db = Database()
        try:
            sql="select gender,count(*) as 总数 from students group by gender"
            rows=db.query_all(sql)
            logging.info("当前学生男女比例%s",len(rows))
            return rows
        finally:
            db.close()

    def tea_gender_part(self):
        db = Database()
        try:
            sql="select gender,count(*) from teachers group by gender"
            rows=db.query_all(sql)
            logging.info("当前老师男女比例%s",len(rows))
            return rows
        finally:
            db.close()

    def class_count(self):
        db = Database()
        try:
            sql=("select c.id,c.name as class_info,c.grade,count(s.id) as total "
                 "from classes c left join students s on s.class_id=c.id "
                 "group by c.id, c.name, c.grade "
                 "order by c.grade")
            rows=db.query_all(sql)
            logging.info("统计各班级人数%s",len(rows))
            return rows
        finally:
            db.close()

    def grade_distribution(self):
        """统计各年级学生人数"""
        db = Database()
        try:
            sql=("select c.grade,count(s.id) as 人数 "
                 "from classes c "
                 "inner join students s on s.class_id=c.id "
                 "group by c.grade order by c.grade")
            rows=db.query_all(sql)
            logging.info("统计各年级人数%s",len(rows))
            return rows
        finally:
            db.close()

    def get_avg(self):
        """各课程成绩统计:选课人数、总分、平均分、及格人数、及格率"""
        db = Database()
        try:
            sql=(
                "SELECT "
                "  course_id, "
                "  CASE course_id "
                "    WHEN 1 THEN '语文' "
                "    WHEN 2 THEN '数学' "
                "    WHEN 3 THEN '英语' "
                "    WHEN 4 THEN '物理'"
                "    WHEN 5 THEN '化学'"
                "    WHEN 6 THEN '生物' "
                "  END AS course_name, "
                "  COUNT(*) AS student_count, "
                "  SUM(score) AS total_score, "
                "  ROUND(AVG(score), 2) AS avg_score, "
                "  SUM(CASE WHEN score >= 60 THEN 1 ELSE 0 END) AS pass_count, "
                "  ROUND(SUM(CASE WHEN score >= 60 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS pass_rate "
                "FROM student_course "
                "GROUP BY course_id "
                "ORDER BY course_id"
            )
            rows=db.query_all(sql)
            logging.info("统计各课程平均分%s",len(rows))
            return rows
        finally:
            db.close()