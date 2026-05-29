# 校园数据管理与智能分析系统

## 项目定位

本项目以校园学生、课程、选课、成绩管理为基础，逐步扩展为面向数据分析和软硬结合场景的校园数据平台。当前目标不是单纯堆功能，而是先保证核心业务稳定，再加入数据库、统计分析、API 和硬件数据采集扩展。

未来方向：

- 软件侧：学生管理、课程管理、成绩管理、数据分析、API 接口
- AI 侧：成绩趋势分析、GPA 预警、异常数据检测
- 硬件侧：预留教室环境数据采集接口，如温度、湿度、光照等传感器数据

## 当前进度

已经具备的基础：

- 项目目录已按 `core / data / algorithms / utils / api / tests` 分层
- 已有学生、课程、成绩相关模型和服务模块
- 已开始接入 SQLAlchemy / Alembic
- 已新增 Repository 层，封装学生、课程、选课、成绩的数据库操作
- 已新增统一业务服务层，支持内存仓库测试和数据库仓库实际接入
- 已新增 `core/interpretation/data_views.py` 和 reader 接口，用于统一实时计算派生数据
- 已接入 FastAPI，提供学生、课程、选课、成绩和分析接口
- 已接入登录认证接口，前端按学生、教师、管理员角色控制模块和操作权限，后端 API 也会强制校验登录和角色权限
- 核心数据、派生数据、业务规则和数据访问开始分离

当前核心原则：

```text
核心数据只保存一份；
统计、筛选、索引等派生数据通过函数实时计算；
业务模块通过统一数据视图接口读取派生数据。
```

## 运行方式

### 安装依赖

```powershell
cd "E:\new python\campus_management"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果本机没有可用虚拟环境，可先执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 启动 FastAPI

```powershell
uvicorn api.app:app --reload
```

启动后访问：

```text
接口文档：http://127.0.0.1:8000/docs
OpenAPI：http://127.0.0.1:8000/openapi.json
```

如果需要同时访问前端页面和 API，请启动 `main:app`：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```

默认登录账号：

```text
学生：student / student123
教师：teacher / teacher123
管理员：admin / admin123
```

### 运行测试

```powershell
python -m pytest -q
```

只运行 API 测试：

```powershell
python -m pytest tests/test_api.py -q
```

## API 接口概览

认证：

```text
POST /api/auth/login
GET  /api/auth/me
```

学生：

```text
POST   /api/students
GET    /api/students
GET    /api/students/{student_id}
PUT    /api/students/{student_id}
DELETE /api/students/{student_id}
```

课程：

```text
POST /api/courses
GET  /api/courses
```

选课：

```text
POST   /api/enrollments
DELETE /api/enrollments?student_id=...&course_code=...&teacher=...&schedule=...
POST   /api/enrollments/drop
GET    /api/enrollments/students/{student_id}
GET    /api/enrollments/courses/{course_code}
```

成绩：

```text
POST /api/grades
GET  /api/grades/students/{student_id}
GET  /api/grades/courses/{course_code}
```

分析：

```text
GET /api/analytics/overview
GET /api/analytics/warnings
GET /api/analytics/gpa-distribution
GET /api/analytics/score-distribution
GET /api/analytics/teacher-statistics
```

常用错误码约定：

```text
401：未登录、Token 缺失或 Token 失效
403：已登录，但当前角色无权执行此操作
400：业务规则不允许，如容量满、时间冲突、未选课不能录成绩
404：学生、课程或记录不存在
409：重复创建或违反唯一约束
422：请求参数格式不符合 Pydantic 校验
500：未预期的系统错误
```

## 当前后端主通路

当前项目的主后端通路是：

```text
api/routers
-> core/services/backend_services.py
-> data/repositories
-> core/models/mysqlDB.py
-> MySQL / 测试 SQLite
```

各层职责：

```text
api/routers：
处理 HTTP 请求、Pydantic 校验、HTTP 状态码和响应模型。

core/services/backend_services.py：
当前主业务层，负责学生、课程、选课、成绩、GPA 等业务规则。

data/repositories：
数据访问层，封装 SQLAlchemy 查询、写入、缓存同步。

core/interpretation：
数据解释层，通过 reader / DataView 做统计、分布、预警等派生分析。

core/cache.py：
缓存层，用于查询结果和派生索引加速；数据库仍是唯一可信数据源。
```

早期学习阶段的内存命令行业务模块已经移动到：

