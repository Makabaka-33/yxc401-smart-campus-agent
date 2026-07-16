# Commit 详情记录

本文件用于记录每次提交背后的具体改动、修改原因、涉及文件和验证方式。  
普通 Git commit message 只适合写一句话，这里用于保留更完整的项目过程，方便答辩、复盘、队友协作和后续合并。

## 当前分支

- 分支：`agent/student-affairs-dashboard`
- 目标：在不直接覆盖 `main` 原版的前提下，持续迭代南京审计大学学生事务助手。
- 说明：后续每次提交前后，都应在本文件中补充对应记录。

## 提交记录

### 0a8f4f1｜2026-07-13｜初始化智启校园智能体项目

- 建立智启校园智能体项目的初始代码结构。
- 搭建前端、后端、文档和数据目录的基本雏形。
- 为后续学习助手、教学助手、事务助手等模块预留基础入口。

### 3dad831｜2026-07-13｜Initial commit

- 提交项目初版基础文件。
- 保留原始 Web Demo 的基本运行能力。
- 作为后续分支开发的早期基线。

### 5805c69｜2026-07-13｜Add project URL to README

- 在 README 中补充项目访问或仓库相关说明。
- 方便从 GitHub 页面快速了解项目入口。

### fa114e9｜2026-07-13｜合并远程README，添加原始项目链接

- 合并远程 README 内容。
- 增加原始项目链接，保留来源说明。
- 该提交可作为事务助手改造前的重要参考节点。

### ab31a5b｜2026-07-14｜实现学生事务助手工作台首版

- 新增学生事务助手第一版工作台。
- 开始围绕南京审计大学学生事务场景组织页面内容。
- 引入本科生和研究生两类学生身份的基础设定。
- 搭建事务卡片、近期重点、校园服务、校园消息等核心模块雏形。

主要涉及：

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `frontend/affairs-data.js`

### f02d2eb｜2026-07-14｜按参考图重构事务助手默认布局

- 根据用户提供的“图1：事务助手首页界面示意图”重构页面布局。
- 将事务助手设为当前分支默认入口，避免用户进入旧版学习助手首页。
- 增加左侧导航、顶部身份区域、搜索输入框、快捷问题和卡片化模块。
- 统一页面视觉风格，使页面更接近参考图。

主要涉及：

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

### f41b779｜2026-07-14｜按身份与时间聚合校园官方资讯

- 将“校园消息速览”从普通官网链接改为按身份和时间推送具体资讯。
- 区分本科生、研究生，展示不同来源和不同适用范围的通知。
- 避免只给南京审计大学官网、图书馆官网这类“大网站链接”。
- 引入官方来源、发布时间、适用身份、匹配原因等字段。

主要涉及：

- `backend/main.py`
- `frontend/app.js`
- `frontend/affairs-data.js`

### ad4b362｜2026-07-14｜更新研究生演示账号姓名

- 将研究生演示账号姓名调整为“江同学”。
- 保持本科生和研究生两套模拟档案：
  - 本科生示例账号
  - 研究生示例账号
- 页面结构不变，只根据身份切换推送内容。

主要涉及：

- `frontend/affairs-data.js`
- `frontend/app.js`

### 5afedcb｜2026-07-14｜整理学生事务助手第一版修改记录

- 新增第一版事务助手修改记录文档。
- 记录分支、PR、功能范围、页面结构、身份差异、数据来源和测试情况。
- README 中增加修改记录入口。

主要涉及：

- `README.md`
- `docs/change_log_student_affairs_v1.md`
- `docs/student_affairs_mvp.md`

### 34d5cc8｜2026-07-15｜校正事务提醒时间线并接入CET官网

- 修正“近期重点”里容易引起误解的时间标注。
- 区分：
  - 官方已发布通知
  - 往年规律预估
  - 待官方通知
  - 演示模拟
- 接入全国大学英语四、六级考试官网来源，避免仅依赖学校站内通知。
- 强化年份和链接时间线校验，避免未来日期或错年链接误导用户。

