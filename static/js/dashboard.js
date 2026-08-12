/* EAMS 管理后台：与 com/wanhe4 下的最新路由保持一致 */

const state = {
    currentPanel: 'home',
    studentPage: 1,
    studentPageSize: 10,
    teacherPage: 1,
    teacherPageSize: 8,
    courses: [],
    students: [],
    classes: [],
    teachers: [],
    charts: {},
};

const panelMeta = {
    home: ['数据总览', '查看学校的实时教务数据'],
    students: ['学生管理', '学生资料、分班和指导教师'],
    teachers: ['教师管理', '教师资料和授课科目'],
    classes: ['班级管理', '班级名单与学生转班'],
    courses: ['课程管理', '按年级维护课程和查看选课人数'],
    enrollment: ['选课与成绩', '学生选课、退课、课程查询和成绩登记'],
};

const username = localStorage.getItem('username') || '访客';
const role = localStorage.getItem('role') || 'guest';
document.getElementById('userName').textContent = username;
document.getElementById('userRole').textContent = role === 'admin' ? '管理员' : role === 'student' ? '学生' : '访客';
document.getElementById('userAvatar').textContent = username.slice(0, 1).toUpperCase();
document.getElementById('welcomeTitle').textContent = `欢迎回来，${username}`;

function enterSearch(event, action) {
    if (event.key === 'Enter') action();
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

function switchTab(name) {
    state.currentPanel = name;
    document.querySelectorAll('.panel').forEach(item => item.classList.toggle('active', item.id === name));
    document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('active', item.dataset.panel === name));
    document.getElementById('pageTitle').textContent = panelMeta[name][0];
    document.getElementById('pageSubtitle').textContent = panelMeta[name][1];
    document.getElementById('sidebar').classList.remove('open');
    if (name === 'home') setTimeout(resizeCharts, 10);
    if (name === 'enrollment') loadEnrollmentStudents();
}

function refreshCurrentPanel() {
    const loaders = {
        home: () => Promise.all([loadStats(), loadCharts()]),
        students: loadStudents,
        teachers: loadTeachers,
        classes: loadClasses,
        courses: loadCourses,
        enrollment: loadEnrollmentWorkspace,
    };
    loaders[state.currentPanel]?.();
}

let modalOnOk = null;

function openModal(title, bodyHtml, options = {}) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalSubtitle').textContent = options.subtitle || '';
    document.getElementById('modalBody').innerHTML = bodyHtml;
    document.getElementById('modalFooter').classList.toggle('hidden', options.footer === false);
    document.getElementById('modalOk').textContent = options.okText || '确定';
    document.querySelector('.modal-box').classList.toggle('wide', Boolean(options.wide));
    const modal = document.getElementById('modal');
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    modalOnOk = null;
}

function modalBackdrop(event) {
    if (event.target.id === 'modal') closeModal();
}

document.getElementById('modalOk').onclick = async () => {
    if (!modalOnOk) return;
    const button = document.getElementById('modalOk');
    button.disabled = true;
    try { await modalOnOk(); } finally { button.disabled = false; }
};

function emptyRow(columns, text = '暂无数据') {
    return `<tr class="empty-row"><td colspan="${columns}">${escapeHtml(text)}</td></tr>`;
}

function teacherRecords(data) {
    return Array.isArray(data) ? data : (data?.records || []);
}

async function getAllTeachers() {
    const data = await api('/teachers/all?page=1&page_size=1000');
    state.teachers = teacherRecords(data);
    return state.teachers;
}

function gradeOptions(value = '高一') {
    return ['高一', '高二', '高三'].map(item => `<option value="${item}" ${item === value ? 'selected' : ''}>${item}</option>`).join('');
}

function nullableNumber(id) {
    const value = document.getElementById(id).value;
    return value === '' ? null : Number(value);
}

async function mutate(action, successMessage, after) {
    try {
        await action();
        if (successMessage) toast(successMessage);
        if (after) await after();
        return true;
    } catch (_) {
        return false;
    }
}

// -------------------- 学生 --------------------
async function loadStudents(keyword) {
    keyword ??= document.getElementById('stuKeyword').value.trim();
    try {
        const data = await api(`/student/page?page=${state.studentPage}&page_size=${state.studentPageSize}&keyword=${encodeURIComponent(keyword)}`);
        const list = data?.items || [];
        if (!list.length && state.studentPage > 1) {
            state.studentPage--;
            return loadStudents(keyword);
        }
        document.getElementById('studentBody').innerHTML = list.length ? list.map(student => {
            const count = student.course_count ?? student['选课数'] ?? 0;
            return `<tr>
                <td><input class="student-check" type="checkbox" value="${student.id}" onchange="updateBatchButton()"></td>
                <td>${student.id}</td><td><strong>${escapeHtml(student.name)}</strong></td><td>${escapeHtml(student.gender)}</td>
                <td>${student.age}</td><td><span class="badge grade-badge">${escapeHtml(student.grade)}</span></td>
                <td>${escapeHtml(student.class_name || '未分班')}</td><td>${escapeHtml(student.teacher_name || '未指定')}</td>
                <td><span class="badge badge-blue">${Number(count)} 门</span></td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="openStudentModal('edit',${student.id})">编辑</button>
                    <button class="btn btn-small btn-warning" onclick="openAssignClassModal(${student.id})">分班</button>
                    <button class="btn btn-small btn-ghost" onclick="openAssignTeacherModal(${student.id})">教师</button>
                    <button class="btn btn-small btn-success" onclick="openStudentCourseDetail(${student.id},'${escapeHtml(student.name)}')">课程</button>
                    <button class="btn btn-small btn-danger-outline" onclick="delStudent(${student.id})">删除</button>
                </td></tr>`;
        }).join('') : emptyRow(10, '没有找到学生');
        renderStudentPager(data?.total || 0);
        document.getElementById('studentCheckAll').checked = false;
        updateBatchButton();
    } catch (_) {
        document.getElementById('studentBody').innerHTML = emptyRow(10, '学生数据加载失败');
    }
}

