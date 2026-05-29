const SESSION_KEY = "campus_demo_session";
const API_BASE = "";

const routes = [
  { id: "dashboard", label: "总览", icon: "D", title: "系统总览", subtitle: "Dashboard", roles: ["student", "teacher", "admin"] },
  { id: "students", label: "学生管理", icon: "S", title: "学生管理", subtitle: "Students", roles: ["teacher", "admin"] },
  { id: "courses", label: "课程管理", icon: "C", title: "课程管理", subtitle: "Courses", roles: ["student", "teacher", "admin"] },
  { id: "enrollments", label: "选课管理", icon: "E", title: "选课管理", subtitle: "Enrollments", roles: ["student", "teacher", "admin"] },
  { id: "grades", label: "成绩管理", icon: "G", title: "成绩管理", subtitle: "Grades", roles: ["student", "teacher", "admin"] },
  { id: "analytics", label: "统计分析", icon: "A", title: "统计分析", subtitle: "Analytics", roles: ["teacher", "admin"] },
];

const writePermissions = {
  student: new Set(["enrollments"]),
  teacher: new Set(["students", "courses", "enrollments", "grades"]),
  admin: new Set(["students", "courses", "enrollments", "grades"]),
};

const pageState = {
  dashboard: { filters: {}, table: { page: 1, pageSize: 10, sort: null } },
  students: { filters: {}, editing: null, table: { page: 1, pageSize: 10, sort: null } },
  courses: { filters: {}, editing: null, table: { page: 1, pageSize: 10, sort: null } },
  enrollments: { filters: {}, table: { page: 1, pageSize: 10, sort: null } },
  grades: { filters: {}, table: { page: 1, pageSize: 10, sort: null } },
  analytics: { filters: {}, table: { page: 1, pageSize: 10, sort: null } },
};

const state = {
  currentPage: "dashboard",
  user: loadSession(),
};

const elements = {
  loginScreen: document.getElementById("loginScreen"),
  workspace: document.getElementById("workspace"),
  navList: document.getElementById("navList"),
  content: document.getElementById("content"),
  pageTitle: document.getElementById("pageTitle"),
  currentModuleLabel: document.getElementById("currentModuleLabel"),
  loginForm: document.getElementById("loginForm"),
  usernameInput: document.getElementById("usernameInput"),
  passwordInput: document.getElementById("passwordInput"),
  loginError: document.getElementById("loginError"),
  exitSystemButton: document.getElementById("exitSystemButton"),
  exitModuleButton: document.getElementById("exitModuleButton"),
  quickCreateButton: document.getElementById("quickCreateButton"),
  userCard: document.getElementById("userCard"),
};

const studentFields = [
  { name: "student_id", label: "学号", placeholder: "7位学号，如 2025001", required: true },
  { name: "name", label: "姓名", required: true },
  { name: "gender", label: "性别", type: "select", options: ["男", "女"], required: true },
  { name: "birth_date", label: "出生日期", type: "date", required: true },
  { name: "department", label: "院系", placeholder: "电子信息工程学院", required: true },
  { name: "grade", label: "年级", type: "number", placeholder: "2025", required: true },
];

const courseFields = [
  { name: "course_code", label: "课程编号", placeholder: "AI001", required: true },
  { name: "name", label: "课程名称", placeholder: "人工智能导论", required: true },
  { name: "credit", label: "学分", type: "number", placeholder: "3", required: true },
  { name: "teacher", label: "教师", placeholder: "李老师", required: true },
  { name: "schedule", label: "上课时间", placeholder: "周一1-2节", required: true },
  { name: "capacity", label: "容量", type: "number", placeholder: "60", required: true },
];

const enrollmentFields = [
  { name: "student_id", label: "学生学号", placeholder: "2025001", required: true },
  { name: "course_code", label: "课程编号", placeholder: "AI001", required: true },
  { name: "teacher", label: "教师", placeholder: "李老师", required: true },
  { name: "schedule", label: "上课时间", placeholder: "周一1-2节", required: true },
];

const gradeFields = [
  ...enrollmentFields,
  { name: "score", label: "分数", type: "number", placeholder: "88", required: true },
];

const pageMeta = {
  dashboard: {
    tableTitle: "预警学生名单",
    tableSubtitle: "GPA < 2.0 或存在不及格科目",
    columns: ["学号", "姓名", "GPA", "院系", "状态"],
    sideTitle: "院系统计",
  },
  students: {
    filters: [
      { name: "student_id", label: "学号" },
      { name: "name", label: "姓名" },
      { name: "department", label: "院系" },
      { name: "grade", label: "年级" },
    ],
    tableTitle: "学生列表",
    tableSubtitle: "数据来自 GET /api/students",
    columns: ["学号", "姓名", "性别", "出生日期", "院系", "年级", "GPA", "操作"],
    sideTitle: "新增学生",
    formFields: studentFields,
  },
  courses: {
    filters: [
      { name: "code", label: "课程编号" },
      { name: "name", label: "课程名称" },
      { name: "teacher", label: "教师" },
    ],
    tableTitle: "课程列表",
    tableSubtitle: "数据来自 GET /api/courses",
    columns: ["ID", "编号", "课程", "教师", "时间", "容量", "已选", "操作"],
    sideTitle: "新增课程",
    formFields: courseFields,
  },
  enrollments: {
    filters: [
      { name: "student_id", label: "学生学号" },
      { name: "course_code", label: "课程编号" },
    ],
    tableTitle: "选课记录",
    tableSubtitle: "输入学生学号查看选课记录，或输入课程编号查看课程学生",
    columns: ["学生学号", "课程编号", "课程名称", "教师", "上课时间", "操作"],
    sideTitle: "选课操作面板",
    formFields: enrollmentFields,
  },
  grades: {
    filters: [
      { name: "student_id", label: "学生学号" },
      { name: "course_code", label: "课程编号" },
    ],
    tableTitle: "成绩记录",
    tableSubtitle: "输入学生学号或课程编号查看成绩",
    columns: ["学生学号", "课程编号", "课程名称", "教师", "上课时间", "分数", "操作"],
    sideTitle: "成绩录入表单",
    formFields: gradeFields,
  },
  analytics: {
    tableTitle: "分析结果",
    tableSubtitle: "数据来自 GET /api/analytics/*",
    columns: ["院系", "学生数", "状态"],
    sideTitle: "成绩分布",
  },
};

