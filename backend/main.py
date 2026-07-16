from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import math
import mimetypes
import os
import re
import sqlite3
import time
import uuid
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, AsyncIterator, Literal
from urllib.parse import urljoin, urlparse

import httpx
import jieba
from openpyxl import load_workbook
from docx import Document as DocxDocument
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pypdf import PdfReader


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
KNOWLEDGE_DIR = ROOT_DIR / "docs" / "knowledge_base"
DATA_DIR = ROOT_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORT_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "app.db"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
CHUNK_SIZE = 900
CHUNK_OVERLAP = 140

load_dotenv(ROOT_DIR / ".env")


AssistantMode = Literal["learning", "teaching", "affairs", "audit", "safety"]


class ChatRequest(BaseModel):
    mode: AssistantMode = Field(default="learning")
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    deep_research: bool = False
    web_search: bool = False


class Reference(BaseModel):
    document_id: str
    chunk_id: str
    source_name: str
    chunk_index: int
    char_start: int
    char_end: int
    snippet: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    mode: AssistantMode
    answer: str
    references: list[Reference] = []
    mock: bool


class ModelProbeRequest(BaseModel):
    message: str = Field(default="请用一句话回复：API 连接正常。", min_length=1, max_length=200)


class ReportRequest(BaseModel):
    session_id: str


class MockLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=120)


class SafetySosRequest(BaseModel):
    event_type: str = Field(default="其他紧急情况", min_length=1, max_length=40)
    location: str = Field(default="位置待确认", min_length=1, max_length=160)
    note: str = Field(default="", max_length=500)
    contact: str = Field(default="", max_length=40)


class SafetyReportRequest(BaseModel):
    category: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=2, max_length=1200)
    location: str = Field(min_length=1, max_length=160)
    urgency: str = Field(default="一般", max_length=20)
    privacy: str = Field(default="实名可追踪", max_length=30)


class SafetyTripRequest(BaseModel):
    destination: str = Field(min_length=1, max_length=160)
    contact: str = Field(min_length=1, max_length=80)
    duration_minutes: int = Field(default=30, ge=5, le=720)


class SafetyLostFoundRequest(BaseModel):
    item_type: Literal["丢失", "拾获"]
    category: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=2, max_length=500)
    area: str = Field(min_length=1, max_length=100)


class ArtifactRequest(BaseModel):
    mode: AssistantMode = Field(default="audit")
    prompt: str = Field(default="审计学基础", min_length=1, max_length=2000)


class QuizRequest(ArtifactRequest):
    question_count: int = Field(default=6, ge=1, le=20)


class TranslationRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=12000)
    target_language: str = Field(default="中文", min_length=1, max_length=40)


class TranslationSummaryRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=12000)
    target_language: str = Field(default="中英双语", min_length=1, max_length=40)


class ArtifactArchiveRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)


MODE_TITLES: dict[str, str] = {
    "learning": "学习助手",
    "teaching": "教学助手",
    "affairs": "事务助手",
    "audit": "审计学习助手",
    "safety": "校园安全助手",
}


AUTH_PORTAL = {
    "provider": "南京审计大学信息门户",
    "portal_url": "https://my.nau.edu.cn/index.html#/",
    "auth_type": "mock",
}


AFFAIRS_NEWS_SOURCES = [
    {
        "name": "中国教育考试网·CET",
        "url": "https://cet.neea.edu.cn/",
        "icon": "CET",
        "audiences": ["undergraduate", "graduate"],
        "allowed_hosts": ["cet.neea.edu.cn"],
        "article_path_markers": ["/html1/report/"],
    },
    {
        "name": "教务处",
        "url": "https://jw.nau.edu.cn/",
        "icon": "📘",
        "audiences": ["undergraduate", "graduate"],
    },
    {
        "name": "研究生院",
        "url": "https://gs.nau.edu.cn/?s=103",
        "icon": "🎓",
        "audiences": ["graduate"],
    },
    {
        "name": "学生工作处",
        "url": "https://xgc.nau.edu.cn/",
        "icon": "🧑‍🎓",
        "audiences": ["undergraduate", "graduate"],
    },
    {
        "name": "图书馆",
        "url": "https://lib.nau.edu.cn/",
        "icon": "📚",
        "audiences": ["undergraduate", "graduate"],
    },
]


AFFAIRS_NEWS_FALLBACK = [
    {
        "id": "neea-cet-20260306",
        "title": "2026年上半年全国大学英语四、六级考试报名工作启动",
        "summary": "中国教育考试网公布上半年笔试、口试和准考证打印安排；各考点具体报名时间仍以所在学校通知为准。",
        "publishedDate": "2026-03-06",
        "deadline": "",
        "sourceName": "中国教育考试网·CET",
        "sourceUrl": "https://cet.neea.edu.cn/html1/report/2603/2-1.htm",
        "icon": "CET",
        "audiences": ["undergraduate", "graduate"],
    },
    {
        "id": "jw-textbook-20260710",
        "title": "关于2026—2027学年第一学期普本学生教材选购工作的通知",
        "summary": "本科生可在学生个人信息系统选购下学期教材，开放时间为7月12日8:00至7月22日8:00。",
        "publishedDate": "2026-07-10",
        "deadline": "2026-07-22",
        "sourceName": "教务处",
        "sourceUrl": "https://jw.nau.edu.cn/2026/0710/c8013a160596/page.htm",
        "icon": "📘",
        "audiences": ["undergraduate"],
    },
    {
        "id": "jw-micro-major-20260710",
        "title": "关于公布2026年获得微专业证书学生名单的通知",
        "summary": "教务处公布2026年微专业证书学生名单，相关同学可查看具体名单与后续安排。",
        "publishedDate": "2026-07-10",
        "deadline": "",
        "sourceName": "教务处",
        "sourceUrl": "https://jw.nau.edu.cn/2026/0710/c8013a160579/page.htm",
        "icon": "📘",
        "audiences": ["undergraduate"],
    },
    {
        "id": "jw-exam-schedule-20260601",
        "title": "关于发布2025-2026学年第二学期期末考试日程安排的通知",
        "summary": "本科生可查询期末考试日程、缓考申请操作流程及考试注意事项。",
        "publishedDate": "2026-06-01",
        "deadline": "",
        "sourceName": "教务处",
        "sourceUrl": "https://jw.nau.edu.cn/2026/0601/c8013a158290/page.htm",
        "icon": "📝",
        "audiences": ["undergraduate"],
    },
    {
        "id": "lib-ai-lecture-20260618",
        "title": "利用AI工具与多模态信息辅助学习与科研",
        "summary": "图书馆面向学生发布的线上信息素养讲座，可查看讲座内容与参与方式。",
        "publishedDate": "2026-06-18",
        "deadline": "2026-06-25",
        "sourceName": "图书馆",
        "sourceUrl": "https://lib.nau.edu.cn/2026/0618/c7014a159260/page.htm",
        "icon": "📚",
        "audiences": ["undergraduate", "graduate"],
    },
    {
        "id": "gs-graduate-recommendation-20260612",
        "title": "关于2026届优秀毕业研究生拟推荐名单的公示",
        "summary": "研究生院发布优秀毕业研究生拟推荐名单，毕业年级可查看公示要求。",
        "publishedDate": "2026-06-12",
        "deadline": "",
        "sourceName": "研究生院",
        "sourceUrl": "https://gs.nau.edu.cn/2026/0612/c4414a158908/page.htm",
        "icon": "🎓",
        "audiences": ["graduate"],
    },
    {
        "id": "gs-scholarship-20260511",
        "title": "关于2026年审计长奖学金（研究生）评审情况的公示",
        "summary": "研究生院发布审计长奖学金评审结果，研究生可查看评审与公示信息。",
        "publishedDate": "2026-05-11",
        "deadline": "",
        "sourceName": "研究生院",
        "sourceUrl": "https://gs.nau.edu.cn/2026/0511/c4414a157308/page.htm",
        "icon": "🎓",
        "audiences": ["graduate"],
    },
    {
        "id": "gs-teaching-result-20260609",
        "title": "关于2026年高等教育（研究生）国家教学成果奖推荐申报的公示",
        "summary": "研究生院发布研究生教育教学成果推荐申报公示，可查看项目与公示信息。",
        "publishedDate": "2026-06-09",
        "deadline": "2026-06-15",
        "sourceName": "研究生院",
        "sourceUrl": "https://gs.nau.edu.cn/2026/0609/c10680a158567/page.htm",
        "icon": "🎓",
        "audiences": ["graduate"],
    },
    {
        "id": "xgc-work-study-20260317",
        "title": "关于发布2026年春学期勤工助学岗位需求的通知",
        "summary": "符合条件的学生可在学工系统提交岗位申请，并按操作指南完成审核流程。",
        "publishedDate": "2026-03-17",
        "deadline": "",
        "sourceName": "学生工作处",
        "sourceUrl": "https://xgc.nau.edu.cn/_t181/2026/0317/c3439a154989/page.htm",
        "icon": "🧑‍🎓",
        "audiences": ["undergraduate", "graduate"],
    },
    {
        "id": "jw-cet-20260318",
        "title": "2026年上半年全国大学英语四、六级考试报名通知",
        "summary": "通知适用于含研究生在内的全体在校生，包含报名对象、时间、入口和资格核对要求。",
        "publishedDate": "2026-03-18",
        "deadline": "2026-03-30",
        "sourceName": "教务处",
        "sourceUrl": "https://jw.nau.edu.cn/2026/0318/c8013a155043/page.htm",
        "icon": "CET",
        "audiences": ["undergraduate", "graduate"],
    },
]


AFFAIRS_NEWS_CACHE: dict[str, tuple[float, list[dict[str, Any]], int]] = {}
AFFAIRS_ARTICLES_PER_SOURCE = 5
AFFAIRS_ARTICLE_MAX_CHARS = 250_000
AFFAIRS_SERVICE_HOSTS = {"cet-bm.neea.edu.cn", "cet.neea.edu.cn", "www.neea.edu.cn"}


SYSTEM_PROMPTS: dict[str, str] = {
    "learning": (
        "你是“智启校园”的学习助手，服务大学生学习全过程。你必须结合知识库资料、对话历史、用户目标和专业背景，"
        "输出可执行的学习路径、复习计划、练习建议和风险提醒。\n"
        "回答结构固定优先采用：1. 需求判断；2. 资料依据；3. 分阶段计划；4. 今日可执行任务；5. 风险提醒；6. 参考资料。\n"
        "当用户问题含糊时，先给出可执行的默认方案，再列出需要补充的信息；不要只反问。"
    ),
    "teaching": (
        "你是“智启校园”的教学助手，服务高校教师备课、试题生成、课堂活动设计和评分 Rubric。"
        "回答必须贴近真实课堂，包含教学目标、导入案例、课堂活动、练习或试题、评分标准和教学反思建议。\n"
        "如果用户要求出题，必须给出题型、难度、参考答案和评分要点；如果用户要求教案，必须给出时间分配。"
    ),
    "affairs": (
        "你是“智启校园”的事务助手，服务校园办事、学业服务和生活服务咨询。"
        "回答必须列出办理对象、办理入口、办理步骤、材料清单、注意事项和官方确认渠道。\n"
        "资料不确定时明确说明“知识库未覆盖最新官方口径”，并建议用户以学校信息门户、教务处或学院通知为准。"
    ),
    "audit": (
        "你是南京审计大学场景下的“审计学习助手”，服务学生学习审计学基础、政府审计、内部审计、社会审计、"
        "审计法规准则、审计流程、审计证据、工作底稿、审计报告和智能审计数据分析。\n"
        "回答必须体现南审审计特色，优先依据知识库资料；涉及事实、法规、案例和结论时要列出来源或说明资料不足。\n"
        "输出应结构化、可执行，适合学生直接用于预习、复习、案例研讨或实训。"
    ),
    "safety": (
        "你是“守望校园安全助手”，提供校园风险预防、紧急求助指引、隐患上报、安全设施查询、预警解读和安全教育。"
        "你不能替代110、119、120或校园保卫处；遇到正在发生的人身危险、火灾或医疗急症时，必须优先建议立即拨打相应公共紧急电话并撤离到安全位置。"
        "回答要短、清楚、可执行，先判断是否紧急，再给出立即行动、校内渠道、信息保护和后续记录。"
        "不得虚构实时警情、值班人员、设施状态或学校电话号码；不确定时明确提示用户以学校官方信息为准。"
    ),
}