function renderStudentPager(total) {
    const pages = Math.max(1, Math.ceil(total / state.studentPageSize));
    document.getElementById('stuPager').innerHTML = `<button class="btn btn-ghost" ${state.studentPage <= 1 ? 'disabled' : ''} onclick="gotoStudentPage(${state.studentPage - 1})">上一页</button><span class="page-info">第 ${state.studentPage} / ${pages} 页，共 ${total} 条</span><button class="btn btn-ghost" ${state.studentPage >= pages ? 'disabled' : ''} onclick="gotoStudentPage(${state.studentPage + 1})">下一页</button>`;
}

function gotoStudentPage(page) { state.studentPage = page; loadStudents(); }
function searchStudents() { state.studentPage = 1; loadStudents(); }
function resetStudents() { document.getElementById('stuKeyword').value = ''; state.studentPage = 1; loadStudents(''); }
function toggleAllStudents(checked) { document.querySelectorAll('.student-check').forEach(item => item.checked = checked); updateBatchButton(); }
function selectedStudentIds() { return [...document.querySelectorAll('.student-check:checked')].map(item => Number(item.value)); }
function updateBatchButton() { document.getElementById('batchDeleteBtn').disabled = selectedStudentIds().length === 0; }

async function openStudentModal(mode, id) {
    try {
        const [student, classes, teachers] = await Promise.all([
            mode === 'edit' ? api(`/student/one/${id}`) : Promise.resolve({}),
            api('/classes/all'),
            getAllTeachers(),
        ]);
        openModal(mode === 'add' ? '新增学生' : '编辑学生', `
            <div class="field-row"><div class="field"><label>姓名</label><input id="studentName" maxlength="50" value="${escapeHtml(student.name || '')}" placeholder="请输入姓名"></div><div class="field"><label>性别</label><select id="studentGender"><option ${student.gender !== '女' ? 'selected' : ''}>男</option><option ${student.gender === '女' ? 'selected' : ''}>女</option></select></div></div>
            <div class="field-row"><div class="field"><label>年龄</label><input id="studentAge" type="number" min="10" max="100" value="${student.age ?? ''}"></div><div class="field"><label>年级</label><select id="studentGrade">${gradeOptions(student.grade)}</select></div></div>
            ${mode === 'add' ? `<div class="field-row"><div class="field"><label>班级（可暂不分班）</label><select id="studentClass"><option value="">暂不分班</option>${classes.map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join('')}</select></div><div class="field"><label>指导教师（可空）</label><select id="studentTeacher"><option value="">暂不指定</option>${teachers.map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join('')}</select></div></div><div class="field"><label>入学日期</label><input id="enrollmentDate" type="date" value="2025-09-01"></div>` : ''}`,
            { subtitle: mode === 'add' ? '创建学生档案' : `学生 ID：${id}` }
        );
        modalOnOk = async () => {
            const name = document.getElementById('studentName').value.trim();
            const age = Number(document.getElementById('studentAge').value);
            if (!name) return toast('请输入学生姓名', 'error');
            if (age < 10 || age > 100) return toast('年龄必须在 10 到 100 之间', 'error');
            const body = { name, gender: document.getElementById('studentGender').value, age, grade: document.getElementById('studentGrade').value };
            if (mode === 'add') Object.assign(body, { class_id: nullableNumber('studentClass'), teacher_id: nullableNumber('studentTeacher'), enrollment_date: document.getElementById('enrollmentDate').value });
            const ok = await mutate(() => api(mode === 'add' ? '/student/add' : `/student/update/${id}`, mode === 'add' ? 'POST' : 'PUT', body), mode === 'add' ? '学生新增成功' : '学生信息已更新');
            if (ok) { closeModal(); await Promise.all([loadStudents(), loadEnrollmentStudents()]); }
        };
    } catch (_) {}
}