const api = {
  login: (payload) => request("/api/auth/login", { method: "POST", body: payload, skipAuth: true }),
  me: () => request("/api/auth/me"),
  getOverview: () => request("/api/analytics/overview"),
  getWarnings: () => request("/api/analytics/warnings"),
  getGpaDistribution: () => request("/api/analytics/gpa-distribution"),
  getTeacherStats: () => request("/api/analytics/teacher-statistics"),
  listStudents: (filters = {}) => request("/api/students" + queryString(filters)),
  createStudent: (payload) => request("/api/students", { method: "POST", body: payload }),
  updateStudent: (studentId, payload) => request(`/api/students/${encodeURIComponent(studentId)}`, { method: "PUT", body: payload }),
  deleteStudent: (studentId) => request(`/api/students/${encodeURIComponent(studentId)}`, { method: "DELETE" }),
  listCourses: (filters = {}) => request("/api/courses" + queryString(filters)),
  createCourse: (payload) => request("/api/courses", { method: "POST", body: payload }),
  updateCourse: (courseId, payload) => request(`/api/courses/${encodeURIComponent(courseId)}`, { method: "PUT", body: payload }),
  deleteCourse: (courseId) => request(`/api/courses/${encodeURIComponent(courseId)}`, { method: "DELETE" }),
  createEnrollment: (payload) => request("/api/enrollments", { method: "POST", body: payload }),
  listStudentEnrollments: (studentId) => request(`/api/enrollments/students/${encodeURIComponent(studentId)}`),
  listCourseStudents: (courseCode) => request(`/api/enrollments/courses/${encodeURIComponent(courseCode)}`),
  dropEnrollment: (payload) => request("/api/enrollments" + queryString(payload), { method: "DELETE" }),
  recordGrade: (payload) => request("/api/grades", { method: "POST", body: payload }),
  deleteGrade: (payload) => request("/api/grades" + queryString(payload), { method: "DELETE" }),
  listStudentGrades: (studentId) => request(`/api/grades/students/${encodeURIComponent(studentId)}`),
  listCourseGrades: (courseCode) => request(`/api/grades/courses/${encodeURIComponent(courseCode)}`),
};

class ApiError extends Error {
  constructor(message, status, details = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function request(path, options = {}) {
  const init = { method: options.method || "GET", headers: options.headers || {} };
  if (!options.skipAuth && state.user?.access_token) {
    init.headers = {
      ...init.headers,
      Authorization: `Bearer ${state.user.access_token}`,
    };
  }
  if (options.body !== undefined) {
    init.headers = { "Content-Type": "application/json", ...init.headers };
    init.body = JSON.stringify(options.body);
  }

  const response = await fetch(API_BASE + path, init);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const details = Array.isArray(data?.detail) ? data.detail : [];
    throw new ApiError(formatApiError(data, response.status), response.status, details);
  }
  return data;
}

function queryString(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      search.set(key, String(value).trim());
    }
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

function formatApiError(data, status) {
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => `${fieldLabel(item.loc?.slice(-1)[0])}: ${item.msg}`).join("；");
  }
  if (data?.detail) return String(data.detail);
  return `请求失败，HTTP ${status}`;
}

function fieldLabel(fieldName) {
  const fields = Object.values(pageMeta).flatMap((meta) => meta.formFields || []);
  return fields.find((field) => field.name === fieldName)?.label || fieldName || "字段";
}

function loadSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSession(user) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
}

