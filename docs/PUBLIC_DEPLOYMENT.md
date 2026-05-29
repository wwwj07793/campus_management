# 公共域名上线步骤

当前项目已经准备好以下部署文件：

```text
Dockerfile
Procfile
render.yaml
.env.example
docs/DEPLOYMENT_CHECKLIST.md
```

## 推荐路线：Render 默认公网域名

Render 部署成功后会给你一个类似这样的地址：

```text
https://campus-management.onrender.com
```

这个地址就是公网可访问入口，适合先完成实训展示和线上验收。

## 1. 推送到 GitHub

如果本地还没有 Git 仓库：

```bash
git init
git add .
git commit -m "prepare production deployment"
```

然后在 GitHub 新建仓库，例如：

```text
campus-management
```

把本地项目推上去：

```bash
git remote add origin https://github.com/<你的用户名>/campus-management.git
git branch -M main
git push -u origin main
```

## 2. 在 Render 创建服务

1. 打开 Render。
2. New -> Web Service。
3. 选择刚才的 GitHub 仓库。
4. Runtime 选择 Python，或直接让 Render 读取 `render.yaml`。
5. Start Command 使用：

```bash
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 3. 设置环境变量

Render 的 Environment 页面里填：

```text
ENVIRONMENT=production
CAMPUS_AUTH_SECRET=一段足够长的随机密钥
DATABASE_URL=mysql+pymysql://user:password@host:3306/campus_db?charset=utf8mb4
CORS_ORIGINS=https://你的服务名.onrender.com
INIT_DB_ON_STARTUP=true
```

说明：

- 第一次演示上线可以先把 `INIT_DB_ON_STARTUP` 设为 `true`，让 SQLAlchemy 自动建表。
- 长期正式上线建议改为 `false`，并使用 Alembic 管理迁移。
- 如果你暂时没有线上 MySQL，只做页面演示，可以临时使用 SQLite：

```text
DATABASE_URL=sqlite:///./campus.db
INIT_DB_ON_STARTUP=true
```

但 SQLite 不适合作为长期生产数据库。

## 4. 部署成功后验收

打开：

```text
https://你的服务名.onrender.com
https://你的服务名.onrender.com/docs
https://你的服务名.onrender.com/api/health
```

默认账号：

```text
student / student123
teacher / teacher123
admin / admin123
```

完整验收流程见：

```text
docs/DEPLOYMENT_CHECKLIST.md
```

## 当前我不能直接替你完成的部分

真正生成 `onrender.com` 公网地址，需要你的 Render/GitHub 账号授权。当前本机没有 GitHub CLI，也没有可用的部署平台登录态，所以我不能直接创建线上服务。

你完成 GitHub 和 Render 授权后，这个项目已经具备直接部署条件。