async function openAssignClassModal(id) {
    try {
        const classes = await api('/classes/all');
        openModal('学生分班', `<div class="field"><label>目标班级</label><select id="assignClass"><option value="">请选择班级</option>${classes.map(item => `<option value="${item.id}">${escapeHtml(item.name)} · ${escapeHtml(item.grade)}</option>`).join('')}</select></div>`);
        modalOnOk = async () => {
            const classId = nullableNumber('assignClass');
            if (!classId) return toast('请选择班级', 'error');
            const ok = await mutate(() => api(`/student/assign-class/${id}`, 'PUT', { class_id: classId }), '分班成功');
            if (ok) { closeModal(); loadStudents(); }
        };
    } catch (_) {}
}

async function openAssignTeacherModal(id) {
    try {
        const teachers = await getAllTeachers();
        openModal('指定指导教师', `<div class="field"><label>教师</label><select id="assignTeacher"><option value="">请选择教师</option>${teachers.map(item => `<option value="${item.id}">${escapeHtml(item.name)} · ${escapeHtml(item.subject)}</option>`).join('')}</select></div>`);
        modalOnOk = async () => {
            const teacherId = nullableNumber('assignTeacher');
            if (!teacherId) return toast('请选择教师', 'error');
            const ok = await mutate(() => api(`/student/assign-teacher/${id}`, 'PUT', { teacher_id: teacherId }), '教师指定成功');
            if (ok) { closeModal(); loadStudents(); }
        };
    } catch (_) {}
}

async function openStudentCourseDetail(id, name) {
    try {
        const list = await api(`/student/${id}/courses`);
        openModal(`${name}的选课详情`, list.length ? `<div class="table-wrap"><table><thead><tr><th>课程</th><th>教师</th><th>学分</th><th>成绩</th></tr></thead><tbody>${list.map(item => `<tr><td>${escapeHtml(item.course_name)}</td><td>${escapeHtml(item.teacher_name || '未指定')}</td><td>${item.credit}</td><td>${scoreHtml(item.score)}</td></tr>`).join('')}</tbody></table></div>` : `<div class="empty-state"><div>0</div><h3>还没有选课</h3></div>`, { footer: false, wide: true });
    } catch (_) {}
}

async function delStudent(id) {
    if (!confirm(`确定删除学生 ${id} 吗？相关账号和选课记录也会被删除。`)) return;
    await mutate(() => api(`/student/del/${id}`, 'DELETE'), '学生已删除', () => Promise.all([loadStudents(), loadCourses(), loadEnrollmentStudents()]));
}

async function batchDeleteStudents() {
    const ids = selectedStudentIds();
    if (!ids.length || !confirm(`确定批量删除选中的 ${ids.length} 名学生吗？`)) return;
    await mutate(() => api('/student/batch-delete', 'POST', { ids }), `已删除 ${ids.length} 名学生`, () => Promise.all([loadStudents(), loadCourses(), loadEnrollmentStudents()]));
}

// -------------------- 教师 --------------------
async function loadTeachers(keyword) {
    keyword ??= document.getElementById('teaKeyword').value.trim();
    try {
        const sortField = document.getElementById('teacherSortField').value;
        const sortOrder = document.getElementById('teacherSortOrder').value;
        const data = await api(`/teachers/all?keyword=${encodeURIComponent(keyword)}&page=${state.teacherPage}&page_size=${state.teacherPageSize}&sort_field=${encodeURIComponent(sortField)}&sort_order=${encodeURIComponent(sortOrder)}`);
        const list = teacherRecords(data);
        document.getElementById('teacherBody').innerHTML = list.length ? list.map(item => `<tr><td>${item.id}</td><td><strong>${escapeHtml(item.name)}</strong></td><td>${escapeHtml(item.gender)}</td><td>${item.age}</td><td><span class="badge badge-blue">${escapeHtml(item.subject)}</span></td><td>${escapeHtml(item.phone || '—')}</td><td><button class="btn btn-small btn-secondary" onclick="openTeacherModal('edit',${item.id})">编辑</button><button class="btn btn-small btn-danger-outline" onclick="delTeacher(${item.id})">删除</button></td></tr>`).join('') : emptyRow(7, '没有找到教师');
        const pages = Math.max(1, data.total_page || 1);
        document.getElementById('teaPager').innerHTML = `<button class="btn btn-ghost" ${state.teacherPage <= 1 ? 'disabled' : ''} onclick="gotoTeacherPage(${state.teacherPage - 1})">上一页</button><span class="page-info">第 ${state.teacherPage} / ${pages} 页，共 ${data.total || 0} 条</span><button class="btn btn-ghost" ${state.teacherPage >= pages ? 'disabled' : ''} onclick="gotoTeacherPage(${state.teacherPage + 1})">下一页</button>`;
    } catch (_) { document.getElementById('teacherBody').innerHTML = emptyRow(7, '教师数据加载失败'); }
}

function gotoTeacherPage(page) { state.teacherPage = page; loadTeachers(); }
function searchTeachers() { state.teacherPage = 1; loadTeachers(); }
function changeTeacherSort() { state.teacherPage = 1; loadTeachers(); }
function resetTeachers() {
    document.getElementById('teaKeyword').value = '';
    document.getElementById('teacherSortField').value = 'id';
    document.getElementById('teacherSortOrder').value = 'desc';
    state.teacherPage = 1;
    loadTeachers('');
}