function getRoutePageId() {
  return window.location.hash.replace(/^#\/?/, "") || "login";
}

function navigate(pageId) {
  window.location.hash = `#/${pageId}`;
}

function handleRoute() {
  const route = getRoutePageId();
  const availableRoutes = getAvailableRoutes();
  const pageExists = availableRoutes.some((page) => page.id === route);

  if (!state.user) {
    showLogin();
    if (route !== "login") navigate("login");
    return;
  }

  if (route === "login") {
    navigate("dashboard");
    return;
  }

  state.currentPage = pageExists ? route : availableRoutes[0]?.id || "dashboard";
  showWorkspace();
  render().catch((error) => renderError(error));
}

function showLogin() {
  elements.loginScreen.classList.remove("is-hidden");
  elements.workspace.classList.add("is-hidden");
}

function showWorkspace() {
  elements.loginScreen.classList.add("is-hidden");
  elements.workspace.classList.remove("is-hidden");
}

async function login(role, username, password) {
  const cleanedUsername = username.trim();
  const cleanedPassword = password.trim();
  if (!cleanedUsername || !cleanedPassword) {
    elements.loginError.textContent = "用户名和密码都需要填写。";
    return;
  }

  elements.loginError.textContent = "正在登录...";
  let result;
  try {
    result = await api.login({
      role,
      username: cleanedUsername,
      password: cleanedPassword,
    });
  } catch (error) {
    elements.loginError.textContent = error.message;
    return;
  }

  state.user = {
    ...result.user,
    access_token: result.access_token,
  };
  saveSession(state.user);
  elements.loginError.textContent = "";
  navigate("dashboard");
}

function logout() {
  state.user = null;
  state.currentPage = "dashboard";
  clearSession();
  navigate("login");
}

async function render() {
  renderNav();
  renderUserCard();

  const route = getCurrentRoute();
  elements.pageTitle.textContent = route.title;
  elements.currentModuleLabel.textContent = route.subtitle;
  elements.quickCreateButton.textContent = route.id === "dashboard" ? "新建记录" : `新增${route.label.replace("管理", "")}`;
  elements.quickCreateButton.style.display = route.id === "dashboard" || canWrite(route.id) ? "" : "none";
  showLoading(route.title);

  const viewModel = await buildViewModel(route.id);
  elements.content.innerHTML = `
    ${renderNotice(viewModel.notice)}
    ${renderStats(viewModel.stats)}
    ${viewModel.chart ? renderAnalyticsLayout(viewModel) : renderManagementLayout(viewModel)}
  `;

  bindFilterEvents(route.id);
  bindFormEvents(route.id);
  bindTableActions();
}

function getCurrentRoute() {
  return getAvailableRoutes().find((page) => page.id === state.currentPage) || getAvailableRoutes()[0] || routes[0];
}

function getAvailableRoutes() {
  const role = state.user?.role;
  return routes.filter((page) => page.roles.includes(role));
}

function roleLabel(role) {
  const labels = { student: "学生", teacher: "教师", admin: "管理员" };
  return labels[role] || role || "未登录";
}

function canWrite(pageId) {
  const role = state.user?.role;
  return Boolean(role && writePermissions[role]?.has(pageId));
}

function showLoading(title) {
  elements.content.innerHTML = `
    <div class="loading-container">
      <span class="loading-text">正在加载 ${escapeHtml(title)}...</span>
    </div>
  `;
}

function renderError(error) {
  elements.content.innerHTML = `
    <section class="table-panel">
      <div class="empty-state error-state">
        <strong>页面加载失败</strong>
        <span>${escapeHtml(error.message || "未知错误")}</span>
        <button class="primary-action" data-action="reload">重新加载</button>
      </div>
    </section>
  `;
  elements.content.querySelector("[data-action='reload']")?.addEventListener("click", () => render());
}

function renderNotice(notice) {
  if (!notice) return "";
  return `<div class="notice ${notice.type || ""}">${escapeHtml(notice.text)}</div>`;
}

function renderNav() {
  elements.navList.innerHTML = getAvailableRoutes()
    .map((page) => `
      <button class="nav-item${page.id === state.currentPage ? " is-active" : ""}" data-page="${page.id}">
        <span class="nav-icon">${page.icon}</span>
        ${page.label}
      </button>
    `)
    .join("");

  elements.navList.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => navigate(button.dataset.page));
  });
}

function renderUserCard() {
  if (!state.user) return;
  elements.userCard.innerHTML = `
    <span>${roleLabel(state.user.role)}</span>
    <strong>${escapeHtml(state.user.display_name || state.user.username)}</strong>
  `;
}

async function buildViewModel(pageId) {
  switch (pageId) {
    case "dashboard":
      return buildDashboardView();
    case "students":
      return buildStudentsView();
    case "courses":
      return buildCoursesView();
    case "enrollments":
      return buildEnrollmentsView();
    case "grades":
      return buildGradesView();
    case "analytics":
      return buildAnalyticsView();
    default:
      return buildDashboardView();
  }
}

async function buildDashboardView() {
  const [overview, warnings, courses] = await Promise.all([
    api.getOverview(),
    api.getWarnings(),
    api.listCourses(),
  ]);
  const courseList = asArray(courses);
  const totalEnrollments = courseList.reduce((sum, course) => sum + numberValue(course.current_count), 0);
  const warningsList = asArray(warnings);
  const departments = Object.entries(overview.by_department || {}).sort((a, b) => b[1] - a[1]);

  return {
    ...pageMeta.dashboard,
    stats: [
      ["学生总数", String(overview.total || 0), `${departments.length} 个院系`],
      ["课程总数", String(courseList.length), "正常运营"],
      ["选课记录", String(totalEnrollments), "来自课程已选人数"],
      ["预警学生", String(warningsList.length), "需要重点关注"],
    ],
    rows: warningsList.slice(0, 20).map((item) => [
      item.student_id,
      item.name,
      formatNumber(item.gpa),
      item.department,
      `预警：${item.failed_courses || 0} 门不及格`,
    ]),
    sideItems: departments.map(([department, count]) => [department, `${count} 人`]),
  };
}

