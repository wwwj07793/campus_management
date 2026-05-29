# 校园管理系统前端

这是一个不引入构建工具的 Vanilla JS 单页前端，由后端 `main.py` 直接托管。启动 FastAPI 后访问 `http://127.0.0.1:8000` 即可使用。

## 启动方式

```bash
cd 项目根目录
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

## 当前闭环

- 登录入口：学生/教师/管理员身份选择，调用后端 `/api/auth/login` 完成账号校验。
- 默认账号：`student/student123`、`teacher/teacher123`、`admin/admin123`。
- 模块权限：学生只显示学习相关模块；教师和管理员显示完整管理模块。
- 权限兜底：前端会隐藏无权操作，后端 API 也会返回 `401` 或 `403` 拦截未登录和越权请求。
- 总览页：读取学生总数、课程数、选课数、预警学生、院系统计。
- 学生管理：查询、新增、编辑、删除学生。
- 课程管理：查询、新增、编辑、删除课程。
- 选课管理：按学生查选课、按课程查学生、新增选课、退课。
- 成绩管理：按学生查成绩、按课程查成绩、录入或覆盖成绩、删除成绩。
- 统计分析：展示 GPA 分布、通过率、优秀率、院系分布、教师统计摘要。
- 表单体验：后端校验失败时，会显示错误信息并高亮对应字段。
- 表格体验：学生、课程、选课、成绩、统计表格支持列排序和分页。

## 前端代码结构

核心代码集中在 `app.js`：

- `routes`：页面路由和左侧导航配置。
- `pageMeta`：每个页面的筛选字段、表格列、表单字段。
- `api`：前端访问后端 API 的统一封装。
- `build*View()`：按页面组装展示数据。
- `render*()`：统一渲染统计卡片、表格、表单、图表、侧栏。
- `bind*Events()`：绑定筛选、表单提交、表格操作。

当前没有引入 Vue/React/Vite，是为了保留项目的低环境成本：后端启动后，前端就能直接访问。

## 已对接接口

```text
GET    /api/analytics/overview
GET    /api/analytics/warnings
GET    /api/analytics/gpa-distribution
GET    /api/analytics/teacher-statistics

POST   /api/auth/login
GET    /api/auth/me

GET    /api/students
POST   /api/students
DELETE /api/students/{student_id}

GET    /api/courses
POST   /api/courses
DELETE /api/courses/{course_id}

POST   /api/enrollments
DELETE /api/enrollments
GET    /api/enrollments/students/{student_id}
GET    /api/enrollments/courses/{course_code}

POST   /api/grades
DELETE /api/grades
GET    /api/grades/students/{student_id}
GET    /api/grades/courses/{course_code}
```

## 检查命令

```bash
node --check frontend-demo\app.js
.\.venv\Scripts\python.exe -m pytest -q
```

## 下一步待办

| 优先级 | 任务 | 目标 |
| --- | --- | --- |
| P0 | 浏览器端手动验收完整流程 | 用页面完成学生、课程、选课、成绩、统计闭环 |
| P1 | 浏览器自动化冒烟测试 | 本地安装 Playwright 后，检查页面登录和核心点击流程 |
| P2 | 登录接入真实用户模型 | 从演示登录升级到后端认证 |
| P2 | 图表增强 | 用更清晰的图表展示成绩、院系和教师统计 |
| P2 | 拆分前端文件 | 从单文件 `app.js` 拆成 API、状态、渲染和页面模块 |