async function openTeacherModal(mode, id) {
    try {
        const teacher = mode === 'edit' ? await api(`/teachers/one/${id}`) : {};
        openModal(mode === 'add' ? '新增教师' : '编辑教师', `<div class="field-row"><div class="field"><label>姓名</label><input id="teacherName" value="${escapeHtml(teacher.name || '')}"></div><div class="field"><label>性别</label><select id="teacherGender"><option ${teacher.gender !== '女' ? 'selected' : ''}>男</option><option ${teacher.gender === '女' ? 'selected' : ''}>女</option></select></div></div><div class="field-row"><div class="field"><label>年龄</label><input id="teacherAge" type="number" min="20" max="70" value="${teacher.age ?? 30}"></div><div class="field"><label>教授科目</label><input id="teacherSubject" value="${escapeHtml(teacher.subject || '')}"></div></div><div class="field"><label>联系电话</label><input id="teacherPhone" maxlength="20" value="${escapeHtml(teacher.phone || '')}"></div>`);
        modalOnOk = async () => {
            const body = { name: document.getElementById('teacherName').value.trim(), gender: document.getElementById('teacherGender').value, age: Number(document.getElementById('teacherAge').value), subject: document.getElementById('teacherSubject').value.trim(), phone: document.getElementById('teacherPhone').value.trim() };
            if (!body.name || !body.subject) return toast('姓名和教授科目不能为空', 'error');
            if (body.age < 20 || body.age > 70) return toast('教师年龄必须在 20 到 70 之间', 'error');
            const ok = await mutate(() => api(mode === 'add' ? '/teachers/add' : `/teachers/update/${id}`, mode === 'add' ? 'POST' : 'PUT', body), mode === 'add' ? '教师新增成功' : '教师信息已更新');
            if (ok) { closeModal(); await Promise.all([loadTeachers(), loadClasses(), loadCourses()]); }
        };
    } catch (_) {}
}

async function delTeacher(id) {
    if (!confirm(`确定删除教师 ${id} 吗？请先确认其未被班级或课程引用。`)) return;
    await mutate(() => api(`/teachers/del/${id}`, 'DELETE'), '教师已删除', loadTeachers);
}

// -------------------- 班级 --------------------
async function loadClasses(keyword) {
    keyword ??= document.getElementById('clsKeyword').value.trim();
    try {
        state.classes = await api(`/classes/all?keyword=${encodeURIComponent(keyword)}`);
        document.getElementById('classBody').innerHTML = state.classes.length ? state.classes.map(item => `<tr><td>${item.id}</td><td><strong>${escapeHtml(item.name)}</strong></td><td><span class="badge grade-badge">${escapeHtml(item.grade)}</span></td><td>${escapeHtml(item.head_teacher_name || '未指定')}</td><td><button class="count-button ${Number(item.student_count) ? 'has-data' : ''}" onclick="openClassRoster(${item.id},'${escapeHtml(item.name)}')">${Number(item.student_count) || 0} 人</button></td><td><button class="btn btn-small btn-success" onclick="openClassRoster(${item.id},'${escapeHtml(item.name)}')">学生名单</button><button class="btn btn-small btn-secondary" onclick="openClassModal('edit',${item.id})">编辑</button><button class="btn btn-small btn-warning" onclick="clearClass(${item.id})">清空学生</button><button class="btn btn-small btn-danger-outline" onclick="delClass(${item.id})">删除</button></td></tr>`).join('') : emptyRow(6, '没有找到班级');
    } catch (_) { document.getElementById('classBody').innerHTML = emptyRow(6, '班级数据加载失败'); }
}

function searchClasses() { loadClasses(); }
function resetClasses() { document.getElementById('clsKeyword').value = ''; loadClasses(''); }

async function openClassModal(mode, id) {
    try {
        const [item, teachers] = await Promise.all([mode === 'edit' ? api(`/classes/one/${id}`) : Promise.resolve({}), getAllTeachers()]);
        openModal(mode === 'add' ? '新增班级' : '编辑班级', `<div class="field"><label>班级名称</label><input id="className" maxlength="50" value="${escapeHtml(item.name || '')}" placeholder="例如：高一(1)班"></div><div class="field-row"><div class="field"><label>年级</label><select id="classGrade">${gradeOptions(item.grade)}</select></div><div class="field"><label>班主任</label><select id="headTeacher"><option value="">暂不指定</option>${teachers.map(teacher => `<option value="${teacher.id}" ${Number(item.head_teacher_id) === Number(teacher.id) ? 'selected' : ''}>${escapeHtml(teacher.name)}</option>`).join('')}</select></div></div>`);
        modalOnOk = async () => {
            const body = { name: document.getElementById('className').value.trim(), grade: document.getElementById('classGrade').value, head_teacher_id: nullableNumber('headTeacher') };
            if (!body.name) return toast('请输入班级名称', 'error');
            const ok = await mutate(() => api(mode === 'add' ? '/classes/add' : `/classes/update/${id}`, mode === 'add' ? 'POST' : 'PUT', body), mode === 'add' ? '班级新增成功' : '班级已更新');
            if (ok) { closeModal(); await Promise.all([loadClasses(), loadStudents()]); }
        };
    } catch (_) {}
}