async function buildStudentsView() {
  const filters = cleanFilters(pageState.students.filters);
  const [students, warnings] = await Promise.all([api.listStudents(filters), api.getWarnings()]);
  const list = asArray(students);
  const warningIds = new Set(asArray(warnings).map((item) => item.student_id));
  const avgGpa = list.length ? list.reduce((sum, item) => sum + numberValue(item.gpa), 0) / list.length : null;

  return {
    ...pageMeta.students,
    filters,
    stats: [
      ["在籍学生", String(list.length), ""],
      ["2025 级", String(list.filter((item) => item.grade === 2025).length), ""],
      ["平均 GPA", avgGpa == null ? "N/A" : formatNumber(avgGpa), ""],
      ["学业预警", String(warningIds.size), "建议跟进辅导"],
    ],
    rows: list.map((student) => [
      student.student_id,
      student.name,
      student.gender,
      student.birth_date,
      student.department,
      student.grade,
      formatNumber(student.gpa),
      actionButtons([
        {
          label: "编辑",
          action: "edit-student",
          data: {
            studentId: student.student_id,
            name: student.name,
            gender: student.gender,
            birthDate: student.birth_date,
            department: student.department,
            grade: student.grade,
          },
        },
        { label: "删除", action: "delete-student", data: { studentId: student.student_id }, danger: true },
        warningIds.has(student.student_id) ? { label: "预警", kind: "pill-danger" } : { label: "正常", kind: "pill" },
      ]),
    ]),
  };
}

async function buildCoursesView() {
  const filters = cleanFilters(pageState.courses.filters);
  const apiFilters = { code: filters.code, teacher: filters.teacher };
  let courses = asArray(await api.listCourses(apiFilters));
  if (filters.name) {
    const name = filters.name.toLowerCase();
    courses = courses.filter((course) => String(course.name).toLowerCase().includes(name));
  }

  const totalCapacity = courses.reduce((sum, item) => sum + numberValue(item.capacity), 0);
  const totalSelected = courses.reduce((sum, item) => sum + numberValue(item.current_count), 0);
  const fullCourses = courses.filter((item) => numberValue(item.current_count) >= numberValue(item.capacity));
  const teacherCount = new Set(courses.map((item) => item.teacher)).size;

  return {
    ...pageMeta.courses,
    filters,
    stats: [
      ["课程总量", String(courses.length), ""],
      ["容量占用", `${totalSelected}/${totalCapacity}`, totalCapacity ? `${Math.round(totalSelected / totalCapacity * 100)}%` : ""],
      ["满员课程", String(fullCourses.length), fullCourses.length ? fullCourses.map((item) => item.course_code).join(", ") : "无"],
      ["教师人数", String(teacherCount), ""],
    ],
    rows: courses.map((course) => [
      course.id,
      course.course_code,
      course.name,
      course.teacher,
      course.schedule,
      course.capacity,
      course.current_count,
      actionButtons([
        {
          label: "编辑",
          action: "edit-course",
          data: {
            courseId: course.id,
            courseCode: course.course_code,
            name: course.name,
            credit: course.credit,
            teacher: course.teacher,
            schedule: course.schedule,
            capacity: course.capacity,
          },
        },
        { label: "删除", action: "delete-course", data: { courseId: course.id }, danger: true },
        numberValue(course.current_count) >= numberValue(course.capacity)
          ? { label: "满员", kind: "pill-danger" }
          : { label: "可选", kind: "pill" },
      ]),
    ]),
    sideItems: fullCourses.length
      ? fullCourses.map((course) => [`${course.course_code} ${course.name}`, "课程已满，后续选课会被拒绝"])
      : [["无满员课程", "所有课程仍有余量"]],
  };
}

async function buildEnrollmentsView() {
  const filters = cleanFilters(pageState.enrollments.filters);
  const meta = { ...pageMeta.enrollments, filters };

  if (filters.student_id) {
    const list = asArray(await api.listStudentEnrollments(filters.student_id));
    return {
      ...meta,
      stats: [
        ["选课记录", String(list.length), "当前学生"],
        ["查询方式", "按学生", filters.student_id],
      ],
      rows: list.map((item) => [
        item.student_id,
        item.course_code,
        item.course_name,
        item.teacher,
        item.schedule,
        actionButtons([
          {
            label: "退课",
            action: "drop-enrollment",
            data: {
              studentId: item.student_id,
              courseCode: item.course_code,
              teacher: item.teacher,
              schedule: item.schedule,
            },
            danger: true,
          },
        ]),
      ]),
    };
  }

  if (filters.course_code) {
    const list = asArray(await api.listCourseStudents(filters.course_code));
    return {
      ...meta,
      columns: ["学号", "姓名", "性别", "院系", "年级", "GPA"],
      stats: [
        ["选课学生", String(list.length), "当前课程"],
        ["查询方式", "按课程", filters.course_code],
      ],
      rows: list.map((student) => [
        student.student_id,
        student.name,
        student.gender,
        student.department,
        student.grade,
        formatNumber(student.gpa),
      ]),
    };
  }

  return {
    ...meta,
    notice: { text: "请输入学生学号或课程编号后查询选课记录。", type: "info" },
    stats: [
      ["选课记录", "0", "等待查询"],
      ["操作方式", "API", "支持选课和退课"],
    ],
    rows: [],
  };
}

