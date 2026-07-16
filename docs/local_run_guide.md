# 本地网站启动方式

本文档记录当前版本 `http://127.0.0.1:8000/` 的本地启动方式，避免因为目录、分支或 Python 环境不一致导致页面和代码对不上。

## 一、正确项目目录

当前网站运行依赖的项目根目录是：

```text
E:\smart-campus-agent项目\smart-campus-agent-main
```

启动前必须先进入这个目录：

```powershell
cd E:\smart-campus-agent项目\smart-campus-agent-main
```

不要从下面这个副本目录启动：

```text
E:\smart-campus-agent项目0716\smart-campus-agent-main
```

`E:\smart-campus-agent项目0716\事务助手提交包` 是小玉校园安全助手的来源提交包，可作为后续合并参考，但不是当前 `http://127.0.0.1:8000/` 的运行目录。

## 二、Python 环境

当前约定使用 Anaconda 虚拟环境 `my_env`：

```text
E:\Anaconda_envs\envs\my_env\python.exe
```

不要使用 base 环境启动。

## 三、启动命令

在 PowerShell 中执行：

```powershell
cd E:\smart-campus-agent项目\smart-campus-agent-main
& "E:\Anaconda_envs\envs\my_env\python.exe" -m uvicorn backend.main:app --reload --port 8000
```

看到类似下面的信息，表示后端启动成功：

```text
Uvicorn running on http://127.0.0.1:8000
```

然后浏览器打开：

```text
http://127.0.0.1:8000/
```

## 四、快速验证

### 1. 验证首页

打开：

```text
http://127.0.0.1:8000/
```

正常情况下应进入南京审计大学学生事务助手页面。

### 2. 验证安全接口

打开：

```text
http://127.0.0.1:8000/api/safety/dashboard
```

如果返回 JSON 数据，说明校园安全助手后端接口已经加载。

如果返回：

```text
404 Not Found
```

通常说明当前 8000 端口运行的是旧后端，或不是从 `E:\smart-campus-agent项目\smart-campus-agent-main` 目录启动。

### 3. 验证模型 API 配置接口

打开：

```text
http://127.0.0.1:8000/api/model/config
```

该接口用于查看模型 API 是否已配置。

## 五、常见问题

### 1. 页面是新的，但安全记录生成失败并显示 Not Found

原因通常是：前端文件已经是新版，但后端进程还是旧版。

处理方式：

1. 停止当前运行的 uvicorn。
2. 回到正确目录：

```powershell
cd E:\smart-campus-agent项目\smart-campus-agent-main
```

3. 用 `my_env` 重新启动：

```powershell
& "E:\Anaconda_envs\envs\my_env\python.exe" -m uvicorn backend.main:app --reload --port 8000
```

### 2. 端口 8000 被占用

可以先查看占用：

```powershell
netstat -ano | Select-String ":8000"
```

如果确认是旧的本地开发进程，可以关闭旧终端，或结束对应进程后重新启动。

### 3. 修改代码后网页没变化

优先尝试：

- 刷新浏览器；
- 硬刷新浏览器；
- 确认当前浏览器打开的是 `http://127.0.0.1:8000/`；
- 确认启动目录是 `E:\smart-campus-agent项目\smart-campus-agent-main`。

## 六、当前运行依赖位置

从正确目录启动时，后端实际读取：

```text
ROOT_DIR      = E:\smart-campus-agent项目\smart-campus-agent-main
FRONTEND_DIR  = E:\smart-campus-agent项目\smart-campus-agent-main\frontend
KNOWLEDGE_DIR = E:\smart-campus-agent项目\smart-campus-agent-main\docs\knowledge_base
DATA_DIR      = E:\smart-campus-agent项目\smart-campus-agent-main\data
DB_PATH       = E:\smart-campus-agent项目\smart-campus-agent-main\data\app.db
```

也就是说，支持当前本地网站运行的代码、页面、知识库和数据库都位于：

```text
E:\smart-campus-agent项目\smart-campus-agent-main
```