async function openClassRoster(id, name) {
    try {
        const [students, classes] = await Promise.all([api(`/classes/${id}/students`), api('/classes/all')]);
        openModal(`${name} · 学生名单`, `<div class="roster-head"><strong>共 ${students.length} 名学生</strong><span class="muted">勾选后可批量转班</span></div>${students.length ? `<div class="check-list">${students.map(item => `<label class="check-item"><input class="move-student-check" type="checkbox" value="${item.id}"><span><strong>${escapeHtml(item.name)}</strong>　${escapeHtml(item.gender)} · ${escapeHtml(item.grade)}</span></label>`).join('')}</div><div class="field"><label>转入班级</label><select id="targetClass"><option value="">请选择目标班级</option>${classes.filter(item => Number(item.id) !== Number(id)).map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join('')}</select></div>` : `<div class="empty-state"><div>0</div><h3>该班暂无学生</h3></div>`}`, { wide: true, okText: students.length ? '转移选中学生' : '关闭' });
        modalOnOk = async () => {
            if (!students.length) return closeModal();
            const ids = [...document.querySelectorAll('.move-student-check:checked')].map(item => Number(item.value));
            const target = nullableNumber('targetClass');
            if (!ids.length) return toast('请先勾选要转移的学生', 'error');
            if (!target) return toast('请选择目标班级', 'error');
            const ok = await mutate(() => api('/classes/move_students', 'POST', { student_ids: ids, target_class_id: target }), `成功转移 ${ids.length} 名学生`);
            if (ok) { closeModal(); await Promise.all([loadClasses(), loadStudents()]); }
        };
    } catch (_) {}
}

async function clearClass(id) {
    if (!confirm('确定把该班所有学生设为“未分班”吗？学生档案不会被删除。')) return;
    await mutate(() => api(`/classes/clear_students/${id}`, 'POST'), '班级学生已清空', () => Promise.all([loadClasses(), loadStudents()]));
}

async function delClass(id) {
    if (!confirm(`确定删除班级 ${id} 吗？建议先清空班级学生。`)) return;
    await mutate(() => api(`/classes/del/${id}`, 'DELETE'), '班级已删除', () => Promise.all([loadClasses(), loadStudents()]));
}

// -------------------- 课程 --------------------
async function loadCourses(keyword) {
    keyword ??= document.getElementById('couKeyword').value.trim();
    try {
        state.courses = await api(`/courses/all?keyword=${encodeURIComponent(keyword)}`);
        renderCourses();
    } catch (_) { document.getElementById('courseBody').innerHTML = emptyRow(7, '课程数据加载失败'); }
}

function renderCourses() {
    const grade = document.getElementById('courseGradeFilter').value;
    const list = grade ? state.courses.filter(item => item.grade === grade) : state.courses;
    document.getElementById('courseBody').innerHTML = list.length ? list.map(item => `<tr><td>${item.id}</td><td><strong>${escapeHtml(item.name)}</strong></td><td><span class="badge grade-badge">${escapeHtml(item.grade || '未设置')}</span></td><td>${item.credit}</td><td>${escapeHtml(item.teacher_name || '未指定')}</td><td><button class="count-button ${Number(item.selected_count) ? 'has-data' : ''}" onclick="openCourseRoster(${item.id})">${Number(item.selected_count) || 0} 人</button></td><td><button class="btn btn-small btn-success" onclick="openCourseRoster(${item.id})">名单</button><button class="btn btn-small btn-secondary" onclick="openCourseModal('edit',${item.id})">编辑</button><button class="btn btn-small btn-danger-outline" onclick="delCourse(${item.id})">删除</button></td></tr>`).join('') : emptyRow(7, '没有找到课程');
}

function searchCourses() { loadCourses(); }
function resetCourses() { document.getElementById('couKeyword').value = ''; document.getElementById('courseGradeFilter').value = ''; loadCourses(''); }

async function openCourseModal(mode, id) {
    try {
        const [course, teachers] = await Promise.all([mode === 'edit' ? api(`/courses/one/${id}`) : Promise.resolve({}), getAllTeachers()]);
        state.courseFormTeachers = teachers;
        state.courseFormTeacherId = course.teacher_id ?? null;
        openModal(mode === 'add' ? '新增课程' : '编辑课程', `<div class="field"><label>课程名称</label><input id="courseName" maxlength="50" value="${escapeHtml(course.name || '')}" placeholder="例如：数学" oninput="renderCourseTeacherOptions()"></div><div class="field-row"><div class="field"><label>适用年级</label><select id="courseGrade">${gradeOptions(course.grade)}</select></div><div class="field"><label>学分（1-5分）</label><input id="courseCredit" type="number" min="1" max="5" value="${course.credit ?? 1}"></div></div><div class="field"><label>授课教师</label><select id="courseTeacher"></select><small id="courseTeacherHint" class="muted"></small></div><div class="modal-note">授课教师的教授科目必须与课程名称一致；例如数学课程只能选择数学教师。</div>`, { subtitle: mode === 'add' ? '创建一门按年级开放的新课程' : `课程 ID：${id}` });
        renderCourseTeacherOptions();
        modalOnOk = async () => {
            const body = { name: document.getElementById('courseName').value.trim(), credit: Number(document.getElementById('courseCredit').value), grade: document.getElementById('courseGrade').value, teacher_id: nullableNumber('courseTeacher') };
            if (!body.name) return toast('请输入课程名称', 'error');
            if (!Number.isInteger(body.credit) || body.credit < 1 || body.credit > 5) return toast('学分必须是 1 到 5 之间的整数', 'error');
            const ok = await mutate(() => api(mode === 'add' ? '/courses/add' : `/courses/update/${id}`, mode === 'add' ? 'POST' : 'PUT', body), mode === 'add' ? '课程新增成功' : '课程已更新');
            if (ok) { closeModal(); await Promise.all([loadCourses(), loadEnrollmentWorkspace()]); }
        };
    } catch (_) {}
}