async function buildGradesView() {
  const filters = cleanFilters(pageState.grades.filters);
  const meta = { ...pageMeta.grades, filters };

  if (filters.student_id) {
    const list = asArray(await api.listStudentGrades(filters.student_id));
    return {
      ...meta,
      stats: [
        ["成绩记录", String(list.length), "当前学生"],
        ["查询方式", "按学生", filters.student_id],
      ],
      rows: list.map((grade) => [
        filters.student_id,
        grade.course_code,
        grade.course_name,
        grade.teacher,
        grade.schedule,
        grade.score,
        actionButtons([
          {
            label: "删除",
            action: "delete-grade",
            data: {
              studentId: filters.student_id,
              courseCode: grade.course_code,
              teacher: grade.teacher,
              schedule: grade.schedule,
            },
            danger: true,
          },
        ]),
      ]),
    };
  }

  if (filters.course_code) {
    const list = asArray(await api.listCourseGrades(filters.course_code));
    return {
      ...meta,
      columns: ["学生学号", "姓名", "课程编号", "课程名称", "分数"],
      stats: [
        ["成绩记录", String(list.length), "当前课程"],
        ["查询方式", "按课程", filters.course_code],
      ],
      rows: list.map((grade) => [
        grade.student_id,
        grade.student_name,
        grade.course_code,
        grade.course_name,
        grade.score,
      ]),
    };
  }

  return {
    ...meta,
    notice: { text: "请输入学生学号或课程编号后查询成绩。成绩提交时会自动更新学生 GPA。", type: "info" },
    stats: [
      ["成绩记录", "0", "等待查询"],
      ["操作方式", "API", "支持录入和覆盖"],
    ],
    rows: [],
  };
}

async function buildAnalyticsView() {
  const [gpaStats, overview, teacherStats] = await Promise.all([
    api.getGpaDistribution(),
    api.getOverview(),
    api.getTeacherStats(),
  ]);
  const departments = Object.entries(overview.by_department || {}).sort((a, b) => b[1] - a[1]);
  const teachers = asArray(teacherStats);

  return {
    ...pageMeta.analytics,
    chart: true,
    stats: [
      ["平均 GPA", gpaStats.average == null ? "N/A" : formatNumber(gpaStats.average), "全样本"],
      ["成绩方差", gpaStats.var == null ? "N/A" : formatNumber(gpaStats.var), ""],
      ["通过率", gpaStats.pass_rate == null ? "N/A" : `${formatNumber(gpaStats.pass_rate * 100)}%`, ""],
      ["优秀率", gpaStats.excellent_rate == null ? "N/A" : `${formatNumber(gpaStats.excellent_rate * 100)}%`, ""],
    ],
    rows: departments.map(([department, count]) => [
      department,
      count,
      count > 50 ? "活跃" : "正常",
    ]),
    chartData: departments,
    sideItems: [
      ["样本总数", gpaStats.count != null ? String(gpaStats.count) : "暂无数据"],
      ["标准差", gpaStats.std != null ? formatNumber(gpaStats.std) : "暂无数据"],
      ["最低 GPA", gpaStats.min != null ? formatNumber(gpaStats.min) : "暂无数据"],
      ["最高 GPA", gpaStats.max != null ? formatNumber(gpaStats.max) : "暂无数据"],
      ["教师统计", `${teachers.length} 位教师有课程数据`],
    ],
  };
}

function renderStats(stats = []) {
  const cards = stats.filter(([label, value]) => label && value !== undefined && value !== "");
  if (!cards.length) return "";
  return `
    <div class="stats-grid">
      ${cards.map(([label, value, hint]) => `
        <article class="stat-card">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <small>${escapeHtml(hint || "")}</small>
        </article>
      `).join("")}
    </div>
  `;
}

function renderManagementLayout(viewModel) {
  return `
    <div class="section-layout">
      <section class="table-panel">
        ${renderPanelTitle(viewModel.tableTitle, viewModel.tableSubtitle)}
        ${renderFilters(viewModel)}
        ${renderTable(viewModel)}
      </section>
      <aside class="panel">
        ${renderSidePanel(viewModel)}
      </aside>
    </div>
  `;
}

function renderAnalyticsLayout(viewModel) {
  return `
    <div class="section-layout">
      <section class="table-panel">
        ${renderPanelTitle("院系学生分布", "数据来自后端统计接口")}
        ${renderChart(viewModel.chartData || [])}
      </section>
      <aside class="panel">
        ${renderSidePanel(viewModel)}
      </aside>
    </div>
    <section class="table-panel">
      ${renderPanelTitle(viewModel.tableTitle, viewModel.tableSubtitle)}
      ${renderTable(viewModel)}
    </section>
  `;
}

function renderPanelTitle(title, subtitle) {
  return `
    <div class="panel-title">
      <div>
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(subtitle || "")}</p>
      </div>
    </div>
  `;
}

function renderFilters(viewModel) {
  if (!viewModel.filters || !pageMeta[state.currentPage].filters) return "";
  const filters = pageMeta[state.currentPage].filters;
  return `
    <div class="filter-row">
      ${filters.map((filter) => `
        <input type="text" name="${filter.name}" value="${escapeAttr(viewModel.filters[filter.name] || "")}" placeholder="${escapeAttr(filter.label)}">
      `).join("")}
    </div>
  `;
}

function renderTable(viewModel) {
  const columns = viewModel.columns || [];
  const rows = viewModel.rows || [];
  if (!rows.length) {
    return `<div class="empty-state">暂无数据，请先新增数据或调整筛选条件</div>`;
  }
  const tableState = getTableState();
  const sortedRows = sortRows(rows, tableState.sort, columns);
  const totalPages = Math.max(1, Math.ceil(sortedRows.length / tableState.pageSize));
  tableState.page = Math.min(Math.max(1, tableState.page), totalPages);
  const start = (tableState.page - 1) * tableState.pageSize;
  const pageRows = sortedRows.slice(start, start + tableState.pageSize);

  return `
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>${columns.map((column, index) => renderTableHeader(column, index, tableState.sort)).join("")}</tr>
        </thead>
        <tbody>
          ${pageRows.map((row) => `
            <tr>${row.map((cell) => `<td>${formatCell(cell)}</td>`).join("")}</tr>
          `).join("")}
        </tbody>
      </table>
    </div>
    ${renderPagination(sortedRows.length, tableState)}
  `;
}

