# 基本上线验收清单

## 1. 环境变量

生产环境至少需要配置：

```text
ENVIRONMENT=production
CAMPUS_AUTH_SECRET=一段足够长的随机密钥
DATABASE_URL=mysql+pymysql://user:password@host:3306/campus_db?charset=utf8mb4
CORS_ORIGINS=https://你的线上域名
INIT_DB_ON_STARTUP=false
```

演示环境如果没有迁移流程，可以临时设置：

```text
INIT_DB_ON_STARTUP=true
```

正式环境建议使用 Alembic 迁移，而不是长期依赖启动时自动建表。

## 2. 本地生产模式预检

```powershell
$env:DATABASE_URL="sqlite:///./campus_smoke.db"
$env:CAMPUS_AUTH_SECRET="local-smoke-secret"
$env:CORS_ORIGINS="http://127.0.0.1:8000"
$env:INIT_DB_ON_STARTUP="true"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/health
```

## 3. Docker 预检

```bash
docker build -t campus-management .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./campus.db \
  -e CAMPUS_AUTH_SECRET=local-docker-secret \
  -e CORS_ORIGINS=http://127.0.0.1:8000 \
  -e INIT_DB_ON_STARTUP=true \
  campus-management
```

## 4. 线上手动验收流程

1. 访问首页，确认前端页面正常加载。
2. 访问 `/api/health`，确认返回 `{"status":"ok"}`。
3. 使用教师账号登录：`teacher / teacher123`。
4. 新增学生。
5. 新增课程。
6. 给学生选课。
7. 录入成绩。
8. 查询学生 GPA 是否更新。
9. 查看统计分析页是否刷新。
10. 测试时间冲突：创建同时间课程后再次选课，应返回业务错误。
11. 使用学生账号登录：`student / student123`。
12. 确认学生看不到学生管理和统计分析模块。
13. 直接请求教师接口，确认返回 `403`。
14. 退出登录后访问受保护 API，确认返回 `401`。

## 5. 上线前风险确认

- `DATABASE_URL` 不要写死在代码里。
- `CAMPUS_AUTH_SECRET` 不要使用默认值。
- `CORS_ORIGINS` 不要使用无关域名。
- MySQL 数据库需要开启备份。
- 正式生产建议补充 HTTPS、日志采集、慢查询监控和 Alembic 迁移流程。