function renderCourseTeacherOptions() {
    const nameInput = document.getElementById('courseName');
    const select = document.getElementById('courseTeacher');
    const hint = document.getElementById('courseTeacherHint');
    if (!nameInput || !select || !hint) return;

    const courseName = nameInput.value.trim();
    const currentTeacherId = select.value || String(state.courseFormTeacherId ?? '');
    const matched = (state.courseFormTeachers || []).filter(
        teacher => String(teacher.subject || '').trim() === courseName
    );
    select.innerHTML = `<option value="">暂不指定教师</option>${matched.map(teacher => `<option value="${teacher.id}">${escapeHtml(teacher.name)} · ${escapeHtml(teacher.subject)}</option>`).join('')}`;
    if (matched.some(teacher => String(teacher.id) === currentTeacherId)) {
        select.value = currentTeacherId;
    }
    state.courseFormTeacherId = null;

    if (!courseName) hint.textContent = '请先输入课程名称，再选择对应科目的教师';
    else if (!matched.length) hint.textContent = `目前没有教授“${courseName}”的教师，可以暂不指定`;
    else hint.textContent = `已找到 ${matched.length} 名教授“${courseName}”的教师`;
}

async function openCourseRoster(courseId) {
    try {
        const [course, students] = await Promise.all([api(`/courses/one/${courseId}`), api(`/courses/${courseId}/students`)]);
        openModal(`${course.name} · 选课名单`, students.length ? `<div class="roster-head"><strong>${escapeHtml(course.grade)} · 共 ${students.length} 人</strong><span class="muted">可在此登记成绩或退课</span></div><div class="table-wrap"><table><thead><tr><th>学号</th><th>姓名</th><th>性别</th><th>班级</th><th>成绩</th><th>操作</th></tr></thead><tbody>${students.map(item => `<tr><td>${item.student_id}</td><td><strong>${escapeHtml(item.student_name)}</strong></td><td>${escapeHtml(item.gender)}</td><td>${escapeHtml(item.class_name || '未分班')}</td><td>${scoreHtml(item.score)}</td><td><button class="btn btn-small btn-secondary" onclick="openScoreModal(${item.student_id},${courseId},'${escapeHtml(course.name)}',${item.score == null ? 'null' : Number(item.score)},'roster')">录入成绩</button><button class="btn btn-small btn-danger-outline" onclick="unselectCourse(${item.student_id},${courseId},'roster')">退课</button></td></tr>`).join('')}</tbody></table></div>` : `<div class="empty-state"><div>0</div><h3>暂无学生选择这门课</h3><p>请到“选课与成绩”页面，以学生身份选择课程。</p></div>`, { footer: false, wide: true, subtitle: `课程 ID：${courseId}` });
    } catch (_) {}
}

async function delCourse(id) {
    if (!confirm(`确定删除课程 ${id} 吗？该课程的全部选课和成绩记录会一并删除。`)) return;
    await mutate(() => api(`/courses/del/${id}`, 'DELETE'), '课程已删除', () => Promise.all([loadCourses(), loadEnrollmentWorkspace()]));
}

// -------------------- 学生选课与成绩（核心功能） --------------------
async function loadEnrollmentStudents() {
    try {
        state.students = await api('/student/all');
        const select = document.getElementById('enrollStudent');
        const old = select.value;
        select.innerHTML = `<option value="">请选择学生</option>${state.students.map(item => `<option value="${item.id}">${escapeHtml(item.name)} · ${escapeHtml(item.grade)} · 学号 ${item.id}</option>`).join('')}`;
        if (state.students.some(item => String(item.id) === old)) select.value = old;
    } catch (_) {}
}

