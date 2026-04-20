# Task2 情感标注系统

## 1. 项目概述

本项目实现了一个面向标注员的音频/视频情感标注系统。系统不依赖情感识别模型，而是围绕人工标注流程提供媒体导入、任务分配、草稿自动保存、正式提交、复核与结构化 JSON 导出能力。

本题重点不是大规模模型训练，而是工程化系统设计。因此实现目标集中在以下方面：

- 清晰且可维护的前后端分层结构
- 配置化运行方式，而不是将路径、标签集合、超时策略写死在业务代码中
- 可测试、可扩展、可恢复的模块化设计
- 能够支撑长时间运行所需的持久化状态、日志、重试和任务租约机制

## 2. 当前实现范围

当前版本已经覆盖一条完整的人工作业链路：

1. 扫描 `task2/media/` 中的音频或视频文件
2. 导入媒体元数据并建立任务
3. 对媒体执行预处理探测，写入格式、时长等信息
4. 将任务分配给标注员并加锁
5. 支持标注过程中的 autosave 与 heartbeat
6. 支持 submit、review 与 export
7. 以 `json` 或 `jsonl` 输出结构化结果

当前分支会将“预处理”从元数据探测升级为标准化流水线：为标注工作台生成可播放的 normalized asset，并按配置生成 waveform 与 poster 等辅助资产。

## 3. 仓库结构

```text
task2/
├── README.md
├── Agent.md
├── architecture.md
├── api_contract.md
├── config.md
├── runbook.md
├── testing.md
├── media/                     # 输入媒体样例
├── exports/                   # 导出结果
├── data/                      # SQLite 数据库
├── logs/                      # 运行日志
├── workspace/                 # 运行时工作目录
├── frontend/                  # React + Vite + TypeScript
└── backend/                   # FastAPI + Python + SQLite
```

文档职责如下：

- `Agent.md`：索引入口和治理规则
- `architecture.md`：唯一架构事实来源
- `api_contract.md`：HTTP 接口与导出协议
- `config.md`：配置项说明
- `runbook.md`：运行与恢复约束
- `testing.md`：测试与结构校验策略

## 4. 技术栈

### 前端

- React 19
- Vite
- TypeScript
- React Router
- Vitest / Testing Library
- dependency-cruiser

### 后端

- FastAPI
- Python 3.11+
- SQLite
- Pydantic v2
- pytest
- import-linter

## 5. 运行环境与依赖安装

### 环境要求

- Node.js 20+
- npm 10+
- Python 3.11+
- `ffprobe` 可用并在 PATH 中，用于媒体探测

### 后端安装与启动

```bash
cd task2/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn task2_backend.main:app --host 127.0.0.1 --port 8000 --reload
```

后端健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

### 前端安装与启动

```bash
cd task2/frontend
npm install
npm run dev
```

前端默认通过 `/api` 访问后端，开发时请确保后端已在 `127.0.0.1:8000` 可用。

## 6. 推荐操作流程

1. 启动后端服务
2. 启动前端页面
3. 在 Media 页面执行 import
4. 执行 preprocess，使媒体进入 `READY`
5. 在 Annotation 页面点击 `Get Next Task`
6. 标注过程中由 autosave 保存草稿，由 heartbeat 续租任务锁
7. 点击 `Submit` 提交正式标注
8. 在 Review 页面进行复核
9. 执行 export，产出 `json` 或 `jsonl`

## 7. 输出格式说明

导出文件默认写入 `task2/exports/`，当前支持：

- `json`：单个批次一个 JSON 数组文件
- `jsonl`：单行一条记录，便于下游流式消费

单条导出记录的核心结构如下：

```json
{
  "media_id": "1226-141268-0001",
  "source_path": "task2/media/1226-141268-0001.mp3",
  "media_type": "audio",
  "detected_format": "mp3",
  "duration_ms": 14670,
  "annotation": {
    "primary_emotion": "sad",
    "secondary_emotions": [],
    "intensity": 3,
    "confidence": 4,
    "valence": -0.6,
    "arousal": 2,
    "notes": "语气平稳但整体偏低落"
  },
  "annotator": {
    "annotator_id": "annotator_01",
    "submitted_at": "2026-04-20T19:30:00+08:00"
  },
  "review": {
    "status": "approved",
    "reviewer_id": "reviewer_01",
    "reviewed_at": "2026-04-20T19:35:00+08:00"
  }
}
```

完整字段定义见 `api_contract.md`。

## 8. 核心技术思路与系统设计

### 8.1 分层架构

本项目采用严格单向依赖的四层结构，依赖方向固定为：

`L3 -> L2 -> L1 -> L0`

前端：

- `L0 components/ui`：纯 UI 原子组件
- `L1 foundation`：共享 hooks、适配器、类型、基础组件
- `L2 domains/{media, annotation, review_export}`：业务域
- `L3 pages`：路由级薄组合层