function renderTableHeader(column, index, sort) {
  if (column === "操作") {
    return `<th>${escapeHtml(column)}</th>`;
  }
  const active = sort?.index === index;
  const arrow = active ? (sort.direction === "asc" ? " ↑" : " ↓") : "";
  return `
    <th>
      <button class="table-sort" data-action="sort-table" data-index="${index}">
        ${escapeHtml(column)}${arrow}
      </button>
    </th>
  `;
}

function renderPagination(total, tableState) {
  const start = total === 0 ? 0 : (tableState.page - 1) * tableState.pageSize + 1;
  const end = Math.min(total, tableState.page * tableState.pageSize);
  const totalPages = Math.max(1, Math.ceil(total / tableState.pageSize));
  return `
    <div class="pagination">
      <span>显示 ${start}-${end} / ${total}</span>
      <div class="pagination-controls">
        <select data-action="page-size" aria-label="每页条数">
          ${[5, 10, 20, 50].map((size) => `<option value="${size}" ${size === tableState.pageSize ? "selected" : ""}>${size} 条/页</option>`).join("")}
        </select>
        <button class="subtle-button" data-action="page-prev" ${tableState.page <= 1 ? "disabled" : ""}>上一页</button>
        <span>${tableState.page} / ${totalPages}</span>
        <button class="subtle-button" data-action="page-next" ${tableState.page >= totalPages ? "disabled" : ""}>下一页</button>
      </div>
    </div>
  `;
}

function sortRows(rows, sort, columns) {
  if (!sort || columns[sort.index] === "操作") return rows;
  return [...rows].sort((left, right) => {
    const a = sortableValue(left[sort.index]);
    const b = sortableValue(right[sort.index]);
    const result = a.localeCompare(b, "zh-CN", { numeric: true, sensitivity: "base" });
    return sort.direction === "asc" ? result : -result;
  });
}

function sortableValue(value) {
  if (value && typeof value === "object" && value.__html) return value.__html.replace(/<[^>]*>/g, "");
  return String(value ?? "");
}

function getTableState() {
  const page = pageState[state.currentPage];
  page.table ||= { page: 1, pageSize: 10, sort: null };
  return page.table;
}

function formatCell(cell) {
  if (cell && typeof cell === "object" && cell.__html) return cell.__html;
  const text = String(cell ?? "");
  const dangerWords = ["预警", "满员", "不及格", "失败"];
  const warnWords = ["关注", "等待", "接近"];
  const isDanger = dangerWords.some((word) => text.includes(word));
  const isWarn = warnWords.some((word) => text.includes(word));
  if (isDanger || isWarn) {
    return `<span class="status-pill${isDanger ? " danger" : " warn"}">${escapeHtml(text)}</span>`;
  }
  return escapeHtml(text);
}

function renderSidePanel(viewModel) {
  if (viewModel.formFields) {
    if (!canWrite(state.currentPage)) {
      return `
        ${renderPanelTitle(viewModel.sideTitle, "当前角色只有查看权限")}
        <div class="empty-state compact-state">当前账号不能在此模块执行新增、编辑或删除操作。</div>
      `;
    }
    const editing = pageState[state.currentPage]?.editing;
    const modeText = editing ? "编辑模式" : "新增模式";
    const submitText = editing ? "保存修改" : "提交";
    return `
      ${renderPanelTitle(viewModel.sideTitle, `${modeText}，填写后提交到后端 API`)}
      <div class="form-stack" data-page="${state.currentPage}">
        ${editing ? `<div class="edit-banner">正在编辑：${escapeHtml(editing.title)}</div>` : ""}
        ${viewModel.formFields.map((field) => renderField(field, editing?.values || {})).join("")}
        <div class="form-actions">
          <button class="primary-action" data-action="submit-form">${submitText}</button>
          ${editing ? `<button class="subtle-button" data-action="cancel-edit" type="button">取消编辑</button>` : ""}
        </div>
        <span class="form-feedback" aria-live="polite"></span>
      </div>
    `;
  }

  const items = viewModel.sideItems?.length ? viewModel.sideItems : [["暂无数据", "完成数据录入后这里会自动更新"]];
  return `
    ${renderPanelTitle(viewModel.sideTitle, "随当前模块数据自动更新")}
    <div class="timeline">
      ${items.map(([title, desc]) => `
        <div class="timeline-item">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(desc)}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function renderField(field, values = {}) {
  const value = values[field.name] ?? "";
  if (field.type === "select") {
    return `
      <div class="field">
        <label for="${field.name}">${escapeHtml(field.label)}</label>
        <select id="${field.name}" name="${field.name}" ${field.required ? "required" : ""}>
          <option value="">请选择</option>
          ${field.options.map((option) => `<option value="${escapeAttr(option)}" ${String(value) === option ? "selected" : ""}>${escapeHtml(option)}</option>`).join("")}
        </select>
      </div>
    `;
  }

  return `
    <div class="field">
      <label for="${field.name}">${escapeHtml(field.label)}</label>
      <input id="${field.name}" type="${field.type || "text"}" name="${field.name}" value="${escapeAttr(value)}" placeholder="${escapeAttr(field.placeholder || field.label)}" ${field.required ? "required" : ""}>
    </div>
  `;
}

