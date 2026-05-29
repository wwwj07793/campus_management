# 校园数据管理与智能分析系统

## 项目概述

Python 3.12 + SQLAlchemy + FastAPI + Pandas 的校园数据管理平台。当前处于第三阶段（数据库层已完成，API 层待开发）。

## 上下文监控规则

### 你需要主动做的事

在对话过程中，你需要持续留意以下信号并在必要时提醒我：

**1. 上下文膨胀信号**
- 当前对话已经覆盖了 5 个以上的不相关话题
- 同一问题被重复讨论了 3 次以上但无进展
- 对话摘要中出现了大段与校园管理系统无关的内容

**2. 上下文污染信号**
- 发现自己在引用其他项目（如 demo 项目）的代码或约定
- 对话中混入了另一个技术栈的讨论（如突然在 Python 项目中大量讨论 Node.js）
- 我给出的指令里包含了明显不属于当前项目的文件路径或概念

**3. 提醒格式**

当检测到以上信号时，用这个格式提醒我：

```
⚠️ 上下文提醒：[具体问题描述]
当前状态：[简单描述对话走向]
建议操作：
  1. /compact — 压缩当前对话
  2. 新开会话 — 在新终端重新开始
  3. 继续 — 忽略此提醒
你选哪个？
```

**4. 重要限制**
- 只提醒，不自动执行任何清理操作
- 永远不主动清除缓存、记忆或对话历史
- 如果拿不准是否该提醒，宁可不提醒——我不需要噪音

## 决策权限

除非满足以下任一条件，否则无需询问，直接执行：
- 涉及删除文件、数据或记录
- 改动会被多处依赖的源头（如核心接口签名、基础模型字段、公共工具函数）

日常操作（新增功能、修复 bug、补测试、写文档、重组代码等）自行完成即可。

## 代码约定

- 核心数据只存一份，派生数据实时计算
- 业务逻辑走 `core/services/`，数据访问走 `data/repositories/`
- 数据库操作通过 Repository 接口，不直接操作 Session
- 新增功能优先补测试

## 当前项目结构

```
core/          # 核心层：models, services, interpretation, cache, exceptions
data/          # 数据层：repositories, database, migrations
api/           # API 层：FastAPI 路由、依赖、schemas、错误映射
algorithms/    # 算法层（待开发）
tests/         # 测试（pytest，当前约 61 个测试）
utils/         # 工具：decorators, validators
data_files/    # CSV 测试数据
```

## 多 AI 协作与 Git 交接规则

为了让 Claude Code、Codex 和用户之间的协作更顺畅，减少重复排查，请优先遵守下面的项目交接约定。

### 1. 优先使用 Git 记录阶段成果

如果项目根目录还没有 `.git`，先建立基线提交：

```powershell
cd "E:\new python\campus_management"
git init
git add .
git commit -m "baseline: current campus management project"
```

完成每个相对独立的任务后，提交一次小而清晰的 commit，例如：

```powershell
git status
git add 相关文件
git commit -m "feat: connect frontend to basic api"
```

推荐的提交粒度：
- `feat: add fastapi routers`
- `feat: connect frontend demo to api`
- `fix: align frontend fields with api schemas`
- `test: add api integration tests`
- `docs: update collaboration notes`

### 2. 切换 AI 工具前必须留下可追踪上下文

当 Claude Code 完成一段工作、准备交给 Codex 或用户检查时，请至少保留以下其中一种记录：

```powershell
git status
git log --oneline -5
```

如果暂时不方便提交，至少导出 diff：

```powershell
git diff > change.patch
```

交接说明建议包含：
- 本次改了哪些模块
- 入口命令是什么
- 已经跑过哪些测试
- 还没解决的风险或 TODO

### 3. Review 时优先让对方看增量

如果用户要求“检查 Claude Code 写的代码”或“检查最近改动”，优先使用：

```powershell
git log --oneline
git show HEAD
git diff baseline..HEAD
```

没有 Git 记录时，检查者只能全项目扫描，效率会低很多，也更容易漏掉上下文。

### 4. 避免两个 AI 同时修改同一片文件

建议按职责分工：
- Claude Code 负责某一轮主要实现时，Codex 优先做 review、测试和补丁。
- Codex 负责某一轮主要实现时，Claude Code 优先做 review、测试和补丁。
- 前端、API、数据库、解释层尽量分批处理，不要同时大改同一文件。

### 5. 每轮完成后的最低验证要求

后端或 API 改动后至少运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

前端 JS 改动后至少运行：

```powershell
node --check frontend-demo\app.js
```

如果涉及前后端联调，应明确说明启动命令和访问地址，例如：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```