后端：

- `L0 common`：纯类型、异常、时间工具
- `L1 foundation`：配置、数据库、日志、媒体探测、重试
- `L2 domains/{media, annotation, review_export}`：业务域
- `L3 api`：HTTP 接口层

约束规则：

- 禁止反向依赖
- 禁止同级跨域导入
- 页面层和 API 层不承载业务逻辑
- 重试只在 `foundation` 层实现
- 配置只在 `foundation` 层读取并注入下游

### 8.2 任务生命周期

系统使用持久化状态机管理任务：

`IMPORTED -> PREPROCESSED -> READY -> IN_PROGRESS -> SUBMITTED -> REVIEWED -> EXPORTED`

所有状态都落库，不依赖进程内存态。这样可以支持：

- 服务重启后恢复任务状态
- 重复导入时保持幂等
- 提交、复核、导出链路可追踪

### 8.3 租约机制

为避免多个标注员同时拿到同一任务，`Get Next Task` 会获取任务锁。系统同时实现了两种配套机制：

- `heartbeat`：用户活跃时续租，不写入新草稿
- `autosave`：用户编辑且内容有变化时保存草稿，并同步续租
- `release`：用户跳过、离开页面或放弃任务时主动释放锁

这一设计既能避免任务冲突，也能减少长时间占锁带来的吞吐损失。

### 8.4 配置化设计

所有运行时可变项都经由配置注入，而不是硬编码在业务层。当前配置覆盖：

- 输入目录、输出目录、数据库路径、日志目录
- maintenance loop 开关与轮询间隔
- 自动保存间隔、心跳间隔、任务锁超时
- 媒体支持格式、目标音频格式、目标视频格式、目标采样率、目标声道数
- 重试次数、退避参数
- 导出格式

详见 `config.md` 与 `backend/config.yaml`。

## 9. 性能与效率优化方案

本项目规模不大，但设计上已经预留了工程优化空间：

### 已实现

- 重复导入按 `media_id` 幂等处理，避免重复建任务
- 任务状态与注释版本落库，减少内存态丢失风险
- 通过任务锁避免重复领取同一任务
- 使用分页接口拉取媒体和任务列表
- 导出支持 `jsonl`，便于流式消费
- 重试逻辑集中实现，避免分散式重复代码

### 已在架构中预留的扩展方向

- 将预处理进一步扩展为独立后台作业队列
- 为媒体标准化引入更高并发 worker
- 增加导出批次去重与版本控制
- 为状态统计和失败记录增加独立监控面板
- 在更大规模部署时，将 SQLite 适配切换为更适合并发写入的数据库

## 10. 运行监控与状态记录

系统当前通过以下方式保证可观测性和可恢复性：

- 结构化日志写入 `task2/logs/`
- 任务、标注、复核、导出状态全部持久化到 SQLite
- 后台 maintenance loop 定时回收过期锁并重放到期失败任务
- retryable failure 通过持久化 failure record 管理，而不是只在内存里 sleep
- 错误映射为稳定的异常类别和 HTTP 错误码
- 针对媒体探测、导出写入、数据库短暂锁冲突等场景提供集中式重试
- 通过任务锁超时和显式释放机制控制任务占用

健康检查端点：

```text
GET /api/health
```

主要运行状态可通过以下资源追踪：

- `GET /api/media`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `GET /api/exports/{batch_id}`
- `GET /api/ops/status`

## 11. 测试与结构校验

### 后端

```bash
cd task2/backend
PYTHONPATH=src pytest tests
PYTHONPATH=src lint-imports --config importlinter.ini
```

### 前端

```bash
cd task2/frontend
npm run build
npx depcruise --config depcruise.config.cjs src
```

当前后端已补齐关键链路测试，覆盖：

- autosave -> submit -> get task detail -> review
- heartbeat -> release -> reacquire
- 重复导入与配置加载

## 12. 已知限制与后续工作

当前版本已经具备完整的人工作业链路、长期运行所需的租约与恢复机制，以及面向标注流程优化过的信息层级界面。但仍有一些增强项适合继续推进：

1. 增加标注员与复核员的身份认证、权限隔离和操作审计，避免系统默认单工作区、弱身份场景。
2. 补齐更完整的端到端自动化测试与长时间 soak test，持续验证导入、预处理、续租、释放、复核、导出链路在重复运行下的稳定性。
3. 为后台任务补充更细粒度的运行统计、失败告警和运维视图，降低 24 小时无人值守运行时的问题定位成本。
4. 在更高并发场景下，将 SQLite 适配替换为更适合多用户协作的数据库后端，同时保持 domain 接口不变。

这些工作不影响当前题目要求的完成度，但会直接决定系统从“可运行原型”进一步走向“可持续运营工具”的上限。