function renderChart(data) {
  if (!data.length) return `<div class="empty-state">暂无统计数据</div>`;
  const max = Math.max(...data.map(([, value]) => value), 1);
  return `
    <div class="chart-row">
      ${data.map(([label, value]) => {
        const height = Math.max(34, Math.round((value / max) * 190));
        return `<div class="bar" style="height:${height}px"><strong>${value}</strong><span>${escapeHtml(label)}</span></div>`;
      }).join("")}
    </div>
  `;
}

function bindFilterEvents(pageId) {
  const filterInputs = elements.content.querySelectorAll(".filter-row input");
  if (!filterInputs.length) return;

  let timer;
  filterInputs.forEach((input) => {
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const nextFilters = {};
        filterInputs.forEach((item) => {
          nextFilters[item.name] = item.value.trim();
        });
        pageState[pageId].filters = nextFilters;
        getTableStateFor(pageId).page = 1;
        render().catch(renderError);
      }, 350);
    });
  });
}

function bindFormEvents(pageId) {
  const formStack = elements.content.querySelector(".form-stack");
  if (!formStack) return;

  const button = formStack.querySelector("[data-action='submit-form']");
  const cancelButton = formStack.querySelector("[data-action='cancel-edit']");
  const feedback = formStack.querySelector(".form-feedback");
  cancelButton?.addEventListener("click", () => {
    pageState[pageId].editing = null;
    render().catch(renderError);
  });

  button?.addEventListener("click", async () => {
    clearFieldErrors(formStack);
    feedback.className = "form-feedback";
    feedback.textContent = "提交中...";

    try {
      const payload = readFormPayload(formStack, pageId);
      await submitPageForm(pageId, payload);
      feedback.className = "form-feedback success";
      feedback.textContent = "操作成功";
      formStack.querySelectorAll("input, select").forEach((input) => {
        input.value = "";
      });
      await render();
    } catch (error) {
      applyFieldErrors(formStack, error);
      feedback.className = "form-feedback error";
      feedback.textContent = error.message;
    }
  });
}

function clearFieldErrors(formStack) {
  formStack.querySelectorAll(".field.has-error").forEach((field) => {
    field.classList.remove("has-error");
    field.querySelector(".field-error")?.remove();
  });
}

function applyFieldErrors(formStack, error) {
  if (!Array.isArray(error.details)) return;

  error.details.forEach((detail) => {
    const fieldName = detail.loc?.slice(-1)[0];
    if (!fieldName) return;
    const input = formStack.querySelector(`[name="${CSS.escape(fieldName)}"]`);
    if (!input) return;

    const field = input.closest(".field");
    if (!field) return;
    field.classList.add("has-error");
    const message = document.createElement("span");
    message.className = "field-error";
    message.textContent = detail.msg || "字段不合法";
    field.appendChild(message);
  });
}

function readFormPayload(formStack, pageId) {
  const payload = {};
  formStack.querySelectorAll("input, select").forEach((input) => {
    payload[input.name] = input.value.trim();
  });

  const fields = pageMeta[pageId]?.formFields || [];
  for (const field of fields) {
    if (field.required && !payload[field.name]) {
      throw new Error(`请填写${field.label}`);
    }
  }

  if (pageId === "students") {
    payload.grade = toInteger(payload.grade, "年级");
  }
  if (pageId === "courses") {
    payload.credit = toInteger(payload.credit, "学分");
    payload.capacity = toInteger(payload.capacity, "容量");
  }
  if (pageId === "grades") {
    payload.score = toNumber(payload.score, "分数");
  }
  return payload;
}

async function submitPageForm(pageId, payload) {
  switch (pageId) {
    case "students": {
      const editing = pageState.students.editing;
      const result = editing
        ? await api.updateStudent(editing.id, payload)
        : await api.createStudent(payload);
      pageState.students.editing = null;
      return result;
    }
    case "courses": {
      const editing = pageState.courses.editing;
      const result = editing
        ? await api.updateCourse(editing.id, payload)
        : await api.createCourse(payload);
      pageState.courses.editing = null;
      return result;
    }
    case "enrollments":
      return api.createEnrollment(payload);
    case "grades":
      return api.recordGrade(payload);
    default:
      throw new Error("当前页面不支持新增操作");
  }
}

function bindTableActions() {
  const uiActions = new Set(["submit-form", "reload", "cancel-edit", "sort-table", "page-size", "page-prev", "page-next"]);
  elements.content.querySelectorAll("[data-action]").forEach((button) => {
    const action = button.dataset.action;
    if (uiActions.has(action)) return;

    button.addEventListener("click", async () => {
      if (button.disabled) return;
      try {
        await runTableAction(button);
        await render();
      } catch (error) {
        alert(error.message);
      }
    });
  });

  elements.content.querySelector("[data-action='page-size']")?.addEventListener("change", (event) => {
    const table = getTableState();
    table.pageSize = Number.parseInt(event.target.value, 10) || 10;
    table.page = 1;
    render().catch(renderError);
  });

  elements.content.querySelector("[data-action='page-prev']")?.addEventListener("click", () => {
    const table = getTableState();
    table.page = Math.max(1, table.page - 1);
    render().catch(renderError);
  });

  elements.content.querySelector("[data-action='page-next']")?.addEventListener("click", () => {
    const table = getTableState();
    table.page += 1;
    render().catch(renderError);
  });

  elements.content.querySelectorAll("[data-action='sort-table']").forEach((button) => {
    button.addEventListener("click", () => {
      const table = getTableState();
      const index = Number.parseInt(button.dataset.index, 10);
      const current = table.sort;
      table.sort = current?.index === index && current.direction === "asc"
        ? { index, direction: "desc" }
        : { index, direction: "asc" };
      table.page = 1;
      render().catch(renderError);
    });
  });
}