```text
core/legacy_services
```

这些文件只作为历史学习版本和内存流程测试参考保留；后续新功能应优先接入 `backend_services.py`、Repository、DataView 和 API 这条主通路。

## 后续完成路径

### 第一阶段：稳定内存版核心业务

目标：不依赖数据库，先让完整业务流程跑通。

任务：

1. 完善学生增删改查、模糊查询、批量导入
2. 完善课程添加、查询、容量管理、教师统计
3. 完成选课、退课、时间冲突、先修课程、等待队列
4. 完成成绩录入、修改、批量导入、GPA 自动计算、学业预警

完成标志：

```text
学生创建 -> 选课 -> 录入成绩 -> 计算 GPA -> 触发预警
```

### 第二阶段：统一数据访问与派生数据计算

目标：继续减少耦合，避免多个字典重复保存同一类信息。

任务：

1. 保留核心数据源：`students_dict`、`all_courses_dict`、必要等待队列
2. 将院系统计、年级统计、教师统计、GPA 分布等放入 `data_views.py`
3. 服务层只调用统一接口，不直接维护派生统计字典

### 第三阶段：接入数据库

目标：让数据可以持久化。

建议优先实现 4 张表：

```text
students
courses
enrollments
grades
```

任务：

1. 整理 SQLAlchemy 模型
2. 使用 Alembic 管理迁移
3. 实现基础增删改查
4. 保证程序重启后数据不丢失

### 第四阶段：数据分析与可视化

目标：体现 AI 和数据分析方向。

任务：

1. 成绩分布统计
2. GPA 分布统计
3. 学业预警名单
4. 成绩趋势分析
5. 使用 Matplotlib / Plotly 输出图表

### 第五阶段：FastAPI 接口

目标：把系统变成可被前端、硬件端或 AI 服务调用的平台。

建议接口：

```text
POST /students
GET /students
POST /courses
POST /enrollments
POST /grades
GET /analytics/gpa
GET /analytics/warnings
```

### 第六阶段：软硬结合扩展

目标：为未来电子 + AI 方向预留接口。

先用模拟数据实现：

```text
device_id
classroom
temperature
humidity
light
timestamp
```

任务：

1. 生成模拟教室环境数据
2. 保存环境数据
3. 查询某教室环境变化
4. 判断温湿度或光照异常
5. 绘制环境趋势图

后续可替换为 ESP32、STM32、Arduino 等真实硬件采集数据。

### 第七阶段：测试与文档

目标：保证项目能稳定交付。

最低测试范围：

1. 学生添加、重复学号、查询
2. 课程容量、时间冲突
3. 选课、退课
4. 成绩录入、GPA 计算
5. 数据视图统计函数
6. 数据库保存与读取

文档补充：

1. 项目架构说明
2. 数据库表设计
3. API 接口说明
4. 运行方式
5. 软硬结合扩展说明

## 推荐完成顺序

```text
核心模型命名统一
-> 学生管理
-> 课程管理
-> 选课退课
-> 成绩与 GPA
-> data_views.py 数据视图整理
-> 数据库
-> 数据分析和图表
-> FastAPI
-> 硬件模拟数据
-> 测试
-> 文档
```

## 基本上线配置

当前项目已经支持用环境变量配置生产环境，不再需要把数据库密码写死在代码里。

核心环境变量：

```text
ENVIRONMENT=production
CAMPUS_AUTH_SECRET=一段足够长的随机密钥
DATABASE_URL=mysql+pymysql://user:password@host:3306/campus_db?charset=utf8mb4
CORS_ORIGINS=https://你的线上域名
INIT_DB_ON_STARTUP=false
```

说明：

- `DATABASE_URL`：线上数据库连接地址，推荐 MySQL。
- `CAMPUS_AUTH_SECRET`：Token 签名密钥，生产环境必须更换。
- `CORS_ORIGINS`：允许访问 API 的前端域名，多个域名用英文逗号分隔。
- `INIT_DB_ON_STARTUP`：演示环境可以设为 `true` 自动建表；正式环境建议用 Alembic 迁移，保持 `false`。

部署相关文件：

```text
.env.example
Dockerfile
.dockerignore
Procfile
render.yaml
docs/DEPLOYMENT_CHECKLIST.md
```

生产模式启动命令：

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

健康检查：

```text
GET /api/health
```

线上手动验收流程见：

```text
docs/DEPLOYMENT_CHECKLIST.md
```
