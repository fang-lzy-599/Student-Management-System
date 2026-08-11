SET NAMES utf8mb4;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS school_db_wanhe DEFAULT CHARSET utf8mb4;
USE school_db_wanhe;

-- ============================================================
-- 1. 用户表（学生注册登录 + 管理员）
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          INT          PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username    VARCHAR(50)  NOT NULL UNIQUE           COMMENT '用户名（登录账号）',
    password    VARCHAR(100) NOT NULL                  COMMENT '密码（bcrypt 哈希存储，历史明文登录后自动升级）',
    role        VARCHAR(20)  DEFAULT 'student'         COMMENT '角色：student / admin',
    student_id  INT                                    COMMENT '关联的学生ID（学生角色时使用）',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) COMMENT '用户表';

-- ============================================================
-- 2. 教师表
-- ============================================================
CREATE TABLE IF NOT EXISTS teachers (
    id          INT         PRIMARY KEY AUTO_INCREMENT COMMENT '教师ID',
    name        VARCHAR(50) NOT NULL                    COMMENT '教师姓名',
    gender      VARCHAR(10)                             COMMENT '性别',
    age         INT                                     COMMENT '年龄',
    subject     VARCHAR(50)                             COMMENT '教授科目',
    phone       VARCHAR(20)                             COMMENT '联系电话',
    create_time DATETIME    DEFAULT CURRENT_TIMESTAMP   COMMENT '创建时间'
) COMMENT '教师表';

-- ============================================================
-- 3. 班级表（学生分班）
-- ============================================================
CREATE TABLE IF NOT EXISTS classes (
    id              INT         PRIMARY KEY AUTO_INCREMENT COMMENT '班级ID',
    name            VARCHAR(50) NOT NULL                    COMMENT '班级名称，如：高一(1)班',
    grade           VARCHAR(20)                             COMMENT '年级：高一/高二/高三',
    head_teacher_id INT                                     COMMENT '班主任教师ID',
    create_time     DATETIME    DEFAULT CURRENT_TIMESTAMP   COMMENT '创建时间'
) COMMENT '班级表';

-- ============================================================
-- 4. 学生表（含选老师和分班）
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    id              INT         PRIMARY KEY AUTO_INCREMENT COMMENT '学生ID',
    name            VARCHAR(50) NOT NULL                    COMMENT '学生姓名',
    gender          VARCHAR(10)                             COMMENT '性别',
    age             INT                                     COMMENT '年龄',
    grade           VARCHAR(20)                             COMMENT '年级',
    class_id        INT                                     COMMENT '所属班级ID（分班）',
    teacher_id      INT                                     COMMENT '所属教师ID（选老师）',
    enrollment_date DATE                                    COMMENT '入学日期',
    create_time     DATETIME    DEFAULT CURRENT_TIMESTAMP   COMMENT '创建时间'
) COMMENT '学生表';

-- ============================================================
-- 5. 课程表（教师授课）
-- ============================================================
CREATE TABLE IF NOT EXISTS courses (
    id          INT         PRIMARY KEY AUTO_INCREMENT COMMENT '课程ID',
    name        VARCHAR(50) NOT NULL                    COMMENT '课程名称',
    credit      INT         DEFAULT 1                   COMMENT '学分',
    teacher_id  INT                                     COMMENT '授课教师ID',
    create_time DATETIME    DEFAULT CURRENT_TIMESTAMP   COMMENT '创建时间'
) COMMENT '课程表';

-- ============================================================
-- 6. 选课表（学生选课，多对多）
-- ============================================================
CREATE TABLE IF NOT EXISTS student_course (
    id          INT         PRIMARY KEY AUTO_INCREMENT COMMENT '选课记录ID',
    student_id  INT         NOT NULL                    COMMENT '学生ID',
    course_id   INT         NOT NULL                    COMMENT '课程ID',
    score       DECIMAL(5,2)                            COMMENT '成绩',
    create_time DATETIME    DEFAULT CURRENT_TIMESTAMP   COMMENT '选课时间',
    UNIQUE KEY uk_student_course (student_id, course_id) COMMENT '同一学生同一课程只能选一次'
) COMMENT '选课表';

-- ============================================================
-- 示例数据
-- ============================================================

-- 教师示例
INSERT INTO teachers (name, gender, age, subject, phone) VALUES
    ('张老师', '男', 35, '数学', '13800138001'),
    ('李老师', '女', 28, '语文', '13800138002'),
    ('王老师', '男', 42, '英语', '13800138003'),
    ('赵老师', '女', 31, '物理', '13800138004');

-- 班级示例（班主任关联教师）
INSERT INTO classes (name, grade, head_teacher_id) VALUES
    ('高一(1)班', '高一', 1),
    ('高一(2)班', '高一', 2),
    ('高二(1)班', '高二', 3),
    ('高三(1)班', '高三', 4);

-- 学生示例（张三选高一(1)班、张老师）
INSERT INTO students (name, gender, age, grade, class_id, teacher_id, enrollment_date) VALUES
    ('张三', '男', 18, '高一', 1, 1, '2025-09-01'),
    ('李四', '女', 17, '高一', 1, 1, '2025-09-01'),
    ('王五', '男', 19, '高二', 3, 2, '2025-09-01'),
    ('赵六', '女', 18, '高二', 3, 2, '2025-09-01'),
    ('孙七', '男', 17, '高一', 2, 3, '2025-09-01'),
    ('周八', '女', 18, '高一', 2, 3, '2025-09-01');

-- 课程示例（数学课由张老师教）
INSERT INTO courses (name, credit, teacher_id) VALUES
    ('数学', 3, 1),
    ('语文', 3, 2),
    ('英语', 2, 3),
    ('物理', 2, 4);

-- 选课示例：张三选了数学和语文，李四选了数学
INSERT INTO student_course (student_id, course_id) VALUES
    (1, 1), (1, 2),
    (2, 1);

-- 管理员账号（密码 admin123，种子为明文，登录后自动升级为 bcrypt 哈希）
INSERT INTO users (username, password, role) VALUES
    ('admin', 'admin123', 'admin');