SUPPORTED_UPLOAD_SUFFIXES = {
    ".txt",
    ".md",
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
TIMETABLE_SUFFIXES = {".xlsx", ".csv"}
TRANSLATION_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


STOPWORDS = {
    "一个",
    "一些",
    "这个",
    "那个",
    "如何",
    "怎么",
    "什么",
    "帮我",
    "一下",
    "进行",
    "可以",
    "需要",
    "以及",
    "如果",
    "关于",
}


app = FastAPI(title="智启校园智能体 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    init_db()
    index_builtin_knowledge()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/auth/status")
def auth_status() -> dict[str, Any]:
    return {
        "authenticated": False,
        "user": None,
        **AUTH_PORTAL,
        "message": "当前为虚拟登录状态，后续可接入南京审计大学统一身份认证。",
    }


@app.post("/api/auth/mock-login")
def mock_login(request: MockLoginRequest) -> dict[str, Any]:
    display_name = request.username.strip()
    return {
        "authenticated": True,
        "user": {
            "id": f"mock-{hashlib.sha1(display_name.encode('utf-8')).hexdigest()[:8]}",
            "name": display_name,
            "role": "student",
            "school": "南京审计大学",
        },
        **AUTH_PORTAL,
        "message": "已完成虚拟登录。真实版本需要接入学校统一身份认证。",
    }


@app.post("/api/auth/logout")
def mock_logout() -> dict[str, Any]:
    return {
        "authenticated": False,
        "user": None,
        **AUTH_PORTAL,
        "message": "已退出虚拟登录。",
    }


@app.get("/api/status")
def status() -> dict[str, Any]:
    with db() as conn:
        document_count = conn.execute("select count(*) from documents").fetchone()[0]
        chunk_count = conn.execute("select count(*) from chunks").fetchone()[0]
        last_call = conn.execute(
            "select created_at, model_name, success, error, duration_ms, mock "
            "from api_calls order by id desc limit 1"
        ).fetchone()

    return {
        "mock_mode": is_mock_mode(),
        "model_name": os.getenv("MODEL_NAME", "").strip() or "未配置",
        "base_url_configured": bool(os.getenv("MODEL_BASE_URL", "").strip()),
        "api_key_configured": bool(os.getenv("MODEL_API_KEY", "").strip()),
        "document_count": document_count,
        "chunk_count": chunk_count,
        "last_call": dict(last_call) if last_call else None,
    }


@app.get("/api/model/config")
def model_config() -> dict[str, Any]:
    config = get_model_config()
    return {
        "mock_mode": is_mock_mode(),
        "configured": config["configured"],
        "model_name": config["model"] or "未配置",
        "base_url": mask_model_base_url(config["base_url"]),
        "base_url_configured": bool(config["base_url"]),
        "api_key_configured": bool(config["api_key"]),
        "api_key_tail": config["api_key"][-4:] if config["api_key"] else "",
        "chat_completions_url": (
            f"{mask_model_base_url(config['base_url'])}/chat/completions"
            if config["base_url"]
            else ""
        ),
    }


@app.post("/api/model/probe")
async def probe_model_api(request: ModelProbeRequest) -> dict[str, Any]:
    config = get_model_config()
    if not config["configured"]:
        missing = [
            name
            for name, value in (
                ("MODEL_API_KEY", config["api_key"]),
                ("MODEL_BASE_URL", config["base_url"]),
                ("MODEL_NAME", config["model"]),
            )
            if not value
        ]
        return {
            "ok": False,
            "mock_mode": is_mock_mode(),
            "configured": False,
            "model_name": config["model"] or "未配置",
            "error": f"模型 API 未配置完整：{', '.join(missing)}",
        }

    started = time.perf_counter()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是校园事务助手的 API 连通性测试器，只需要简短回答。"},
            {"role": "user", "content": request.message},
        ],
        "temperature": 0,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            return {
                "ok": False,
                "mock_mode": is_mock_mode(),
                "configured": True,
                "model_name": config["model"],
                "duration_ms": elapsed_ms,
                "error": f"HTTP {response.status_code}: {response.text[:300]}",
            }
        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "ok": True,
            "mock_mode": is_mock_mode(),
            "configured": True,
            "model_name": config["model"],
            "duration_ms": elapsed_ms,
            "answer_preview": str(answer).strip()[:160],
        }
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "ok": False,
            "mock_mode": is_mock_mode(),
            "configured": True,
            "model_name": config["model"],
            "duration_ms": elapsed_ms,
            "error": str(exc)[:300],
        }


@app.get("/api/affairs/notices")
async def list_affairs_notices(
    profile: Literal["undergraduate", "graduate"] = "undergraduate",
    grade: str = "",
    limit: int = 6,
    refresh: bool = False,
) -> dict[str, Any]:
    safe_limit = max(1, min(limit, 12))
    cache_key = f"{profile}:{grade.strip()}"
    cached = AFFAIRS_NEWS_CACHE.get(cache_key)
    if cached and not refresh and time.monotonic() - cached[0] < 900:
        ranked, live_count = cached[1], cached[2]
    else:
        live_items = await fetch_affairs_live_news(profile)
        ranked = rank_affairs_news(profile, grade.strip(), live_items)
        live_count = sum(1 for item in ranked if item.get("live"))
        AFFAIRS_NEWS_CACHE[cache_key] = (time.monotonic(), ranked, live_count)

    return {
        "profile": profile,
        "grade": grade.strip(),
        "generatedAt": now_iso(),
        "liveCount": live_count,
        "contentFetchedCount": sum(1 for item in ranked[:safe_limit] if item.get("contentFetched")),
        "fallbackUsed": live_count == 0,
        "items": ranked[:safe_limit],
    }


@app.get("/api/safety/dashboard")
def safety_dashboard() -> dict[str, Any]:
    with db() as conn:
        reports = [dict(row) for row in conn.execute(
            "select * from safety_reports order by created_at desc limit 8"
        ).fetchall()]
        trips = [dict(row) for row in conn.execute(
            "select * from safety_trips order by created_at desc limit 5"
        ).fetchall()]
        lost_found = [dict(row) for row in conn.execute(
            "select * from safety_lost_found order by created_at desc limit 8"
        ).fetchall()]
    return {
        "campus_status": {"level": "正常", "source": "演示数据 · 待接入保卫处", "updated_at": now_iso()},
        "emergency_numbers": [
            {"name": "公安报警", "number": "110"},
            {"name": "火警", "number": "119"},
            {"name": "医疗急救", "number": "120"},
        ],
        "facilities": [
            {"id": "SEC-01", "type": "安保", "name": "校园保卫处", "area": "校园主入口", "status": "开放", "phone": "以学校官方通讯录为准"},
            {"id": "MED-01", "type": "医疗", "name": "校医院", "area": "生活区", "status": "开放时间待核验", "phone": "以学校官方通讯录为准"},
            {"id": "AED-01", "type": "AED", "name": "AED 示例点位", "area": "体育馆一层", "status": "演示点位，使用前须核验", "phone": "120"},
            {"id": "FIRE-01", "type": "消防", "name": "应急集合点", "area": "中心广场", "status": "演示点位，服从现场指挥", "phone": "119"},
        ],
        "notices": [
            {"id": "N-01", "level": "yellow", "title": "防范电信网络诈骗提醒", "department": "安全助手演示", "action": "不转账、不泄露验证码，疑似被骗请立即停止操作并报警。", "valid_until": "长期"},
            {"id": "N-02", "level": "blue", "title": "实验室安全操作提示", "department": "安全助手演示", "action": "进入实验室前确认培训、劳保用品和应急出口。", "valid_until": "长期"},
        ],
        "classes": [
            {"title": "30秒火灾应急卡", "topic": "消防与疏散", "steps": ["立即撤离，不乘电梯", "低姿前进，远离烟气", "到安全地点拨打119"]},
            {"title": "AED与心肺复苏", "topic": "急救", "steps": ["确认环境安全并呼叫120", "请他人取AED", "按设备语音提示操作"]},
            {"title": "防诈骗三步检查", "topic": "网络安全", "steps": ["核验身份", "拒绝屏幕共享", "不提供验证码"]},
        ],
        "reports": reports,
        "trips": trips,
        "lost_found": lost_found,
    }


@app.post("/api/safety/sos")
def create_safety_sos(request: SafetySosRequest) -> dict[str, Any]:
    incident_id = f"SOS-{datetime.now().strftime('%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
    created_at = now_iso()
    with db() as conn:
        conn.execute(
            "insert into safety_sos (id, event_type, location, note, contact, status, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?, ?)",
            (incident_id, request.event_type, request.location, request.note, request.contact, "已发送（演示）", created_at, created_at),
        )
        conn.commit()
    return {
        "id": incident_id,
        "status": "已发送（演示）",
        "created_at": created_at,
        "message": "演示求助记录已保存。本原型未连接真实接警台；如有现实危险，请立即拨打110、119或120。",
    }


@app.post("/api/safety/sos/{incident_id}/cancel")
def cancel_safety_sos(incident_id: str) -> dict[str, str]:
    with db() as conn:
        result = conn.execute(
            "update safety_sos set status = ?, updated_at = ? where id = ?",
            ("已取消（误触）", now_iso(), incident_id),
        )
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="求助记录不存在")
    return {"id": incident_id, "status": "已取消（误触）"}


@app.post("/api/safety/reports")
def create_safety_report(request: SafetyReportRequest) -> dict[str, str]:
    report_id = f"SAF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
    with db() as conn:
        conn.execute(
            "insert into safety_reports (id, category, description, location, urgency, privacy, status, created_at) values (?, ?, ?, ?, ?, ?, ?, ?)",
            (report_id, request.category, request.description, request.location, request.urgency, request.privacy, "待分派", now_iso()),
        )
        conn.commit()
    return {"id": report_id, "status": "待分派", "message": "上报已保存，可使用工单号追踪。"}


@app.post("/api/safety/trips")
def create_safety_trip(request: SafetyTripRequest) -> dict[str, Any]:
    trip_id = f"TRIP-{uuid.uuid4().hex[:8]}"
    created_at = now_iso()
    with db() as conn:
        conn.execute(
            "insert into safety_trips (id, destination, contact, duration_minutes, status, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?)",
            (trip_id, request.destination, request.contact, request.duration_minutes, "守护中", created_at, created_at),
        )
        conn.commit()
    return {"id": trip_id, "status": "守护中", "duration_minutes": request.duration_minutes}


@app.post("/api/safety/trips/{trip_id}/arrive")
def finish_safety_trip(trip_id: str) -> dict[str, str]:
    with db() as conn:
        result = conn.execute(
            "update safety_trips set status = ?, updated_at = ? where id = ?",
            ("已安全到达", now_iso(), trip_id),
        )
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="守护行程不存在")
    return {"id": trip_id, "status": "已安全到达"}


