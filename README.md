# 智启校园智能体

面向”AI赋能教·学·管”竞赛的最小可运行项目。

原始项目：[yxc401/smart-campus-agent](https://github.com/yxc401/smart-campus-agent)

## 当前开发版本

学生事务助手第一版已在 `agent/student-affairs-dashboard` 分支开发，支持本科生与研究生身份切换、四大事务模块、事务 Agent 和官方资讯动态聚合。

- [完整修改记录](docs/change_log_student_affairs_v1.md)
- [每次 Commit 详情记录](docs/commit_details.md)
- [MVP 范围与数据说明](docs/student_affairs_mvp.md)
- [草稿 Pull Request #1](https://github.com/Makabaka-33/yxc401-smart-campus-agent/pull/1)

## 项目简介

这个版本参考 `deepsearch-agents` 的思路，但先做小白能跑通的闭环：

- 前端页面负责选择场景、输入问题、展示回答
- FastAPI 后端负责接收问题、读取资料、调用大模型 API
- `docs/knowledge_base` 放校园资料和课程资料
- `.env` 放主办方提供的 API Key、Base URL、模型名称

## 运行步骤

```powershell
cd smart-campus-agent
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## 接入主办方 API

拿到千问、GLM 或其他模型接口后，编辑 `.env`：

```env
MODEL_API_KEY=你的真实key
MODEL_BASE_URL=主办方给的OpenAI兼容接口地址
MODEL_NAME=主办方给的模型名
MOCK_MODE=0
```

如果主办方接口不是 OpenAI 兼容格式，只需要改 `backend/main.py` 里的 `call_model_api` 函数。

## 当前版本目标

先完成第一个闭环：

用户问题 -> FastAPI -> 模拟/真实模型回答 -> 前端展示

后续再逐步加：

- 文件上传
- 更好的知识库检索
- 生成学习计划 PDF/Word
- API 调用记录
- 演示视频脚本