async function loadEnrollmentWorkspace() {
    const studentId = Number(document.getElementById('enrollStudent').value);
    const empty = document.getElementById('enrollmentEmpty');
    const workspace = document.getElementById('enrollmentWorkspace');
    if (!studentId) {
        empty.classList.remove('hidden'); workspace.classList.add('hidden');
        document.getElementById('studentProfile').innerHTML = '选择学生后将自动匹配该生年级课程';
        return;
    }
    try {
        const [student, available, selected] = await Promise.all([
            api(`/student/one/${studentId}`),
            api(`/courses/available/${studentId}`),
            api(`/courses/student/${studentId}`),
        ]);
        const joinedStudent = state.students.find(item => Number(item.id) === studentId) || student;
        empty.classList.add('hidden'); workspace.classList.remove('hidden');
        document.getElementById('studentProfile').innerHTML = `<strong>${escapeHtml(student.name)}</strong><span class="badge grade-badge">${escapeHtml(student.grade)}</span>　${escapeHtml(joinedStudent.class_name || '未分班')}　·　已选 ${selected.length} 门`;
        document.getElementById('availableCount').textContent = `${available.length} 门`;
        document.getElementById('selectedCount').textContent = `${selected.length} 门`;
        document.getElementById('availableCourses').innerHTML = available.length ? available.map(item => `<div class="course-option"><div><h4>${escapeHtml(item.name)} <span class="badge grade-badge">${escapeHtml(item.grade)}</span></h4><p>${escapeHtml(item.teacher_name || '未指定教师')} · ${item.credit} 学分 · 已有 ${Number(item.selected_count) || 0} 人选择</p></div><button class="btn btn-primary" onclick="selectCourse(${studentId},${item.id})">选择课程</button></div>`).join('') : `<div class="empty-state"><div>✓</div><h3>没有更多可选课程</h3><p>该年级课程可能已经全部选择。</p></div>`;
        document.getElementById('selectedCourseBody').innerHTML = selected.length ? selected.map(item => `<tr><td><strong>${escapeHtml(item.course_name)}</strong></td><td><span class="badge grade-badge">${escapeHtml(item.course_grade)}</span></td><td>${escapeHtml(item.teacher_name || '未指定')}</td><td>${item.credit}</td><td>${scoreHtml(item.score)}</td><td><button class="btn btn-small btn-secondary" onclick="openScoreModal(${studentId},${item.course_id},'${escapeHtml(item.course_name)}',${item.score == null ? 'null' : Number(item.score)},'student')">成绩</button><button class="btn btn-small btn-danger-outline" onclick="unselectCourse(${studentId},${item.course_id},'student')">退课</button></td></tr>`).join('') : emptyRow(6, '该学生还没有选择课程');
    } catch (_) {
        workspace.classList.add('hidden'); empty.classList.remove('hidden');
        document.getElementById('studentProfile').textContent = '选课数据加载失败';
    }
}

function scoreHtml(score) {
    if (score === null || score === undefined) return '<span class="score pending">未登记</span>';
    const number = Number(score);
    return `<span class="score ${number >= 60 ? 'good' : 'bad'}">${number}</span>`;
}

async function selectCourse(studentId, courseId) {
    await mutate(() => api(`/courses/select/${studentId}`, 'POST', { course_id: courseId }), '选课成功', () => Promise.all([loadEnrollmentWorkspace(), loadCourses(), loadStudents()]));
}

async function unselectCourse(studentId, courseId, source) {
    if (!confirm('确定退选这门课程吗？已登记的成绩也会随选课记录删除。')) return;
    const ok = await mutate(() => api(`/courses/unselect/${studentId}`, 'DELETE', { course_id: courseId }), '退课成功', () => Promise.all([loadEnrollmentWorkspace(), loadCourses(), loadStudents()]));
    if (ok && source === 'roster') openCourseRoster(courseId);
}

function openScoreModal(studentId, courseId, courseName, currentScore, source) {
    openModal('登记课程成绩', `<div class="modal-note">课程：${escapeHtml(courseName)}　·　学生 ID：${studentId}</div><div class="field"><label>成绩（0 - 100）</label><input id="scoreInput" type="number" min="0" max="100" step="0.1" value="${currentScore ?? ''}" placeholder="请输入成绩"></div>`, { okText: '保存成绩' });
    modalOnOk = async () => {
        const score = Number(document.getElementById('scoreInput').value);
        if (document.getElementById('scoreInput').value === '' || score < 0 || score > 100) return toast('成绩必须在 0 到 100 之间', 'error');
        const ok = await mutate(() => api(`/courses/score/${studentId}`, 'PUT', { course_id: courseId, score }), '成绩保存成功', () => loadEnrollmentWorkspace());
        if (ok) {
            closeModal();
            if (source === 'roster') openCourseRoster(courseId);
        }
    };
}

// -------------------- 统计 --------------------
function firstNumeric(items) {
    const row = Array.isArray(items) ? items[0] : items;
    if (!row) return 0;
    return Number(Object.values(row).find(value => typeof value === 'number' || /^\d+$/.test(String(value))) || 0);
}