@app.post("/api/safety/lost-found")
def create_safety_lost_found(request: SafetyLostFoundRequest) -> dict[str, str]:
    item_id = f"LF-{uuid.uuid4().hex[:8]}"
    with db() as conn:
        conn.execute(
            "insert into safety_lost_found (id, item_type, category, description, area, status, created_at) values (?, ?, ?, ?, ?, ?, ?)",
            (item_id, request.item_type, request.category, request.description, request.area, "待核验", now_iso()),
        )
        conn.commit()
    return {"id": item_id, "status": "待核验", "message": "信息已发布，公开页面不会显示联系方式或精确宿舍位置。"}


@app.get("/api/sessions")
def list_sessions() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            """
            select s.id, s.mode, s.title, s.created_at, s.updated_at,
                   count(m.id) as message_count,
                   max(case when m.role = 'user' then m.content else '' end) as last_user_message
            from sessions s
            left join messages m on m.session_id = s.id
            group by s.id
            order by s.updated_at desc
            limit 20
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    with db() as conn:
        session = conn.execute("select * from sessions where id = ?", (session_id,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        messages = conn.execute(
            "select role, mode, content, created_at from messages where session_id = ? order by id asc",
            (session_id,),
        ).fetchall()
    return {"session": dict(session), "messages": [dict(row) for row in messages]}


@app.get("/api/documents")
def list_documents() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            """
            select id, source_name, scope, char_count, chunk_count, created_at
            from documents
            order by created_at desc
            """
        ).fetchall()
    return [document_payload(row) for row in rows]


@app.get("/api/documents/{document_id}")
def get_document(document_id: str) -> dict[str, Any]:
    row = get_document_row(document_id)
    payload = document_payload(row)
    path = Path(row["path"])
    payload["content"] = extract_text_from_file(path)[:30000] if path.suffix.lower() not in IMAGE_SUFFIXES else ""
    return payload


@app.get("/api/documents/{document_id}/view")
def view_document(document_id: str) -> FileResponse:
    row = get_document_row(document_id)
    path = Path(row["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="资料文件不存在")
    media_type = mimetypes.guess_type(row["source_name"])[0] or "application/octet-stream"
    return FileResponse(
        path,
        filename=row["source_name"],
        media_type=media_type,
        content_disposition_type="inline",
    )


@app.get("/api/documents/{document_id}/download")
def download_document(document_id: str) -> FileResponse:
    row = get_document_row(document_id)
    path = Path(row["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="资料文件不存在")
    media_type = mimetypes.guess_type(row["source_name"])[0] or "application/octet-stream"
    return FileResponse(path, filename=row["source_name"], media_type=media_type)


@app.get("/api/api-calls")
def list_api_calls() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            """
            select created_at, model_name, mode, input_summary, output_summary,
                   success, error, duration_ms, mock
            from api_calls
            order by id desc
            limit 20
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    scope: str = Form(default="knowledge"),
) -> dict[str, Any]:
    safe_name = Path(file.filename or "upload.txt").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_SUFFIXES:
        raise HTTPException(status_code=400, detail="仅支持 txt、md、pdf、docx、xlsx 文件")

    payload = await file.read()
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="文件超过 10MB 限制")

    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{safe_name}"
    target = UPLOAD_DIR / unique_name
    target.write_bytes(payload)

    text = extract_text_from_file(target)
    document_id, chunk_count = upsert_document(target, source_name=safe_name, scope=scope)
    return {
        "document_id": document_id,
        "source_name": safe_name,
        "char_count": len(text),
        "chunk_count": chunk_count,
        "indexed": bool(text.strip()),
        "view_url": f"/api/documents/{document_id}/view",
        "download_url": f"/api/documents/{document_id}/download",
        "status": "indexed",
    }


@app.post("/api/timetable/import")
async def import_timetable(file: UploadFile = File(...)) -> dict[str, Any]:
    safe_name = Path(file.filename or "课程表.xlsx").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in TIMETABLE_SUFFIXES:
        raise HTTPException(status_code=400, detail="课程表导入仅支持 xlsx、csv 文件")
    payload = await file.read()
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="文件超过 10MB 限制")

    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{safe_name}"
    target = UPLOAD_DIR / unique_name
    target.write_bytes(payload)
    document_id, _ = upsert_document(target, source_name=safe_name, scope="timetable")
    entries = parse_timetable(target)
    if not entries:
        raise HTTPException(status_code=400, detail="未识别到课程记录，请检查表头和内容")
    with db() as conn:
        for entry in entries:
            conn.execute(
                """
                insert into timetable_entries
                (id, source_document_id, course_name, teacher, location, day_of_week,
                 class_time, weeks, created_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    document_id,
                    entry["course_name"],
                    entry["teacher"],
                    entry["location"],
                    entry["day_of_week"],
                    entry["class_time"],
                    entry["weeks"],
                    now_iso(),
                ),
            )
        conn.commit()
    return {"source_name": safe_name, "document_id": document_id, "imported_count": len(entries)}


@app.get("/api/timetable")
def list_timetable() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            """
            select id, source_document_id, course_name, teacher, location,
                   day_of_week, class_time, weeks, created_at
            from timetable_entries
            order by created_at desc, day_of_week, class_time
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/artifacts/mindmap")
async def create_mindmap(request: ArtifactRequest) -> dict[str, Any]:
    references = retrieve_references(request.prompt, request.mode)
    if is_mock_mode():
        content = build_mock_mindmap(request.prompt, references)
    else:
        content = await call_model_once(
            request.mode,
            (
                "请根据知识库资料生成可直接渲染的 Mermaid mindmap，并附上 5 条复习要点。"
                f"主题：{request.prompt}"
            ),
            references,
            [],
        )
    return artifact_payload("mindmap", request.prompt, request.mode, content, references)


@app.post("/api/artifacts/quiz")
async def create_quiz(request: QuizRequest) -> dict[str, Any]:
    references = retrieve_references(request.prompt, request.mode)
    if is_mock_mode():
        content = build_mock_quiz(request.prompt, request.question_count, references)
    else:
        content = await call_model_once(
            request.mode,
            (
                f"请围绕“{request.prompt}”生成 {request.question_count} 道审计学习测验题，"
                "覆盖选择题、判断题、简答题和案例分析题。每题给出答案、解析、难度和知识点标签。"
            ),
            references,
            [],
        )
    return artifact_payload("quiz", request.prompt, request.mode, content, references)


@app.post("/api/artifacts/outline")
async def create_outline(request: ArtifactRequest) -> dict[str, Any]:
    references = retrieve_references(request.prompt, request.mode)
    if is_mock_mode():
        content = build_mock_outline(request.prompt, references)
    else:
        content = await call_model_once(
            request.mode,
            (
                "请根据知识库资料生成层级清晰的文件大纲，包含核心概念、章节关系、"
                f"重点、难点和复习路径。主题：{request.prompt}"
            ),
            references,
            [],
        )
    return artifact_payload("outline", request.prompt, request.mode, content, references)


@app.post("/api/artifacts/audit-workpaper")
async def create_audit_workpaper(request: ArtifactRequest) -> dict[str, Any]:
    references = retrieve_references(request.prompt, "audit")
    if is_mock_mode():
        content = build_mock_workpaper(request.prompt, references)
    else:
        content = await call_model_once(
            "audit",
            (
                "请根据案例生成审计工作底稿框架，包含审计目标、风险点、审计程序、"
                f"证据清单、发现、结论和整改建议。案例或主题：{request.prompt}"
            ),
            references,
            [],
        )
    return artifact_payload("audit-workpaper", request.prompt, "audit", content, references)


@app.get("/api/artifacts")
def list_artifacts() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            """
            select id, artifact_type, title, prompt, mode, archived_document_id, created_at
            from artifacts
            order by created_at desc
            """
        ).fetchall()
    return [artifact_summary(row) for row in rows]