主要涉及：

- `backend/main.py`
- `frontend/affairs-data.js`
- `frontend/app.js`
- `tests/test_backend.py`

### bf41ab6｜2026-07-15｜增加官方通知正文抓取与结构化解析

- 在标题级资讯抓取之外，增加正文级抓取和结构化解析。
- 从官方通知正文中提取：
  - 截止时间
  - 适用对象
  - 联系电话
  - 附件链接
  - 办理入口
  - 正文章节
- 提升“校园消息速览”的可信度和可解释性。

主要涉及：

- `backend/main.py`
- `tests/test_backend.py`

### c50e5c8｜2026-07-16｜新增模型API配置检测接口

- 新增模型 API 配置检测能力。
- 后端提供：
  - `GET /api/model/config`
  - `POST /api/model/probe`
- 前端状态栏可显示：
  - 真实 API 已配置
  - 等待配置
  - 配置检测失败
- 测试覆盖环境变量缺失、Base URL 标准化和密钥尾号显示。

主要涉及：

- `.env.example`
- `backend/main.py`
- `frontend/app.js`
- `tests/test_backend.py`

## 待提交记录

### 待提交｜2026-07-16｜整合小玉校园安全助手并新增悬浮守护小人

本轮修改来源于队友小玉的成果目录：

- `E:\smart-campus-agent项目0716\事务助手提交包`

本轮目标不是重做安全模块，而是在当前事务助手中充分复用小玉已经完成的校园安全助手页面、样式、脚本和接口设计。

#### 主要改动

- 从小玉提交包复用完整安全中心页面：
  - `frontend/safety.html`
  - `frontend/safety.css`
  - `frontend/safety.js`
- 在事务助手页面新增“悬浮守护小人”。
- 悬浮守护小人包含四个入口：
  - SOS 快速求助
  - 隐患上报
  - 心理安抚
  - 进入安全中心
- 悬浮守护小人支持：
  - 拖动位置
  - 打开安全面板
  - 关闭安全面板
  - 只在事务助手页面显示
- “进入安全中心”跳转到小玉的完整安全中心页面。
- 修正安全中心返回链接，将原 `/static/affairs.html` 改为返回当前事务助手首页 `/`。
- 新增前端 `postJson` 辅助方法，使 SOS、隐患上报和心理安抚可以真正请求后端接口。
- 提高前端资源缓存版本号到 `20260716-safety-3`，避免浏览器继续加载旧 JS/CSS。

#### 后端能力

新增或接入校园安全相关能力：

- `GET /api/safety/dashboard`
- `POST /api/safety/sos`
- `POST /api/safety/sos/{incident_id}/cancel`
- `POST /api/safety/reports`
- `POST /api/safety/trips`
- `POST /api/safety/trips/{trip_id}/arrive`
- `POST /api/safety/lost-found`
- `mode: "safety"` 安全问答模式

新增安全演示数据表：

- `safety_sos`
- `safety_reports`
- `safety_trips`
- `safety_lost_found`

#### 涉及文件

- `backend/main.py`
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `frontend/safety.html`
- `frontend/safety.css`
- `frontend/safety.js`
- `tests/test_backend.py`
- `docs/commit_details.md`

#### 验证结果

- `node --check frontend/app.js`：通过
- `node --check frontend/safety.js`：通过
- `E:\Anaconda_envs\envs\my_env\python.exe -m pytest tests/test_backend.py`：`23 passed`

#### 注意事项

- 本轮安全模块是演示原型，不会自动报警，也不会替代真实 110、119、120 或学校正式处置流程。
- 小玉后续如果继续提供新版安全模块，应先对比再合并，避免直接覆盖当前事务助手中已经接好的悬浮入口、接口调用和缓存版本号。

### 待提交｜2026-07-16｜取消前端正文解析展示，改为速览概括

#### 问题