async function loadStats() {
    const [students, teachers, classes, courses] = await Promise.all([
        apiSafe('/stats/student-count'), apiSafe('/stats/teacher-count'), apiSafe('/stats/class-count-total'), apiSafe('/courses/all', []),
    ]);
    const fallbackStudents = await apiSafe('/student/page?page=1&page_size=1', { total: 0 });
    const fallbackTeachers = await apiSafe('/teachers/all?page=1&page_size=1', { total: 0 });
    const fallbackClasses = await apiSafe('/classes/all', []);
    document.getElementById('studentCount').textContent = students ? firstNumeric(students.items) : (fallbackStudents?.total || 0);
    document.getElementById('teacherCount').textContent = teachers ? firstNumeric(teachers.items) : (fallbackTeachers?.total || 0);
    document.getElementById('classCount').textContent = classes ? firstNumeric(classes.items) : fallbackClasses.length;
    document.getElementById('courseCount').textContent = courses.length;
}

function chart(id, option) {
    if (typeof echarts === 'undefined') return;
    state.charts[id]?.dispose();
    const instance = echarts.init(document.getElementById(id));
    instance.setOption(option);
    state.charts[id] = instance;
}

function axisOption(labels, values, color = '#3157d5', extraSeries = []) {
    return { tooltip: { trigger: 'axis' }, grid: { left: 12, right: 15, top: 25, bottom: 10, containLabel: true }, xAxis: { type: 'category', data: labels, axisLabel: { color: '#78849a', interval: 0, rotate: labels.length > 6 ? 25 : 0 }, axisLine: { lineStyle: { color: '#e5e9f2' } } }, yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#eef1f6' } } }, series: [{ type: 'bar', name: '人数', data: values, barMaxWidth: 34, itemStyle: { color, borderRadius: [6,6,0,0] } }, ...extraSeries] };
}

function pieOption(items) {
    return { tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' }, legend: { bottom: 0 }, color: ['#3157d5', '#ec6e91', '#f0a348'], series: [{ type: 'pie', radius: ['38%', '67%'], center: ['50%', '44%'], label: { formatter: '{b}\n{c}人', fontSize: 11 }, data: items }] };
}

async function loadCharts() {
    if (typeof echarts === 'undefined') return;
    const [classData, gradeData, stuGender, teaGender, courseData] = await Promise.all([
        apiSafe('/stats/class-count', { items: [] }), apiSafe('/stats/grade-count', { items: [] }), apiSafe('/stats/stu-gender-ratio', { items: [] }), apiSafe('/stats/tea-gender-ratio', { items: [] }), apiSafe('/stats/course-avg', { items: [] }),
    ]);
    let classes = classData?.items || [];
    let grades = gradeData?.items || [];
    let studentGender = stuGender?.items || [];
    let teacherGender = teaGender?.items || [];
    let courses = courseData?.items || [];

    // 某个统计接口暂时不可用时，用基础查询接口在浏览器端生成同样的数据。
    const needStudentFallback = !classes.length || !grades.length || !studentGender.length;
    const fallbackStudents = needStudentFallback ? await apiSafe('/student/all', []) : [];
    if (!classes.length) {
        const fallbackClasses = await apiSafe('/classes/all', []);
        classes = fallbackClasses.map(item => ({
            class_info: item.name,
            total: fallbackStudents.filter(student => Number(student.class_id) === Number(item.id)).length,
        }));
    }
    if (!grades.length) {
        grades = ['高一', '高二', '高三'].map(grade => ({ grade, 人数: fallbackStudents.filter(student => student.grade === grade).length }));
    }
    if (!studentGender.length) {
        studentGender = ['男', '女'].map(gender => ({ gender, 总数: fallbackStudents.filter(student => student.gender === gender).length }));
    }
    if (!teacherGender.length) {
        const fallbackTeachers = teacherRecords(await apiSafe('/teachers/all?page=1&page_size=1000', { records: [] }));
        teacherGender = ['男', '女'].map(gender => ({ gender, 总数: fallbackTeachers.filter(teacher => teacher.gender === gender).length }));
    }
    chart('classChart', axisOption(classes.map(item => item.class_info || item.class_name || item.name), classes.map(item => Number(item.total ?? item.cnt ?? 0))));
    chart('gradeChart', axisOption(grades.map(item => item.grade), grades.map(item => Number(item['人数'] ?? item.total ?? 0)), '#824fd4'));
    chart('studentGenderChart', pieOption(studentGender.map(item => ({ name: item.gender, value: Number(item['总数'] ?? item.total ?? item.cnt ?? 0) }))));
    chart('teacherGenderChart', pieOption(teacherGender.map(item => ({ name: item.gender, value: Number(item['count(*)'] ?? item['总数'] ?? item.total ?? item.cnt ?? 0) }))));
    chart('courseChart', axisOption(courses.map(item => item.course_name || `课程${item.course_id}`), courses.map(item => Number(item.avg_score || 0)), '#15986a', [{ type: 'line', name: '及格率', data: courses.map(item => Number(item.pass_rate || 0)), yAxisIndex: 0, smooth: true, itemStyle: { color: '#e6922e' } }]));
}

function resizeCharts() { Object.values(state.charts).forEach(instance => instance.resize()); }
window.addEventListener('resize', resizeCharts);

async function initialize() {
    await Promise.allSettled([loadStats(), loadCharts(), loadStudents(), loadTeachers(), loadClasses(), loadCourses(), loadEnrollmentStudents()]);
}

initialize();