@app.get("/api/artifacts/{artifact_id}")
def get_artifact(artifact_id: str) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("select * from artifacts where id = ?", (artifact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="生成内容不存在")
    payload = dict(row)
    payload["archived"] = bool(row["archived_document_id"])
    return payload


@app.post("/api/artifacts/{artifact_id}/archive")
def archive_artifact(artifact_id: str, request: ArtifactArchiveRequest | None = None) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("select * from artifacts where id = ?", (artifact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="生成内容不存在")
    if row["archived_document_id"]:
        document = get_document_row(row["archived_document_id"])
        return document_payload(document)

    title = (request.title if request else None) or row["title"]
    safe_title = re.sub(r'[\\/:*?"<>|]+', "-", title).strip()[:80] or "生成内容"
    generated_dir = DATA_DIR / "generated"
    generated_dir.mkdir(exist_ok=True)
    path = generated_dir / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{artifact_id[:8]}_{safe_title}.md"
    path.write_text(row["content"], encoding="utf-8")
    document_id, _ = upsert_document(path, source_name=f"{safe_title}.md", scope="generated")
    with db() as conn:
        conn.execute(
            "update artifacts set archived_document_id = ? where id = ?",
            (document_id, artifact_id),
        )
        conn.commit()
    return document_payload(get_document_row(document_id))


@app.post("/api/translate/text")
async def translate_text(request: TranslationRequest) -> dict[str, Any]:
    references = retrieve_references(request.source_text[:1000], "audit", limit=3)
    translated = await translate_learning_text(
        request.source_text,
        request.target_language,
        references,
    )
    return {
        "target_language": request.target_language,
        "translation": translated,
        "mock": is_mock_mode(),
        "references": [ref.model_dump() for ref in references],
    }


@app.post("/api/translate/file")
async def translate_file(
    file: UploadFile = File(...),
    target_language: str = Form(default="中文"),
) -> dict[str, Any]:
    safe_name = Path(file.filename or "translation.txt").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in TRANSLATION_SUFFIXES:
        raise HTTPException(status_code=400, detail="翻译仅支持 txt、md、pdf、docx 文件")

    payload = await file.read()
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="文件超过 10MB 限制")

    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{safe_name}"
    source_path = UPLOAD_DIR / unique_name
    source_path.write_bytes(payload)

    source_text = extract_text_from_file(source_path)
    if not source_text.strip():
        raise HTTPException(status_code=400, detail="文件未解析到有效文本，扫描版 PDF 暂不支持")

    references = retrieve_references(source_text[:1000], "audit", limit=3)
    translated = await translate_learning_text(source_text[:12000], target_language, references)
    export_id = save_translation_docx(safe_name, target_language, translated, references)
    return {
        "export_id": export_id,
        "source_name": safe_name,
        "target_language": target_language,
        "download_url": f"/api/exports/{export_id}/download",
        "translation_preview": translated[:1200],
        "mock": is_mock_mode(),
    }


@app.post("/api/translate/summary")
async def summarize_translation(request: TranslationSummaryRequest) -> dict[str, Any]:
    references = retrieve_references(request.source_text[:1000], "audit", limit=3)
    summary = await summarize_translation_text(
        request.source_text,
        request.target_language,
        references,
    )
    return {
        "target_language": request.target_language,
        "summary": summary,
        "mock": is_mock_mode(),
        "references": [ref.model_dump() for ref in references],
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = ensure_session(request.session_id, request.mode, request.message)
    add_message(session_id, "user", request.mode, request.message)
    references = retrieve_references(request.message, request.mode)
    history = get_recent_history(session_id)
    start = time.perf_counter()
    model_name = model_label()
    mock = is_mock_mode()
    error = ""
    success = True

    try:
        if mock:
            answer = build_mock_answer(request.mode, request.message, references, history)
            if request.deep_research:
                answer = add_mock_research_frame(answer, request.message)
            if request.web_search:
                answer = add_mock_web_search_note(answer)
        else:
            answer = await call_model_once(
                request.mode,
                prepare_model_question(request),
                references,
                history,
            )
    except Exception as exc:
        success = False
        error = str(exc)
        answer = f"抱歉，模型调用失败：{error}"

    add_message(session_id, "assistant", request.mode, answer)
    record_api_call(
        session_id=session_id,
        mode=request.mode,
        model_name=model_name,
        input_text=request.message,
        output_text=answer,
        success=success,
        error=error,
        duration_ms=int((time.perf_counter() - start) * 1000),
        mock=mock,
    )
    return ChatResponse(
        session_id=session_id,
        mode=request.mode,
        answer=answer,
        references=references,
        mock=mock,
    )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        session_id = ensure_session(request.session_id, request.mode, request.message)
        add_message(session_id, "user", request.mode, request.message)
        references = retrieve_references(request.message, request.mode)
        history = get_recent_history(session_id)
        mock = is_mock_mode()
        model_name = model_label()
        output_parts: list[str] = []
        start = time.perf_counter()
        success = True
        error = ""

        yield sse(
            "meta",
            {
                "session_id": session_id,
                "mode": request.mode,
                "mock": mock,
                "model_name": model_name,
            },
        )

        try:
            if mock:
                answer = build_mock_answer(request.mode, request.message, references, history)
                if request.deep_research:
                    answer = add_mock_research_frame(answer, request.message)
                if request.web_search:
                    answer = add_mock_web_search_note(answer)
                async for token in slice_for_stream(answer):
                    output_parts.append(token)
                    yield sse("token", {"text": token})
            else:
                model_question = prepare_model_question(request)
                async for token in call_model_stream(request.mode, model_question, references, history):
                    output_parts.append(token)
                    yield sse("token", {"text": token})
        except Exception as exc:
            success = False
            error = str(exc)
            yield sse("error", {"message": error})

        answer_text = "".join(output_parts).strip()
        if answer_text:
            add_message(session_id, "assistant", request.mode, answer_text)

        record_api_call(
            session_id=session_id,
            mode=request.mode,
            model_name=model_name,
            input_text=request.message,
            output_text=answer_text,
            success=success,
            error=error,
            duration_ms=int((time.perf_counter() - start) * 1000),
            mock=mock,
        )
        yield sse("references", {"references": [ref.model_dump() for ref in references]})
        yield sse("done", {"session_id": session_id, "success": success})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/reports")
def create_report(request: ReportRequest) -> dict[str, str]:
    with db() as conn:
        session = conn.execute("select * from sessions where id = ?", (request.session_id,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        messages = conn.execute(
            "select role, mode, content, created_at from messages where session_id = ? order by id asc",
            (request.session_id,),
        ).fetchall()

    report_id = uuid.uuid4().hex
    report_path = REPORT_DIR / f"{report_id}.md"
    lines = [
        f"# 智启校园对话报告",
        "",
        f"- 会话 ID：{request.session_id}",
        f"- 模式：{MODE_TITLES.get(session['mode'], session['mode'])}",
        f"- 生成时间：{now_iso()}",
        "",
        "## 对话记录",
        "",
    ]
    for msg in messages:
        speaker = "用户" if msg["role"] == "user" else "智启校园"
        lines.extend([f"### {speaker}（{msg['created_at']}）", "", msg["content"], ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")

    with db() as conn:
        conn.execute(
            "insert into reports (id, session_id, file_path, created_at) values (?, ?, ?, ?)",
            (report_id, request.session_id, str(report_path), now_iso()),
        )
        conn.commit()

    return {"report_id": report_id, "download_url": f"/api/reports/{report_id}/download"}


@app.get("/api/reports/{report_id}/download")
def download_report(report_id: str) -> FileResponse:
    with db() as conn:
        row = conn.execute("select file_path from reports where id = ?", (report_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="报告不存在")
    path = Path(row["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")
    return FileResponse(path, filename=f"智启校园对话报告-{report_id[:8]}.md", media_type="text/markdown")


@app.get("/api/exports/{export_id}/download")
def download_export(export_id: str) -> FileResponse:
    with db() as conn:
        row = conn.execute("select file_path, file_name, media_type from exports where id = ?", (export_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="导出文件不存在")
    path = Path(row["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="导出文件已失效")
    return FileResponse(path, filename=row["file_name"], media_type=row["media_type"])


def db() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            create table if not exists sessions (
                id text primary key,
                mode text not null,
                title text not null,
                created_at text not null,
                updated_at text not null
            );

            create table if not exists messages (
                id integer primary key autoincrement,
                session_id text not null,
                role text not null,
                mode text not null,
                content text not null,
                created_at text not null
            );

            create table if not exists documents (
                id text primary key,
                source_name text not null,
                path text not null unique,
                scope text not null,
                content_hash text not null,
                char_count integer not null,
                chunk_count integer not null,
                created_at text not null
            );

            create table if not exists chunks (
                id text primary key,
                document_id text not null,
                source_name text not null,
                chunk_index integer not null,
                content text not null,
                token_json text not null,
                char_start integer not null,
                char_end integer not null
            );

            create table if not exists api_calls (
                id integer primary key autoincrement,
                session_id text not null,
                created_at text not null,
                model_name text not null,
                mode text not null,
                input_summary text not null,
                output_summary text not null,
                success integer not null,
                error text,
                duration_ms integer not null,
                mock integer not null
            );

            create table if not exists reports (
                id text primary key,
                session_id text not null,
                file_path text not null,
                created_at text not null
            );

            create table if not exists exports (
                id text primary key,
                file_path text not null,
                file_name text not null,
                media_type text not null,
                created_at text not null
            );

            create table if not exists artifacts (
                id text primary key,
                artifact_type text not null,
                title text not null,
                prompt text not null,
                mode text not null,
                content text not null,
                archived_document_id text,
                created_at text not null
            );

            create table if not exists timetable_entries (
                id text primary key,
                source_document_id text not null,
                course_name text not null,
                teacher text not null,
                location text not null,
                day_of_week text not null,
                class_time text not null,
                weeks text not null,
                created_at text not null
            );

            create table if not exists safety_sos (
                id text primary key,
                event_type text not null,
                location text not null,
                note text not null,
                contact text not null,
                status text not null,
                created_at text not null,
                updated_at text not null
            );

            create table if not exists safety_reports (
                id text primary key,
                category text not null,
                description text not null,
                location text not null,
                urgency text not null,
                privacy text not null,
                status text not null,
                created_at text not null
            );

            create table if not exists safety_trips (
                id text primary key,
                destination text not null,
                contact text not null,
                duration_minutes integer not null,
                status text not null,
                created_at text not null,
                updated_at text not null
            );

            create table if not exists safety_lost_found (
                id text primary key,
                item_type text not null,
                category text not null,
                description text not null,
                area text not null,
                status text not null,
                created_at text not null
            );
            """
        )
        conn.commit()


def index_builtin_knowledge() -> None:
    if not KNOWLEDGE_DIR.exists():
        return
    for path in KNOWLEDGE_DIR.glob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_UPLOAD_SUFFIXES:
            try:
                upsert_document(path, source_name=path.name, scope="builtin")
            except Exception:
                continue


def upsert_document(path: Path, source_name: str, scope: str) -> tuple[str, int]:
    text = extract_text_from_file(path)
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    with db() as conn:
        existing = conn.execute("select id, content_hash from documents where path = ?", (str(path),)).fetchone()
        if existing and existing["content_hash"] == content_hash:
            return existing["id"], conn.execute(
                "select count(*) from chunks where document_id = ?", (existing["id"],)
            ).fetchone()[0]

        if existing:
            document_id = existing["id"]
            conn.execute("delete from chunks where document_id = ?", (document_id,))
            conn.execute("delete from documents where id = ?", (document_id,))
        else:
            document_id = uuid.uuid4().hex

        chunks = split_text(text)
        conn.execute(
            """
            insert into documents
            (id, source_name, path, scope, content_hash, char_count, chunk_count, created_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (document_id, source_name, str(path), scope, content_hash, len(text), len(chunks), now_iso()),
        )
        for index, (content, start, end) in enumerate(chunks):
            conn.execute(
                """
                insert into chunks
                (id, document_id, source_name, chunk_index, content, token_json, char_start, char_end)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    document_id,
                    source_name,
                    index,
                    content,
                    json.dumps(dict(Counter(tokenize(content))), ensure_ascii=False),
                    start,
                    end,
                ),
            )
        conn.commit()
    return document_id, len(chunks)


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        document = DocxDocument(str(path))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(parts)
    if suffix == ".xlsx":
        workbook = load_workbook(str(path), read_only=True, data_only=True)
        parts = []
        for sheet in workbook.worksheets:
            parts.append(f"工作表：{sheet.title}")
            for row_index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                values = [str(value).strip() for value in row if value is not None and str(value).strip()]
                if values:
                    parts.append(" | ".join(values))
                if row_index >= 160:
                    parts.append("（后续行已省略）")
                    break
        workbook.close()
        return "\n".join(parts)
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as source:
            return "\n".join(" | ".join(cell.strip() for cell in row) for row in csv.reader(source))
    if suffix in IMAGE_SUFFIXES:
        return ""
    raise HTTPException(status_code=400, detail="不支持的文件类型")


def get_document_row(document_id: str) -> sqlite3.Row:
    with db() as conn:
        row = conn.execute(
            """
            select id, source_name, path, scope, char_count, chunk_count, created_at
            from documents where id = ?
            """,
            (document_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="资料不存在")
    return row


def document_payload(row: sqlite3.Row) -> dict[str, Any]:
    suffix = Path(row["source_name"]).suffix.lower()
    return {
        "id": row["id"],
        "source_name": row["source_name"],
        "scope": row["scope"],
        "char_count": row["char_count"],
        "chunk_count": row["chunk_count"],
        "created_at": row["created_at"],
        "file_type": suffix.removeprefix(".").upper() or "FILE",
        "preview_kind": "image" if suffix in IMAGE_SUFFIXES else "pdf" if suffix == ".pdf" else "text",
        "view_url": f"/api/documents/{row['id']}/view",
        "download_url": f"/api/documents/{row['id']}/download",
    }


def parse_timetable(path: Path) -> list[dict[str, str]]:
    rows: list[list[str]] = []
    if path.suffix.lower() == ".xlsx":
        workbook = load_workbook(str(path), read_only=True, data_only=True)
        sheet = workbook.active
        rows = [
            ["" if value is None else str(value).strip() for value in row]
            for row in sheet.iter_rows(values_only=True)
        ]
        workbook.close()
    else:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as source:
            rows = [[cell.strip() for cell in row] for row in csv.reader(source)]

    rows = [row for row in rows if any(row)]
    if len(rows) < 2:
        return []
    aliases = {
        "course_name": ("课程名称", "课程", "科目", "course", "name"),
        "teacher": ("教师", "老师", "授课教师", "teacher"),
        "location": ("教室", "地点", "上课地点", "location", "room"),
        "day_of_week": ("星期", "周几", "上课日期", "day"),
        "class_time": ("节次", "时间", "上课时间", "time"),
        "weeks": ("周次", "教学周", "weeks", "week"),
    }
    headers = [cell.lower().replace(" ", "") for cell in rows[0]]
    indexes: dict[str, int] = {}
    for field, names in aliases.items():
        for index, header in enumerate(headers):
            if any(name.lower().replace(" ", "") in header for name in names):
                indexes[field] = index
                break
    if "course_name" not in indexes:
        indexes["course_name"] = 0

    entries = []
    for row in rows[1:201]:
        def value(field: str) -> str:
            index = indexes.get(field)
            return row[index].strip() if index is not None and index < len(row) else ""

        course_name = value("course_name")
        if not course_name:
            continue
        entries.append(
            {
                "course_name": course_name,
                "teacher": value("teacher"),
                "location": value("location"),
                "day_of_week": value("day_of_week"),
                "class_time": value("class_time"),
                "weeks": value("weeks"),
            }
        )
    return entries


def split_text(text: str) -> list[tuple[str, int, int]]:
    normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not normalized:
        return []
    chunks: list[tuple[str, int, int]] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + CHUNK_SIZE)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append((chunk, start, end))
        if end == len(normalized):
            break
        start = max(0, end - CHUNK_OVERLAP)
    return chunks


def tokenize(text: str) -> list[str]:
    words = []
    for word in jieba.lcut(text):
        token = word.strip().lower()
        if len(token) < 2 or token in STOPWORDS:
            continue
        if re.fullmatch(r"[\W_]+", token):
            continue
        words.append(token)
    return words


def retrieve_references(question: str, mode: AssistantMode, limit: int = 5) -> list[Reference]:
    query_tokens = Counter(tokenize(question))
    if not query_tokens:
        return []

    with db() as conn:
        rows = conn.execute(
            """
            select c.id as chunk_id, c.document_id, c.source_name, c.chunk_index,
                   c.content, c.token_json, c.char_start, c.char_end, d.scope
            from chunks c
            join documents d on d.id = c.document_id
            """
        ).fetchall()

    if not rows:
        return []

    chunk_tokens: list[Counter[str]] = []
    document_frequency: Counter[str] = Counter()
    for row in rows:
        counts = Counter(json.loads(row["token_json"]))
        chunk_tokens.append(counts)
        document_frequency.update(counts.keys())

    scored: list[tuple[float, sqlite3.Row]] = []
    total = len(rows)
    for row, counts in zip(rows, chunk_tokens, strict=True):
        score = tfidf_cosine(query_tokens, counts, document_frequency, total)
        content = row["content"]
        for token in query_tokens:
            if token in content:
                score += 0.05
        if mode in row["source_name"] or MODE_TITLES[mode][:2] in row["source_name"]:
            score += 0.08
        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    references = []
    for score, row in scored[:limit]:
        snippet = re.sub(r"\s+", " ", row["content"]).strip()[:220]
        references.append(
            Reference(
                document_id=row["document_id"],
                chunk_id=row["chunk_id"],
                source_name=row["source_name"],
                chunk_index=row["chunk_index"],
                char_start=row["char_start"],
                char_end=row["char_end"],
                snippet=snippet,
                score=round(float(score), 4),
            )
        )
    return references


def tfidf_cosine(
    query: Counter[str],
    chunk: Counter[str],
    df: Counter[str],
    total_docs: int,
) -> float:
    vocab = set(query) | set(chunk)
    dot = 0.0
    q_norm = 0.0
    c_norm = 0.0
    for token in vocab:
        idf = math.log((total_docs + 1) / (df.get(token, 0) + 1)) + 1.0
        q_weight = query.get(token, 0) * idf
        c_weight = chunk.get(token, 0) * idf
        dot += q_weight * c_weight
        q_norm += q_weight * q_weight
        c_norm += c_weight * c_weight
    if not q_norm or not c_norm:
        return 0.0
    return dot / (math.sqrt(q_norm) * math.sqrt(c_norm))


def ensure_session(session_id: str | None, mode: AssistantMode, first_message: str) -> str:
    now = now_iso()
    with db() as conn:
        if session_id:
            row = conn.execute("select id from sessions where id = ?", (session_id,)).fetchone()
            if row:
                conn.execute(
                    "update sessions set mode = ?, updated_at = ? where id = ?",
                    (mode, now, session_id),
                )
                conn.commit()
                return session_id

        new_id = uuid.uuid4().hex
        title = first_message.strip().replace("\n", " ")[:32] or MODE_TITLES[mode]
        conn.execute(
            "insert into sessions (id, mode, title, created_at, updated_at) values (?, ?, ?, ?, ?)",
            (new_id, mode, title, now, now),
        )
        conn.commit()
        return new_id


def add_message(session_id: str, role: str, mode: AssistantMode, content: str) -> None:
    with db() as conn:
        conn.execute(
            "insert into messages (session_id, role, mode, content, created_at) values (?, ?, ?, ?, ?)",
            (session_id, role, mode, content, now_iso()),
        )
        conn.execute("update sessions set updated_at = ? where id = ?", (now_iso(), session_id))
        conn.commit()


def get_recent_history(session_id: str, limit: int = 12) -> list[dict[str, str]]:
    with db() as conn:
        rows = conn.execute(
            """
            select role, content from messages
            where session_id = ?
            order by id desc
            limit ?
            """,
            (session_id, limit),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def build_messages(
    mode: AssistantMode,
    question: str,
    references: list[Reference],
    history: list[dict[str, str]],
) -> list[dict[str, str]]:
    context = "\n\n".join(
        f"【资料：{ref.source_name} #片段{ref.chunk_index + 1}】\n{ref.snippet}"
        for ref in references
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPTS[mode]}]
    if context:
        messages.append(
            {
                "role": "system",
                "content": (
                    "以下是本地知识库检索到的资料。请优先依据资料回答，并在答案末尾用“参考资料”列出文件名。"
                    f"\n\n{context}"
                ),
            }
        )
    for item in history:
        if item["role"] in {"user", "assistant"}:
            messages.append({"role": item["role"], "content": item["content"]})
    if not history or history[-1].get("content") != question:
        messages.append({"role": "user", "content": question})
    return messages


def build_mock_answer(
    mode: AssistantMode,
    question: str,
    references: list[Reference],
    history: list[dict[str, str]],
) -> str:
    title = MODE_TITLES[mode]
    history_note = "这是本轮新问题。"
    if len(history) > 1:
        last_user = next((m["content"] for m in reversed(history[:-1]) if m["role"] == "user"), "")
        if last_user:
            history_note = f"我会延续你前面提到的“{last_user[:24]}”来回答。"

    refs = "\n".join(
        f"- {ref.source_name}：片段 {ref.chunk_index + 1}，匹配分 {ref.score}"
        for ref in references[:3]
    )
    refs = refs or "- 当前知识库没有强匹配资料，以下为模拟通用建议。"

    if mode == "learning":
        body = (
            "## 学习规划\n"
            "1. 先把目标拆成“资料理解、知识点梳理、练习验证、复盘调整”四步。\n"
            "2. 每天只安排 1 个主知识点，配 3-5 道练习题，避免计划过满。\n"
            "3. 如果要准备智能体竞赛，建议顺序是 Python 基础、FastAPI、模型 API、知识库检索、演示视频。\n\n"
            "## 下一步任务\n"
            "- 今天完成资料整理和接口跑通。\n"
            "- 明天加入真实 API 和一份课程资料检索。\n"
            "- 第三天录制第一次 3 分钟演示。"
        )
    elif mode == "teaching":
        body = (
            "## 教学辅助方案\n"
            "1. 教学目标：明确学生课后能完成的可观察任务。\n"
            "2. 课堂活动：用校园真实场景引入，再安排小组任务。\n"
            "3. 试题生成：覆盖基础题、应用题、开放题三类。\n"
            "4. Rubric：按准确性、完整性、表达清晰度、创新性评分。"
        )
    elif mode == "audit":
        body = (
            "## 审计学习方案\n"
            "1. 先把问题放入“审计目标、风险识别、审计程序、证据获取、结论表达”框架。\n"
            "2. 如果学习审计学基础，建议按审计本质、三类审计、审计准则、审计流程、证据与底稿、报告写作推进。\n"
            "3. 如果做审计案例，先找异常事实，再说明违反依据、影响后果、审计程序和证据来源。\n"
            "4. 如果做智能审计数据分析，可先筛查重复报销、供应商集中度、异常金额、资产闲置和日期异常。\n\n"
            "## 今日可执行任务\n"
            "- 选择一个审计主题生成思维导图。\n"
            "- 根据同一主题生成 6 道测验题。\n"
            "- 用一个脱敏案例生成审计工作底稿框架。"
        )
    elif mode == "safety":
        body = (
            "## 风险判断\n"
            "如果事件正在发生，或已经有人受伤、出现火情、烟雾、威胁、失联等情况，请立即离开危险区域并拨打 110、119 或 120。\n\n"
            "## 立即行动\n"
            "1. 先保证自己在安全位置，不独自处理高风险现场。\n"
            "2. 简短记录地点、时间、现场情况和是否有人受伤。\n"
            "3. 可通过安全助手生成演示工单；真实处置仍以学校保卫处、辅导员/导师和公共紧急电话为准。\n\n"
            "## 信息保护\n"
            "- 不公开身份证号、手机号、宿舍门牌、他人照片等敏感信息。\n"
            "- 涉及心理危机、欺凌或骚扰时，优先联系可信赖的人和学校正式支持渠道。"
        )
    else:
        body = (
            "## 事务办理建议\n"
            "1. 先确认办理对象、办理时间和是否需要线上预约。\n"
            "2. 准备身份证明、申请表、证明材料或截图。\n"
            "3. 提交后保存办理编号或结果截图。\n"
            "4. 如果资料和学校最新通知不一致，以教务处、学院办公室或学生服务中心通知为准。"
        )

    return (
        f"# {title}答复\n\n"
        f"你问的是：{question}\n\n"
        f"{history_note}\n\n"
        f"{body}\n\n"
        f"## 参考资料\n{refs}"
    )


def deep_research_prompt(question: str) -> str:
    return (
        "请使用深度研究方式处理下面的问题：先拆分子问题，再检索和比较知识库证据，"
        "区分事实、推断与待核验信息，最后给出结构化结论、依据、风险和后续行动。"
        "不得为了完整性编造资料。\n\n"
        f"研究问题：{question}"
    )


def prepare_model_question(request: ChatRequest) -> str:
    question = deep_research_prompt(request.message) if request.deep_research else request.message
    if request.web_search:
        question = (
            "如当前模型或服务具备联网检索能力，请检索最新可靠来源并标注来源；"
            "如不具备，请明确说明，不能虚构检索结果。\n\n"
            f"{question}"
        )
    return question


def add_mock_research_frame(answer: str, question: str) -> str:
    return (
        "# 深度研究\n\n"
        f"研究问题：{question}\n\n"
        "## 研究路径\n"
        "1. 拆分核心概念、适用场景和判断标准。\n"
        "2. 对照知识库资料，区分已知事实、合理推断和待核验信息。\n"
        "3. 从支持证据、反例、风险和可执行建议四个角度形成结论。\n\n"
        f"{answer}"
    )


def add_mock_web_search_note(answer: str) -> str:
    return (
        "> 已开启联网搜索，但当前运行在模拟模式，未执行真实网络检索。"
        "接入支持搜索的模型服务后将返回可核验来源。\n\n"
        f"{answer}"
    )


def artifact_payload(
    artifact_type: str,
    prompt: str,
    mode: AssistantMode,
    content: str,
    references: list[Reference],
) -> dict[str, Any]:
    artifact_id = uuid.uuid4().hex
    labels = {
        "mindmap": "思维导图",
        "quiz": "练习测验",
        "outline": "文件大纲",
        "audit-workpaper": "审计工作底稿",
    }
    title = f"{prompt[:50]} · {labels.get(artifact_type, '生成内容')}"
    with db() as conn:
        conn.execute(
            """
            insert into artifacts
            (id, artifact_type, title, prompt, mode, content, archived_document_id, created_at)
            values (?, ?, ?, ?, ?, ?, null, ?)
            """,
            (artifact_id, artifact_type, title, prompt, mode, content, now_iso()),
        )
        conn.commit()
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "title": title,
        "content": content,
        "archived": False,
        "mock": is_mock_mode(),
        "references": [ref.model_dump() for ref in references],
    }


def artifact_summary(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "artifact_type": row["artifact_type"],
        "title": row["title"],
        "prompt": row["prompt"],
        "mode": row["mode"],
        "archived": bool(row["archived_document_id"]),
        "document_id": row["archived_document_id"],
        "created_at": row["created_at"],
    }


def build_mock_outline(topic: str, references: list[Reference]) -> str:
    return (
        f"# {topic} 文件大纲\n\n"
        "## 一、学习目标\n"
        "- 明确核心概念、适用场景和知识边界。\n"
        "- 建立从理论到案例再到练习的复习路径。\n\n"
        "## 二、核心知识结构\n"
        "1. 基础概念与关键术语\n"
        "2. 制度、准则与方法依据\n"
        "3. 标准流程与关键控制点\n"
        "4. 典型案例与常见风险\n\n"
        "## 三、重点与难点\n"
        "- 重点：将目标、风险、程序、证据和结论串联起来。\n"
        "- 难点：在案例中选择充分、适当且可追溯的证据。\n\n"
        "## 四、复习与练习\n"
        "1. 用思维导图复述章节关系。\n"
        "2. 完成概念题、判断题和案例分析题。\n"
        "3. 对错误题目回查知识库原始资料。\n\n"
        f"## 参考资料\n{reference_lines(references)}"
    )


def build_mock_mindmap(topic: str, references: list[Reference]) -> str:
    source_lines = reference_lines(references)
    return (
        f"# {topic} 思维导图\n\n"
        "```mermaid\n"
        "mindmap\n"
        f"  root(({escape_mermaid(topic)}))\n"
        "    审计基础\n"
        "      审计目标\n"
        "      审计分类\n"
        "      职业道德\n"
        "    审计流程\n"
        "      审计计划\n"
        "      风险评估\n"
        "      审计实施\n"
        "      审计报告\n"
        "    审计证据\n"
        "      书面证据\n"
        "      实物证据\n"
        "      口头证据\n"
        "      分析性证据\n"
        "    南审特色\n"
        "      政府审计\n"
        "      智能审计\n"
        "      审计案例实训\n"
        "```\n\n"
        "## 复习要点\n"
        "1. 先区分政府审计、内部审计和社会审计的主体、目标、依据和报告对象。\n"
        "2. 用“目标-风险-程序-证据-结论”串联每个案例，不要只背概念。\n"
        "3. 学审计法规时优先看适用主体、程序要求、权限边界和法律责任。\n"
        "4. 做案例题时先识别异常，再补充审计程序和证据来源。\n"
        "5. 数据审计训练可从重复报销、金额异常、供应商集中度和资产闲置开始。\n\n"
        f"## 参考资料\n{source_lines}"
    )


def build_mock_quiz(topic: str, question_count: int, references: list[Reference]) -> str:
    templates = [
        (
            "选择题",
            "风险导向审计中，审计人员首先应重点完成哪项工作？",
            "C",
            "A. 直接出具审计报告\nB. 随机抽取凭证\nC. 了解被审计单位及其环境并评估风险\nD. 只核对账表金额",
            "风险评估决定后续审计程序的性质、时间和范围。",
        ),
        (
            "判断题",
            "审计证据只包括书面文件，访谈记录和实地观察不能作为审计证据。",
            "错",
            "",
            "审计证据可以包括书面证据、实物证据、口头证据、环境证据和分析性证据。",
        ),
        (
            "简答题",
            "简述审计工作底稿应当记录哪些核心内容。",
            "参考要点：审计事项、审计目标、审计程序、获取证据、审计发现、判断依据、审计结论、复核记录。",
            "",
            "底稿需要支持审计结论，并形成可追溯证据链。",
        ),
        (
            "案例分析题",
            "某单位将 81 万元办公设备采购拆分为 28 万、26 万、27 万三次采购。请识别风险并设计审计程序。",
            "参考要点：存在化整为零规避公开招标风险；应检查采购计划、预算批复、合同、发票、验收资料、供应商关联关系，并访谈经办人员。",
            "",
            "案例题要同时回答风险点、证据和程序。",
        ),
        (
            "选择题",
            "内部审计在组织治理中的核心价值更接近以下哪一项？",
            "B",
            "A. 替代管理层审批\nB. 评价并改进风险管理、控制和治理过程\nC. 只负责财务记账\nD. 决定业务部门绩效奖金",
            "内部审计强调独立客观确认与咨询，不能替代管理层履职。",
        ),
        (
            "简答题",
            "比较政府审计、内部审计、社会审计的主要差异。",
            "参考要点：主体不同、服务对象不同、依据不同、强制性不同、报告使用者不同；政府审计偏公共资金监督，内部审计服务组织治理，社会审计面向鉴证服务。",
            "",
            "三类审计对比是审计学入门高频考点。",
        ),
    ]
    selected = templates[: max(1, min(question_count, len(templates)))]
    lines = [f"# {topic} 测验题", ""]
    for index, (kind, question, answer, options, explanation) in enumerate(selected, start=1):
        lines.extend(
            [
                f"## {index}. {kind}",
                question,
                "",
            ]
        )
        if options:
            lines.extend([options, ""])
        lines.extend(
            [
                f"- 答案：{answer}",
                f"- 解析：{explanation}",
                "- 难度：中",
                "- 知识点：审计基础 / 审计程序 / 审计证据",
                "",
            ]
        )
    lines.extend(["## 参考资料", reference_lines(references)])
    return "\n".join(lines)


def build_mock_workpaper(topic: str, references: list[Reference]) -> str:
    return (
        f"# 审计工作底稿框架：{topic}\n\n"
        "## 1. 审计事项\n"
        "围绕案例或资料中出现的资金拨付、政府采购、科研经费、资产管理、供应商关联关系等事项开展审计。\n\n"
        "## 2. 审计目标\n"
        "- 判断业务是否真实、合法、合规、有效。\n"
        "- 判断内部控制设计和执行是否存在重大缺陷。\n"
        "- 判断是否存在损失浪费、违规采购、虚假报销或利益输送风险。\n\n"
        "## 3. 主要风险点\n"
        "- 大额资金审批缺失或审批链条不完整。\n"
        "- 同类采购拆分，规避公开招标或集体决策。\n"
        "- 供应商与关键岗位人员存在关联关系。\n"
        "- 报销、资产、合同、验收资料之间无法相互印证。\n\n"
        "## 4. 审计程序\n"
        "1. 获取预算、合同、发票、验收单、付款记录和审批流程记录。\n"
        "2. 对同一供应商、同一项目、相近日期、相近金额进行分组分析。\n"
        "3. 对关键样本做穿行测试，核对申请、审批、采购、验收、付款全过程。\n"
        "4. 查询供应商工商信息，排查关联关系和异常集中度。\n"
        "5. 对资产实物或服务交付成果进行现场核查。\n\n"
        "## 5. 证据清单\n"
        "| 证据 | 作用 |\n"
        "| --- | --- |\n"
        "| 预算批复/项目计划 | 判断事项是否纳入预算和计划 |\n"
        "| 合同/采购文件 | 判断采购程序和合同条款是否规范 |\n"
        "| 发票/付款凭证 | 判断资金支付真实性 |\n"
        "| 验收报告/资产台账 | 判断交付和资产管理情况 |\n"
        "| 访谈记录/工商信息 | 判断责任链条与关联关系 |\n\n"
        "## 6. 初步结论\n"
        "如资料中异常能够被多项证据相互印证，可形成“风险事实-违反依据-影响后果-整改建议”的结论表达。\n\n"
        f"## 参考资料\n{reference_lines(references)}"
    )


async def translate_learning_text(
    source_text: str,
    target_language: str,
    references: list[Reference],
) -> str:
    if is_mock_mode():
        return build_mock_translation(source_text, target_language, references)
    return await call_model_once(
        "audit",
        (
            f"请把以下学习资料翻译为{target_language}，要求术语准确、适合审计学课程学习；"
            "遇到审计术语请尽量保留中英对照；不要增加原文没有的事实。\n\n"
            f"{source_text}"
        ),
        references,
        [],
    )


async def summarize_translation_text(
    source_text: str,
    target_language: str,
    references: list[Reference],
) -> str:
    if is_mock_mode():
        return build_mock_translation_summary(source_text, target_language, references)
    return await call_model_once(
        "audit",
        (
            f"请根据以下已翻译或待翻译的文档内容生成{target_language}要点总结。"
            "要求：1. 中文要点和 English key points 成对出现；"
            "2. 保留审计学术语；3. 给出适合学生复习的行动建议；"
            "4. 不要添加原文没有的事实。\n\n"
            f"{source_text}"
        ),
        references,
        [],
    )


def build_mock_translation(source_text: str, target_language: str, references: list[Reference]) -> str:
    term_map = {
        "audit evidence": "审计证据",
        "materiality": "重要性",
        "internal control": "内部控制",
        "substantive procedure": "实质性程序",
        "risk assessment": "风险评估",
        "working paper": "审计工作底稿",
        "audit report": "审计报告",
        "government audit": "政府审计",
        "internal audit": "内部审计",
        "external audit": "外部审计",
    }
    translated = source_text.strip()
    for english, chinese in term_map.items():
        translated = re.sub(english, f"{chinese}（{english}）", translated, flags=re.IGNORECASE)
    preview = translated[:5000]
    return (
        f"# {target_language}译文草稿\n\n"
        "当前处于模拟模式，系统已完成审计术语替换和译文结构化；接入真实模型 API 后会输出完整自然语言翻译。\n\n"
        "## 术语处理\n"
        "- audit evidence：审计证据\n"
        "- materiality：重要性\n"
        "- internal control：内部控制\n"
        "- substantive procedure：实质性程序\n"
        "- working paper：审计工作底稿\n\n"
        "## 译文\n"
        f"{preview}\n\n"
        f"## 参考资料\n{reference_lines(references)}"
    )


def build_mock_translation_summary(source_text: str, target_language: str, references: list[Reference]) -> str:
    compact = re.sub(r"\s+", " ", source_text).strip()[:360]
    return (
        "# 双语要点总结 / Bilingual Key Points\n\n"
        "## 中文要点\n"
        "- 文档重点围绕审计证据、内部控制、风险评估和审计程序展开，适合作为课程复习材料。\n"
        "- 复习时建议按“概念定义-适用场景-证据来源-案例判断”整理笔记。\n"
        "- 对涉及法规、准则或案例结论的内容，应回到原始资料核对依据。\n\n"
        "## English Key Points\n"
        "- The document focuses on audit evidence, internal control, risk assessment, and audit procedures.\n"
        "- Review the material through definitions, use cases, evidence sources, and case-based judgments.\n"
        "- For rules, standards, or case conclusions, verify the basis in the original source material.\n\n"
        "## 复习建议 / Study Actions\n"
        "- 将术语整理成中英对照表，并为每个术语补充一个审计案例。\n"
        "- 把章节结构导入思维导图，再生成 5-8 道练习题检测掌握程度。\n\n"
        f"## 原文摘录 / Source Excerpt\n{compact}\n\n"
        f"## 参考资料\n{reference_lines(references)}"
    )


def save_translation_docx(
    source_name: str,
    target_language: str,
    translated: str,
    references: list[Reference],
) -> str:
    export_id = uuid.uuid4().hex
    output_path = REPORT_DIR / f"translation_{export_id}.docx"
    document = DocxDocument()
    document.add_heading(f"{Path(source_name).stem} {target_language}译文", level=0)
    document.add_paragraph(f"生成时间：{now_iso()}")
    document.add_paragraph(f"源文件：{source_name}")
    for block in translated.split("\n"):
        text = block.strip()
        if not text:
            continue
        if text.startswith("# "):
            document.add_heading(text[2:], level=1)
        elif text.startswith("## "):
            document.add_heading(text[3:], level=2)
        elif text.startswith("- "):
            document.add_paragraph(text[2:], style="List Bullet")
        else:
            document.add_paragraph(text)
    if references:
        document.add_heading("检索参考", level=2)
        for ref in references:
            document.add_paragraph(f"{ref.source_name} 片段 {ref.chunk_index + 1}：{ref.snippet}", style="List Bullet")
    document.save(output_path)
    save_export(
        export_id=export_id,
        path=output_path,
        file_name=f"{Path(source_name).stem}-{target_language}译文.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    return export_id


def save_export(export_id: str, path: Path, file_name: str, media_type: str) -> None:
    with db() as conn:
        conn.execute(
            "insert into exports (id, file_path, file_name, media_type, created_at) values (?, ?, ?, ?, ?)",
            (export_id, str(path), file_name, media_type, now_iso()),
        )
        conn.commit()


def reference_lines(references: list[Reference]) -> str:
    if not references:
        return "- 当前知识库没有强匹配资料，建议上传课程课件或案例材料后重新生成。"
    return "\n".join(
        f"- {ref.source_name}：片段 {ref.chunk_index + 1}，匹配分 {ref.score}"
        for ref in references[:5]
    )


def escape_mermaid(text: str) -> str:
    cleaned = re.sub(r"[(){}\[\]\"']", "", text)
    return cleaned[:40] or "审计学习"


def get_model_config() -> dict[str, Any]:
    api_key = os.getenv("MODEL_API_KEY", "").strip()
    base_url = normalize_model_base_url(os.getenv("MODEL_BASE_URL", ""))
    model = os.getenv("MODEL_NAME", "").strip()
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "configured": bool(api_key and base_url and model),
    }


def normalize_model_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]
    return base_url.rstrip("/")


def mask_model_base_url(base_url: str) -> str:
    if not base_url:
        return ""
    parsed = urlparse(base_url)
    if not parsed.hostname:
        return base_url
    host = parsed.hostname
    if len(host) > 18:
        host = f"{host[:8]}...{host[-7:]}"
    netloc = host
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return parsed._replace(netloc=netloc).geturl()


async def call_model_once(
    mode: AssistantMode,
    question: str,
    references: list[Reference],
    history: list[dict[str, str]],
) -> str:
    tokens = []
    async for token in call_model_stream(mode, question, references, history):
        tokens.append(token)
    return "".join(tokens)


async def call_model_stream(
    mode: AssistantMode,
    question: str,
    references: list[Reference],
    history: list[dict[str, str]],
) -> AsyncIterator[str]:
    config = get_model_config()
    if not config["configured"]:
        raise RuntimeError("模型 API 未配置完整，请检查 .env")

    payload = {
        "model": config["model"],
        "messages": build_messages(mode, question, references, history),
        "temperature": 0.4,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=90) as client:
        async with client.stream(
            "POST",
            f"{config['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
            json=payload,
        ) as response:
            if response.status_code >= 400:
                body = await response.aread()
                raise RuntimeError(f"模型接口调用失败：HTTP {response.status_code} {body[:300].decode(errors='ignore')}")

            content_type = response.headers.get("content-type", "")
            if "text/event-stream" not in content_type:
                body = await response.aread()
                data = json.loads(body)
                answer = data["choices"][0]["message"]["content"]
                async for token in slice_for_stream(answer):
                    yield token
                return

            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                data_text = line.removeprefix("data:").strip()
                if data_text == "[DONE]":
                    break
                try:
                    data = json.loads(data_text)
                except json.JSONDecodeError:
                    continue
                token = data.get("choices", [{}])[0].get("delta", {}).get("content")
                if token:
                    yield token


async def slice_for_stream(text: str, step: int = 8) -> AsyncIterator[str]:
    for index in range(0, len(text), step):
        await asyncio.sleep(0.01)
        yield text[index : index + step]


def record_api_call(
    session_id: str,
    mode: AssistantMode,
    model_name: str,
    input_text: str,
    output_text: str,
    success: bool,
    error: str,
    duration_ms: int,
    mock: bool,
) -> None:
    with db() as conn:
        conn.execute(
            """
            insert into api_calls
            (session_id, created_at, model_name, mode, input_summary, output_summary,
             success, error, duration_ms, mock)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                now_iso(),
                model_name,
                mode,
                summarize(input_text),
                summarize(output_text),
                1 if success else 0,
                error,
                duration_ms,
                1 if mock else 0,
            ),
        )
        conn.commit()


def summarize(text: str, limit: int = 160) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:limit]


class AffairsArticleParser(HTMLParser):
    BLOCK_TAGS = {"article", "br", "dd", "div", "dl", "dt", "h1", "h2", "h3", "h4", "li", "p", "section", "table", "td", "th", "tr"}
    SKIP_TAGS = {"footer", "header", "nav", "noscript", "script", "style", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.fragments: list[str] = []
        self.links: list[dict[str, str]] = []
        self.skip_depth = 0
        self.current_link: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.fragments.append("\n")
        if tag == "a":
            href = dict(attrs).get("href") or ""
            self.current_link = {"href": href, "text": []}

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "a" and self.current_link is not None:
            text = re.sub(r"\s+", " ", "".join(self.current_link["text"])).strip()
            self.links.append({"href": str(self.current_link["href"]), "text": text})
            self.current_link = None
        if tag in self.BLOCK_TAGS:
            self.fragments.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        self.fragments.append(data)
        if self.current_link is not None:
            self.current_link["text"].append(data)


def affairs_source_allows_url(article_url: str, source: dict[str, Any]) -> bool:
    parsed = urlparse(article_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.lower()
    allowed_hosts = source.get("allowed_hosts") or ["nau.edu.cn"]
    if not any(hostname == host or hostname.endswith(f".{host}") for host in allowed_hosts):
        return False
    path_markers = source.get("article_path_markers") or ["page.htm"]
    return any(marker in parsed.path for marker in path_markers)


def affairs_safe_related_url(raw_url: str, article_url: str) -> str:
    candidate = urljoin(article_url, unescape(raw_url).strip())
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    hostname = parsed.hostname.lower()
    article_host = (urlparse(article_url).hostname or "").lower()
    if hostname == article_host or hostname.endswith(".nau.edu.cn") or hostname in AFFAIRS_SERVICE_HOSTS or hostname.endswith(".neea.edu.cn"):
        return candidate
    return ""


AFFAIRS_TEMPLATE_LINK_TEXTS = {
    "课表查询",
    "调停课查询",
    "教学信息系统",
    "创新创业教育平台",
    "毕业实习智能管理平台",
    "毕业论文（设计）管理系统",
}


def affairs_link_is_template_noise(link_text: str, safe_url: str) -> bool:
    compact = re.sub(r"\s+", "", link_text)
    if compact in AFFAIRS_TEMPLATE_LINK_TEXTS:
        return True
    path = urlparse(safe_url).path.lower()
    if any(marker in path for marker in ("/_s", "/system/", "/list.", "/main.")):
        return True
    return False


def affairs_link_is_actionable_entry(link_text: str, safe_url: str, title: str) -> bool:
    hostname = (urlparse(safe_url).hostname or "").lower()
    compact = re.sub(r"\s+", "", link_text)
    strong_keywords = (
        "报名入口",
        "报名系统",
        "申请入口",
        "申报入口",
        "办理入口",
        "缴费入口",
        "下载",
        "附件",
        "名单",
        "表格",
    )
    if hostname in {"cet-bm.neea.edu.cn", "cet.neea.edu.cn"}:
        return True
    if any(keyword in compact for keyword in strong_keywords):
        return True
    if any(keyword in title for keyword in ("四六级", "考试", "报名")) and any(keyword in compact for keyword in ("报名", "考试")):
        return True
    return False


def clean_affairs_news_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def affairs_news_date(article_url: str, context: str = "") -> date | None:
    path_match = re.search(r"/(20\d{2})/(\d{2})(\d{2})/", urlparse(article_url).path)
    if path_match:
        try:
            return date(int(path_match.group(1)), int(path_match.group(2)), int(path_match.group(3)))
        except ValueError:
            return None
    context_match = re.search(r"(20\d{2})[./年-](\d{1,2})[./月-](\d{1,2})日?", context)
    if not context_match:
        return None
    try:
        return date(int(context_match.group(1)), int(context_match.group(2)), int(context_match.group(3)))
    except ValueError:
        return None


def affairs_news_summary(title: str, source_name: str) -> str:
    summaries = [
        (("教材", "选购"), "查看教材选购对象、开放时间、操作路径和逾期处理要求。"),
        (("考试", "考情", "四六级"), "查看考试安排、报名节点、资格要求或考试注意事项。"),
        (("奖学金", "助学", "资助"), "查看奖助项目的适用对象、评审结果、材料和时间节点。"),
        (("课程", "课表", "培养"), "查看课程、课表或培养环节的对象范围和具体安排。"),
        (("图书", "讲座", "数据库"), "查看图书馆服务、资源或活动的内容、时间和参与方式。"),
        (("毕业", "学位", "论文"), "查看毕业、学位或论文相关工作的对象、材料和时间安排。"),
        (("勤工", "岗位"), "查看勤工助学岗位、申请条件和线上办理流程。"),
    ]
    for keywords, summary in summaries:
        if any(keyword in title for keyword in keywords):
            return summary
    return f"来自{source_name}的官方文章，点击查看适用对象、完整要求和时间节点。"


def extract_affairs_news(html_text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    anchor_pattern = re.compile(
        r"<a\b[^>]*?href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in anchor_pattern.finditer(html_text):
        title = clean_affairs_news_text(match.group(2))
        if len(title) < 8:
            continue
        article_url = urljoin(source["url"], unescape(match.group(1)).strip())
        if not affairs_source_allows_url(article_url, source):
            continue
        if article_url in seen:
            continue
        context = clean_affairs_news_text(
            html_text[max(0, match.start() - 120) : min(len(html_text), match.end() + 260)]
        )
        published = affairs_news_date(article_url, context)
        if not published:
            continue
        seen.add(article_url)
        items.append(
            {
                "id": f"live-{hashlib.sha1(article_url.encode('utf-8')).hexdigest()[:12]}",
                "title": title[:120],
                "summary": affairs_news_summary(title, source["name"]),
                "publishedDate": published.isoformat(),
                "deadline": "",
                "sourceName": source["name"],
                "sourceUrl": article_url,
                "icon": source["icon"],
                "audiences": list(source["audiences"]),
                "live": True,
            }
        )
    return items


def normalize_affairs_article_text(html_text: str, title: str) -> tuple[list[str], list[dict[str, str]]]:
    parser = AffairsArticleParser()
    parser.feed(html_text[:AFFAIRS_ARTICLE_MAX_CHARS])
    lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(parser.fragments).splitlines()]
    lines = [line for line in lines if line]

    exact_matches = [index for index, line in enumerate(lines) if line == title]
    partial_matches = [index for index, line in enumerate(lines) if title in line]
    if exact_matches:
        lines = lines[exact_matches[-1] :]
    elif partial_matches:
        lines = lines[partial_matches[-1] :]

    stop_markers = ("南京审计大学版权所有", "友情链接：", "主办单位：教育部教育考试院")
    for index, line in enumerate(lines):
        if index > 2 and any(marker in line for marker in stop_markers):
            lines = lines[:index]
            break
    return lines[:180], parser.links


def parse_affairs_date_text(value: str) -> date | None:
    match = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", value)
    if not match:
        match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", value)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def extract_affairs_sections(lines: list[str]) -> list[dict[str, str]]:
    heading_pattern = re.compile(r"^(?:[一二三四五六七八九十]+、|\d+[.、])\s*(.{2,40})$")
    sections: list[dict[str, str]] = []
    current: dict[str, Any] | None = None
    for line in lines:
        heading = heading_pattern.match(line)
        if heading:
            if current and current["lines"]:
                sections.append({"title": current["title"], "content": " ".join(current["lines"])[:700]})
            current = {"title": heading.group(1).strip(), "lines": []}
            if len(sections) >= 8:
                break
            continue
        if current and len(" ".join(current["lines"])) < 900:
            current["lines"].append(line)
    if current and current["lines"] and len(sections) < 8:
        sections.append({"title": current["title"], "content": " ".join(current["lines"])[:700]})
    return sections


def extract_affairs_article_details(
    html_text: str,
    item: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    lines, links = normalize_affairs_article_text(html_text, str(item["title"]))
    article_text = "\n".join(lines)
    if len(article_text) < 80:
        return {"contentFetched": False, "contentStatus": "正文内容不足"}

    dated_fragments = re.findall(
        r"20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*\d{1,2}[:：]\d{2})?|20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?:\s*\d{1,2}[:：]\d{2})?",
        article_text,
    )
    relative_fragments = re.findall(
        r"(?<!\d)(?:\d{1,2}\s*月\s*\d{1,2}\s*日)(?:\s*(?:至|—|-)\s*\d{1,2}\s*月\s*\d{1,2}\s*日)?(?:\s*\d{1,2}\s*时(?:\s*\d{1,2}\s*分)?)?",
        article_text,
    )
    time_nodes = list(
        dict.fromkeys(re.sub(r"\s+", "", value) for value in [*dated_fragments, *relative_fragments])
    )[:10]

    deadline = ""
    deadline_text = ""
    time_keywords = ("报名时间", "申请时间", "截止", "截至", "逾期", "开放时间", "办理时间")
    for line in lines:
        if not any(keyword in line for keyword in time_keywords):
            continue
        candidates = re.findall(
            r"20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日(?:\s*\d{1,2}[:：]\d{2})?|20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?:\s*\d{1,2}[:：]\d{2})?",
            line,
        )
        if candidates:
            parsed_deadline = parse_affairs_date_text(candidates[-1])
            if parsed_deadline:
                deadline = parsed_deadline.isoformat()
                deadline_text = candidates[-1]

    contacts = list(dict.fromkeys(re.findall(r"(?<!\d)(?:0\d{2,3}[-－— ]?)?\d{7,8}(?!\d)", article_text)))[:6]
    audiences: list[str] = []
    if any(term in article_text for term in ("全体在校学生", "含研究生", "本科生和研究生")):
        audiences = ["undergraduate", "graduate"]
    else:
        if any(term in article_text for term in ("本科生", "普本学生", "本科学生")):
            audiences.append("undergraduate")
        if "研究生" in article_text:
            audiences.append("graduate")
    if not audiences:
        audiences = list(source["audiences"])

    attachments: list[dict[str, str]] = []
    service_links: list[dict[str, str]] = []
    for link in links:
        safe_url = affairs_safe_related_url(link["href"], str(item["sourceUrl"]))
        if not safe_url:
            continue
        link_text = link["text"] or Path(urlparse(safe_url).path).name
        if affairs_link_is_template_noise(link_text, safe_url):
            continue
        path = urlparse(safe_url).path.lower()
        if "附件" in link_text or re.search(r"\.(?:pdf|docx?|xlsx?|pptx?|zip|rar)$", path):
            if safe_url != item["sourceUrl"] and all(entry["url"] != safe_url for entry in attachments):
                attachments.append({"title": link_text[:100] or "附件", "url": safe_url})
            continue
        if affairs_link_is_actionable_entry(link_text, safe_url, str(item["title"])):
            if safe_url != item["sourceUrl"] and all(entry["url"] != safe_url for entry in service_links):
                hostname = (urlparse(safe_url).hostname or "").lower()
                service_links.append({"title": link_text[:100] or hostname, "url": safe_url})

    action_items = [
        line[:220]
        for line in lines
        if len(line) >= 12 and any(word in line for word in ("必须", "务必", "需要", "请于", "请在", "应当"))
    ][:6]
    summary_candidates = [
        line for line in lines[1:]
        if len(line) >= 24 and not any(marker in line for marker in ("发布者：", "发布时间：", "浏览次数："))
    ]
    content_summary = " ".join(summary_candidates[:2])[:320] or affairs_news_summary(str(item["title"]), source["name"])

    return {
        "contentFetched": True,
        "contentStatus": "官方内容已概括",
        "summary": content_summary,
        "contentExcerpt": "\n".join(lines[:36])[:1800],
        "deadline": deadline,
        "deadlineText": deadline_text,
        "timeNodes": time_nodes,
        "audiences": audiences,
        "contacts": contacts,
        "serviceLinks": service_links[:6],
        "attachments": attachments[:6],
        "actionItems": action_items,
        "sections": extract_affairs_sections(lines),
    }


async def fetch_affairs_live_news(profile: str) -> list[dict[str, Any]]:
    sources = [source for source in AFFAIRS_NEWS_SOURCES if profile in source["audiences"]]
    article_semaphore = asyncio.Semaphore(8)

    async def fetch_article(
        client: httpx.AsyncClient,
        item: dict[str, Any],
        source: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            async with article_semaphore:
                response = await client.get(item["sourceUrl"])
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type or len(response.content) > AFFAIRS_ARTICLE_MAX_CHARS * 4:
                return item
            details = extract_affairs_article_details(response.text, item, source)
            return {**item, **details}
        except Exception:
            return item

    async def fetch_source(client: httpx.AsyncClient, source: dict[str, Any]) -> list[dict[str, Any]]:
        discovered: list[dict[str, Any]] = []
        try:
            response = await client.get(source["url"])
            response.raise_for_status()
            discovered = extract_affairs_news(response.text, source)
        except Exception:
            pass
        verified_seeds = [
            {**item, "live": True}
            for item in AFFAIRS_NEWS_FALLBACK
            if item.get("sourceName") == source["name"] and affairs_source_allows_url(str(item["sourceUrl"]), source)
        ]
        candidates_by_url = {item["sourceUrl"]: item for item in verified_seeds}
        candidates_by_url.update({item["sourceUrl"]: item for item in discovered})
        candidates = list(candidates_by_url.values())
        candidates.sort(key=lambda item: item["publishedDate"], reverse=True)
        selected = candidates[:AFFAIRS_ARTICLES_PER_SOURCE]
        return await asyncio.gather(*(fetch_article(client, item, source) for item in selected))

    timeout = httpx.Timeout(7.0, connect=3.5)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 NAU-Smart-Campus-Agent/1.0"},
    ) as client:
        groups = await asyncio.gather(*(fetch_source(client, source) for source in sources))
    return [item for group in groups for item in group]


def affairs_news_timeline_is_valid(item: dict[str, Any], today: date) -> bool:
    """Reject notices whose publication, URL year, or deadline contradicts the timeline."""
    try:
        published = date.fromisoformat(str(item["publishedDate"]))
    except (KeyError, TypeError, ValueError):
        return False
    if published > today:
        return False

    url_date = affairs_news_date(str(item.get("sourceUrl", "")))
    if url_date and url_date != published:
        return False

    deadline_text = str(item.get("deadline", "")).strip()
    if deadline_text:
        try:
            deadline = date.fromisoformat(deadline_text)
        except ValueError:
            return False
        if deadline < published:
            return False
    return True


def affairs_news_score(item: dict[str, Any], profile: str, grade: str, today: date) -> float:
    if not affairs_news_timeline_is_valid(item, today):
        return -1000

    title = str(item.get("title", ""))
    source = str(item.get("sourceName", ""))
    audiences = item.get("audiences") or []
    if profile not in audiences:
        return -1000
    if profile == "undergraduate" and "研究生" in title:
        return -1000
    if profile == "graduate" and any(word in title for word in ("本科", "普本", "微专业")):
        return -1000

    source_scores = {
        "undergraduate": {"教务处": 48, "中国教育考试网·CET": 46, "学生工作处": 38, "图书馆": 30, "研究生院": -100},
        "graduate": {"研究生院": 52, "中国教育考试网·CET": 46, "教务处": 30, "图书馆": 28, "学生工作处": 26},
    }
    score = float(source_scores.get(profile, {}).get(source, 10))
    relevant_words = (
        "通知", "公告", "公示", "报名", "考试", "课程", "课表", "教材", "奖学金",
        "助学", "勤工", "图书", "借阅", "讲座", "毕业", "学位", "论文", "培养", "实习",
    )
    score += sum(4 for word in relevant_words if word in title)
    if any(
        word in title
        for word in (
            "党支部", "党建", "党总支", "成立大会", "工作会议", "教师", "采购",
            "获批", "调研", "典礼", "仪式", "消防培训", "共建",
        )
    ):
        score -= 80

    audience_year_match = re.search(r"(20\d{2})级", title)
    if audience_year_match and not grade.startswith(audience_year_match.group(1)):
        score -= 70

    admission_words = ("招生", "复试", "调剂", "拟录取", "初试", "新生")
    if any(word in title for word in admission_words):
        year_match = re.search(r"(20\d{2})级", title)
        if not year_match or not grade.startswith(year_match.group(1)):
            score -= 75

    try:
        published = date.fromisoformat(str(item["publishedDate"]))
        age_days = (today - published).days
        if age_days < -2 or age_days > 240:
            return -1000
        score += max(0, 90 - max(age_days, 0)) * 0.35
    except (KeyError, TypeError, ValueError):
        return -1000
    return score


def rank_affairs_news(profile: str, grade: str, live_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = date.today()
    fallback_by_url = {
        item["sourceUrl"]: dict(item, live=False)
        for item in AFFAIRS_NEWS_FALLBACK
        if profile in item.get("audiences", [])
    }
    merged_by_url = dict(fallback_by_url)
    for live_item in live_items:
        article_url = live_item["sourceUrl"]
        if article_url in fallback_by_url:
            merged_by_url[article_url] = {**live_item, **fallback_by_url[article_url], "live": True}
        else:
            merged_by_url[article_url] = live_item

    ranked: list[dict[str, Any]] = []
    level_label = "本科生" if profile == "undergraduate" else "研究生"
    for item in merged_by_url.values():
        score = affairs_news_score(item, profile, grade, today)
        if score < 40:
            continue
        published = date.fromisoformat(item["publishedDate"])
        age_days = max((today - published).days, 0)
        freshness = "7天内发布" if age_days <= 7 else "近30天发布" if age_days <= 30 else "近期发布"
        status_label = freshness
        deadline_text = str(item.get("deadline", "")).strip()
        if deadline_text:
            try:
                deadline = date.fromisoformat(deadline_text)
                remaining = (deadline - today).days
                if remaining < 0:
                    status_label = "已截止"
                elif remaining <= 7:
                    status_label = f"剩余{remaining}天"
                else:
                    status_label = f"截止 {deadline.strftime('%m-%d')}"
            except ValueError:
                pass
        ranked.append(
            {
                **item,
                "matchReason": f"匹配{level_label} · {item['sourceName']}",
                "freshness": freshness,
                "statusLabel": status_label,
                "sourceStatus": "官方内容已概括" if item.get("contentFetched") else "官网实时" if item.get("live") else "官方已核验",
                "score": round(score, 2),
            }
        )
    ranked.sort(key=lambda item: (item["publishedDate"], item["score"]), reverse=True)
    return ranked


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def is_mock_mode() -> bool:
    return os.getenv("MOCK_MODE", "1") == "1"


def model_label() -> str:
    if is_mock_mode():
        return "mock-campus-agent"
    return os.getenv("MODEL_NAME", "").strip() or "unconfigured-model"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