function getTableStateFor(pageId) {
  const page = pageState[pageId];
  page.table ||= { page: 1, pageSize: 10, sort: null };
  return page.table;
}

async function runTableAction(button) {
  const data = button.dataset;
  switch (data.action) {
    case "delete-student":
      if (!confirm(`确定删除学生 ${data.studentId} 吗？`)) return;
      if (pageState.students.editing?.id === data.studentId) pageState.students.editing = null;
      return api.deleteStudent(data.studentId);
    case "edit-student":
      pageState.students.editing = {
        id: data.studentId,
        title: `${data.studentId} ${data.name}`,
        values: {
          student_id: data.studentId,
          name: data.name,
          gender: data.gender,
          birth_date: data.birthDate,
          department: data.department,
          grade: data.grade,
        },
      };
      return;
    case "delete-course":
      if (!confirm(`确定删除课程 ID ${data.courseId} 吗？`)) return;
      if (pageState.courses.editing?.id === data.courseId) pageState.courses.editing = null;
      return api.deleteCourse(data.courseId);
    case "edit-course":
      pageState.courses.editing = {
        id: data.courseId,
        title: `${data.courseCode} ${data.name}`,
        values: {
          course_code: data.courseCode,
          name: data.name,
          credit: data.credit,
          teacher: data.teacher,
          schedule: data.schedule,
          capacity: data.capacity,
        },
      };
      return;
    case "drop-enrollment":
      if (!confirm(`确定退掉 ${data.studentId} 的 ${data.courseCode} 课程吗？`)) return;
      return api.dropEnrollment({
        student_id: data.studentId,
        course_code: data.courseCode,
        teacher: data.teacher,
        schedule: data.schedule,
      });
    case "delete-grade":
      if (!confirm(`确定删除 ${data.studentId} 的 ${data.courseCode} 成绩吗？`)) return;
      return api.deleteGrade({
        student_id: data.studentId,
        course_code: data.courseCode,
        teacher: data.teacher,
        schedule: data.schedule,
      });
    default:
      throw new Error("未知操作");
  }
}

function actionButtons(actions) {
  const visibleActions = actions.filter(canUseAction);
  const html = visibleActions.map((item) => {
    if (item.kind === "pill" || item.kind === "pill-danger") {
      return `<span class="status-pill${item.kind === "pill-danger" ? " danger" : ""}">${escapeHtml(item.label)}</span>`;
    }
    const dataAttrs = Object.entries(item.data || {})
      .map(([key, value]) => `data-${kebabCase(key)}="${escapeAttr(value)}"`)
      .join(" ");
    return `
      <button
        class="subtle-button table-action${item.danger ? " danger-action" : ""}"
        data-action="${escapeAttr(item.action)}"
        ${dataAttrs}
        ${item.disabled ? "disabled" : ""}
        title="${escapeAttr(item.title || item.label)}"
      >${escapeHtml(item.label)}</button>
    `;
  }).join("");
  return { __html: `<div class="row-actions">${html}</div>` };
}

function canUseAction(item) {
  if (item.kind) return true;
  if (!item.action) return true;
  const mutatingActions = new Set([
    "edit-student",
    "delete-student",
    "edit-course",
    "delete-course",
    "drop-enrollment",
    "delete-grade",
  ]);
  return !mutatingActions.has(item.action) || canWrite(state.currentPage);
}

function cleanFilters(filters = {}) {
  const cleaned = {};
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      cleaned[key] = String(value).trim();
    }
  });
  return cleaned;
}

function toInteger(value, label) {
  const number = Number.parseInt(value, 10);
  if (!Number.isFinite(number)) throw new Error(`${label} 必须是整数`);
  return number;
}

function toNumber(value, label) {
  const number = Number.parseFloat(value);
  if (!Number.isFinite(number)) throw new Error(`${label} 必须是数字`);
  return number;
}

function numberValue(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function formatNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "N/A";
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function kebabCase(value) {
  return String(value).replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
}

function escapeHtml(value) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(value ?? "").replace(/[&<>"']/g, (char) => map[char]);
}

function escapeAttr(value) {
  return escapeHtml(value);
}

function updateRoleVisual() {
  document.querySelectorAll(".role-option").forEach((label) => {
    const input = label.querySelector("input");
    label.classList.toggle("is-active", input.checked);
  });
}

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(elements.loginForm);
  await login(
    formData.get("role"),
    elements.usernameInput.value,
    elements.passwordInput.value,
  );
});

elements.loginForm.querySelectorAll('input[name="role"]').forEach((input) => {
  input.addEventListener("change", updateRoleVisual);
});

elements.exitSystemButton.addEventListener("click", logout);
elements.exitModuleButton.addEventListener("click", () => navigate("dashboard"));
elements.quickCreateButton.addEventListener("click", () => {
  if (pageState[state.currentPage]?.editing) {
    pageState[state.currentPage].editing = null;
    render().catch(renderError);
  }
  if (state.currentPage === "dashboard") {
    navigate("students");
    return;
  }
  elements.content.querySelector(".form-stack input, .form-stack select")?.focus();
});

window.addEventListener("hashchange", handleRoute);

if (!window.location.hash) {
  navigate(state.user ? "dashboard" : "login");
} else {
  handleRoute();
}