校园消息速览中的“查看正文解析”功能对用户不友好：用户真正需要的是直接读懂通知重点，而不是看到后端如何拆正文。此前该折叠区还曾把学校网页模板里的公共导航链接误识别为正文办理入口，例如：

- 课表查询
- 调停课查询
- 教学信息系统
- 创新创业教育平台
- 毕业实习智能管理平台
- 毕业论文（设计）管理系统

同时，前端把正文中抓到的多个日期统一显示为“正文时间”，容易让用户误以为这些日期都是办理时间或截止时间。

#### 修正

- 移除前端“查看正文解析”折叠区。
- 正文抓取只作为后端能力，用来支撑校园消息速览里的摘要、适用身份、截止状态和来源可信度。
- 后端新增模板噪声链接过滤，明确排除教务处等页面中的公共导航链接。
- 后端收紧办理入口识别，只保留附件、下载、报名入口、申请入口、办理入口等强相关链接。
- 前端元信息从“正文解析 N 篇”改为“已概括 N 篇”。
- 新增回归测试，防止“课表查询 / 教学信息系统”等模板链接再次混入正文解析。

#### 涉及文件

- `backend/main.py`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/change_log_student_affairs_v1.md`
- `tests/test_backend.py`
- `docs/commit_details.md`

#### 验证结果

- `node --check frontend/app.js`：通过
- `node --check frontend/safety.js`：通过
- `E:\Anaconda_envs\envs\my_env\python.exe -m pytest tests/test_backend.py`：`24 passed`

### 待提交｜2026-07-16｜记录本地网站启动方式

#### 背景

项目本地存在多个相似目录，例如：

- `E:\smart-campus-agent项目\smart-campus-agent-main`
- `E:\smart-campus-agent项目0716\smart-campus-agent-main`
- `E:\smart-campus-agent项目0716\事务助手提交包`

为了避免运行到旧副本、旧后端或错误 Python 环境，需要把当前网站的标准启动方式写入项目文档。

#### 记录内容

- 当前 `http://127.0.0.1:8000/` 的正确项目目录：
  - `E:\smart-campus-agent项目\smart-campus-agent-main`
- 指定 Python 环境：
  - `E:\Anaconda_envs\envs\my_env\python.exe`
- 标准启动命令：
  - `& "E:\Anaconda_envs\envs\my_env\python.exe" -m uvicorn backend.main:app --reload --port 8000`
- 验证地址：
  - `http://127.0.0.1:8000/`
  - `http://127.0.0.1:8000/api/safety/dashboard`
  - `http://127.0.0.1:8000/api/model/config`
- 常见问题：
  - 安全接口 Not Found
  - 8000 端口占用
  - 浏览器仍加载旧页面

#### 涉及文件

- `docs/local_run_guide.md`
- `README.md`
- `docs/commit_details.md`

### 待提交｜2026-07-16｜修复安全记录短描述提交失败

#### 问题

悬浮守护小人中选择“隐患上报”，填写：

- 地点：沁3
- 情况：路灯不亮

提交时曾返回失败。原因有两个：

- 后端要求隐患描述至少 5 个字符，而“路灯不亮”只有 4 个中文字符。
- 前端没有正确展开 FastAPI 的校验错误数组，导致页面显示 `[object Object]`。

此外，安全工单号原本只精确到秒，连续提交时可能出现数据库主键冲突。

#### 修正

- 将隐患上报描述最短长度从 5 调整为 2。
- 前端新增 API 错误格式化逻辑，避免显示 `[object Object]`。
- SOS 记录和隐患工单号增加随机短后缀，避免同一秒内连续提交撞号。
- 新增测试覆盖“路灯不亮”这类短隐患描述。

#### 涉及文件

- `backend/main.py`
- `frontend/app.js`
- `tests/test_backend.py`
- `docs/commit_details.md`

#### 验证结果

- `node --check frontend/app.js`：通过
- `node --check frontend/safety.js`：通过
- `E:\Anaconda_envs\envs\my_env\python.exe -m pytest tests/test_backend.py`：`25 passed`
