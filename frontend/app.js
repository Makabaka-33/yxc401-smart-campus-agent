const assistantModes = {
  learning: {
    title: "学生助手",
    subtitle: "学习全过程支持 · 南审审计特色",
    logo: "学",
    apiMode: "audit",
    placeholder: "向学生助手提问，例如：根据审计课件生成复习计划",
    defaultPrompt: "审计风险模型、政府采购合规性和审计证据",
    greeting: "你好，我是学生助手",
  },
  teaching: {
    title: "教学助手",
    subtitle: "备课、出题、课堂活动与评价",
    logo: "教",
    apiMode: "teaching",
    placeholder: "向教学助手提问，例如：设计一节审计案例讨论课",
    defaultPrompt: "审计学基础课程教学设计",
    greeting: "你好，我是教学助手",
  },
  affairs: {
    title: "事务助手",
    subtitle: "身份适配 · 校园事务一站式办理",
    logo: "办",
    apiMode: "affairs",
    placeholder: "向事务助手提问，例如：奖学金申请流程是什么",
    defaultPrompt: "学生校园事务办理流程",
    greeting: "你好，我是事务助手",
  },
};

const presetPhrases = {
  learning: [
    {
      category: "课程学习",
      items: [
        ["生成复习计划", "根据我上传的课件，整理本周复习计划，并列出每天的学习任务和检测方式。"],
        ["解释知识点", "用大学生容易理解的语言解释这个知识点，并给出一个例题和常见误区。"],
        ["梳理章节大纲", "根据课程资料提取章节结构、核心概念、重点和难点。"],
      ],
    },
    {
      category: "审计专项",
      items: [
        ["分析审计案例", "按审计目标、风险、程序、证据和结论分析这个审计案例。"],
        ["比较三类审计", "比较政府审计、内部审计和社会审计的主体、目标、依据与报告对象。"],
        ["审计练习检测", "根据当前知识库生成 6 道审计练习题，附答案、解析和知识点。"],
      ],
    },
    {
      category: "资料处理",
      items: [
        ["总结课程资料", "总结我上传的课程资料，保留关键术语、结论和资料依据。"],
        ["生成思维导图", "把当前主题整理成层级清晰的思维导图，并附复习路径。"],
        ["制定论文阅读表", "根据论文内容整理研究问题、方法、数据、结论和局限。"],
      ],
    },
  ],
  teaching: [
    {
      category: "备课设计",
      items: [
        ["生成课程教案", "设计一节 45 分钟课程教案，包含目标、导入、活动、练习和时间分配。"],
        ["设计案例课堂", "围绕当前主题设计案例讨论课，给出案例、问题链和教师引导语。"],
        ["设计课堂活动", "设计三个由浅入深的课堂活动，并说明组织方式和预期产出。"],
      ],
    },
    {
      category: "评价与出题",
      items: [
        ["生成课程试题", "生成选择题、判断题、简答题和案例题，并附答案、解析与难度。"],
        ["制定评分量规", "为本次作业制定 Rubric，包含评价维度、等级描述和分值。"],
        ["分析学习表现", "根据学生作业表现归纳共性问题，并提出分层教学建议。"],
      ],
    },
    {
      category: "教学改进",
      items: [
        ["生成教学反思", "根据本节课目标和课堂表现生成教学反思与下次改进清单。"],
        ["课程资料大纲", "把课程材料整理成教师备课大纲和学生预习清单。"],
        ["设计课后任务", "设计能够检验课堂目标的课后任务，并给出提交要求。"],
      ],
    },
  ],
  affairs: [
    {
      category: "校园办事",
      items: [
        ["查询办事流程", "说明这项校园事务的办理入口、材料、步骤、时间和官方确认渠道。"],
        ["开具证明", "整理在校证明或成绩证明的申请流程、所需材料和注意事项。"],
        ["校园卡服务", "说明校园卡挂失、补办、充值或异常处理的办理步骤。"],
      ],
    },
    {
      category: "学业服务",
      items: [
        ["奖学金申请", "整理奖学金申请条件、材料、时间节点和常见退回原因。"],
        ["选课与退课", "说明选课、补选、退课的流程和需要关注的时间节点。"],
        ["考试安排", "帮助我整理考试时间、地点、携带材料和复习安排。"],
      ],
    },
    {
      category: "学生生活",
      items: [
        ["宿舍事务", "说明宿舍报修、调宿或住宿证明的办理入口和步骤。"],
        ["医保报销", "整理学生医保报销所需材料、办理流程和注意事项。"],
        ["活动与场地", "说明校园活动申请或场地预约的流程、材料和审批节点。"],
      ],
    },
  ],
};

const homePage = document.querySelector("#homePage");
const assistantPage = document.querySelector("#assistantPage");
const chatStage = document.querySelector("#chatStage");
const knowledgeWorkspace = document.querySelector("#knowledgeWorkspace");
const backHomeBtn = document.querySelector("#backHomeBtn");
const backToChatBtn = document.querySelector("#backToChatBtn");
const modeTitle = document.querySelector("#modeTitle");
const modeSubtitle = document.querySelector("#modeSubtitle");
const assistantLogo = document.querySelector("#assistantLogo");
const welcomeTitle = document.querySelector("#welcomeTitle");
const assistantGreeting = document.querySelector(".assistant-greeting");
const statusBadge = document.querySelector("#statusBadge");
const homeStatusBadge = document.querySelector("#homeStatusBadge");
const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const sendBtn = document.querySelector("#sendBtn");
const fileInput = document.querySelector("#fileInput");
const translateFileInput = document.querySelector("#translateFileInput");
const timetableFileInput = document.querySelector("#timetableFileInput");
const documentList = document.querySelector("#documentList");
const knowledgeDocumentList = document.querySelector("#knowledgeDocumentList");
const knowledgeArtifactList = document.querySelector("#knowledgeArtifactList");
const timetableBody = document.querySelector("#timetableBody");
const knowledgeDocCount = document.querySelector("#knowledgeDocCount");
const knowledgeArtifactCount = document.querySelector("#knowledgeArtifactCount");
const knowledgeCourseCount = document.querySelector("#knowledgeCourseCount");
const sessionList = document.querySelector("#sessionList");
const apiStatus = document.querySelector("#apiStatus");
const callList = document.querySelector("#callList");
const newSessionBtn = document.querySelector("#newSessionBtn");
const uploadTriggerBtn = document.querySelector("#uploadTriggerBtn");
const composerToolWrap = document.querySelector("#composerToolWrap");
const composerToolMenu = document.querySelector("#composerToolMenu");
const webSearchState = document.querySelector("#webSearchState");
const deepResearchBtn = document.querySelector("#deepResearchBtn");
const quickToolStrip = document.querySelector(".quick-tool-strip");
const knowledgeFeatureEntry = document.querySelector(".knowledge-feature-entry");
const utilityPanel = document.querySelector(".utility-panel");
const featureWorkbench = document.querySelector("#featureWorkbench");
const activeToolChip = document.querySelector("#activeToolChip");
const activeToolSymbol = document.querySelector("#activeToolSymbol");
const activeToolName = document.querySelector("#activeToolName");
const exitFeatureBtn = document.querySelector("#exitFeatureBtn");
const translateWorkbench = document.querySelector("#translateWorkbench");
const mindmapWorkbench = document.querySelector("#mindmapWorkbench");
const instantSourceLang = document.querySelector("#instantSourceLang");
const instantTargetLang = document.querySelector("#instantTargetLang");
const swapTranslateLangBtn = document.querySelector("#swapTranslateLangBtn");
const instantSourceText = document.querySelector("#instantSourceText");
const instantTargetText = document.querySelector("#instantTargetText");
const instantTranslateBtn = document.querySelector("#instantTranslateBtn");
const documentTranslateUploadBtn = document.querySelector("#documentTranslateUploadBtn");
const documentTranslateResult = document.querySelector("#documentTranslateResult");
const documentSummaryBtn = document.querySelector("#documentSummaryBtn");
const documentArchiveBtn = document.querySelector("#documentArchiveBtn");
const documentSummaryResult = document.querySelector("#documentSummaryResult");
const mindmapTopicInput = document.querySelector("#mindmapTopicInput");
const mindmapGenerateBtn = document.querySelector("#mindmapGenerateBtn");
const mindmapBranchInput = document.querySelector("#mindmapBranchInput");
const mindmapAddBranchBtn = document.querySelector("#mindmapAddBranchBtn");
const mindmapClearBtn = document.querySelector("#mindmapClearBtn");
const mindmapArchiveBtn = document.querySelector("#mindmapArchiveBtn");
const mindmapBranchList = document.querySelector("#mindmapBranchList");
const mindmapCanvas = document.querySelector("#mindmapCanvas");
const knowledgeUploadBtn = document.querySelector("#knowledgeUploadBtn");
const inlineUploadBtn = document.querySelector("#inlineUploadBtn");
const timetableImportBtn = document.querySelector("#timetableImportBtn");
const inlineTimetableBtn = document.querySelector("#inlineTimetableBtn");
const createOutlineBtn = document.querySelector("#createOutlineBtn");
const loginBtn = document.querySelector("#loginBtn");
const homeLoginBtn = document.querySelector("#homeLoginBtn");
const loginModal = document.querySelector("#loginModal");
const loginCloseBtn = document.querySelector("#loginCloseBtn");
const loginForm = document.querySelector("#loginForm");
const loginUserInput = document.querySelector("#loginUserInput");
const loginPassInput = document.querySelector("#loginPassInput");
const loginStatus = document.querySelector("#loginStatus");
const authPortalLink = document.querySelector("#authPortalLink");
const logoutBtn = document.querySelector("#logoutBtn");
const assetViewerModal = document.querySelector("#assetViewerModal");
const assetViewerCloseBtn = document.querySelector("#assetViewerCloseBtn");
const assetViewerTitle = document.querySelector("#assetViewerTitle");
const assetViewerBody = document.querySelector("#assetViewerBody");
const assetDownloadLink = document.querySelector("#assetDownloadLink");
const commonPhraseModal = document.querySelector("#commonPhraseModal");
const commonPhraseCloseBtn = document.querySelector("#commonPhraseCloseBtn");
const commonPhraseSearch = document.querySelector("#commonPhraseSearch");
const commonPhraseContent = document.querySelector("#commonPhraseContent");
const addCommonPhraseBtn = document.querySelector("#addCommonPhraseBtn");
const affairsDashboard = document.querySelector("#affairsDashboard");
const affairsProfileSwitch = document.querySelector("#affairsProfileSwitch");
const affairsProfileSelect = document.querySelector("#affairsProfileSelect");
const affairsProfileAvatar = document.querySelector("#affairsProfileAvatar");
const affairsProfileName = document.querySelector("#affairsProfileName");
const affairsProfileMeta = document.querySelector("#affairsProfileMeta");
const affairsGreetingTitle = document.querySelector("#affairsGreetingTitle");
const affairsGreetingText = document.querySelector("#affairsGreetingText");
const affairsProfileFacts = document.querySelector("#affairsProfileFacts");
const affairsSearchForm = document.querySelector("#affairsSearchForm");
const affairsSearchInput = document.querySelector("#affairsSearchInput");
const affairsQuickQuestions = document.querySelector("#affairsQuickQuestions");
const affairsAgentResult = document.querySelector("#affairsAgentResult");
const affairsAgentResultBody = document.querySelector("#affairsAgentResultBody");
const affairsAgentResultClose = document.querySelector("#affairsAgentResultClose");
const affairsTaskCount = document.querySelector("#affairsTaskCount");
const affairsTaskGrid = document.querySelector("#affairsTaskGrid");
const affairsPriorityGrid = document.querySelector("#affairsPriorityGrid");
const affairsServiceGrid = document.querySelector("#affairsServiceGrid");
const affairsNoticeList = document.querySelector("#affairsNoticeList");
const affairsNoticeMeta = document.querySelector("#affairsNoticeMeta");
const affairsNewsRefreshBtn = document.querySelector("#affairsNewsRefreshBtn");
const affairsRecentList = document.querySelector("#affairsRecentList");
const affairsDataUpdatedAt = document.querySelector("#affairsDataUpdatedAt");
const affairsDetailModal = document.querySelector("#affairsDetailModal");
const affairsDetailCloseBtn = document.querySelector("#affairsDetailCloseBtn");
const affairsDetailBody = document.querySelector("#affairsDetailBody");
const affairsSidebar = document.querySelector("#affairsSidebar");
const affairsSettingsBtn = document.querySelector("#affairsSettingsBtn");
const affairsNotificationBtn = document.querySelector("#affairsNotificationBtn");

let currentMode = "learning";
let currentSessionId = null;
let currentAssistant = null;
let lastPrompt = "";
let authState = JSON.parse(localStorage.getItem("mock_auth_state") || "null");
let latestDocuments = [];
let latestArtifacts = [];
let deepResearchEnabled = false;
let webSearchEnabled = false;
let activeFeature = null;
let translateFileContext = "chat";
let lastDocumentTranslation = null;
let lastDocumentArchivePayload = null;
let mindmapBranches = [];
let lastMindmapArtifact = null;
let currentAffairsProfileId = localStorage.getItem("affairs_profile") || "undergraduate";
let affairsTasks = [];
let affairsNewsRequestId = 0;

document.querySelectorAll("[data-open-mode]").forEach((button) => {
  button.addEventListener("click", () => openAssistant(button.dataset.openMode));
});

document.querySelectorAll("[data-feature]").forEach((button) => {
  button.addEventListener("click", () => runFeature(button.dataset.feature));
});

function showHomePage() {
  assistantPage.hidden = true;
  homePage.hidden = false;
  assistantPage.classList.remove("affairs-mode");
  knowledgeWorkspace.hidden = true;
  chatStage.hidden = false;
  affairsDashboard.hidden = true;
  affairsProfileSwitch.hidden = true;
  affairsSidebar.hidden = true;
  affairsNotificationBtn.hidden = true;
}

backHomeBtn.addEventListener("click", showHomePage);

affairsSidebar.addEventListener("click", (event) => {
  const button = event.target.closest("[data-affairs-nav]");
  if (!button) return;
  const target = button.dataset.affairsNav;
  if (target === "home") showHomePage();
  else openAssistant(target);
});

affairsSettingsBtn.addEventListener("click", () => {
  loginModal.hidden = false;
  loginUserInput.focus();
});

affairsNotificationBtn.addEventListener("click", () => {
  document.querySelector("#affairsNoticesTitle")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

affairsNewsRefreshBtn.addEventListener("click", () => loadAffairsNotices(true));

affairsProfileSelect.addEventListener("change", () => {
  currentAffairsProfileId = affairsProfileSelect.value;
  localStorage.setItem("affairs_profile", currentAffairsProfileId);
  affairsAgentResult.hidden = true;
  renderAffairsDashboard();
});

affairsSearchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await answerAffairsQuestion(affairsSearchInput.value);
});

affairsDashboard.addEventListener("click", handleAffairsDashboardClick);
affairsAgentResultClose.addEventListener("click", () => {
  affairsAgentResult.hidden = true;
});
affairsDetailCloseBtn.addEventListener("click", closeAffairsDetail);
affairsDetailModal.addEventListener("click", (event) => {
  if (event.target === affairsDetailModal) closeAffairsDetail();
});
affairsDetailModal.addEventListener("change", (event) => {
  const checkbox = event.target.closest("[data-affairs-material]");
  if (!checkbox) return;
  const task = affairsTasks.find((item) => item.id === checkbox.dataset.taskId);
  const material = task?.materials[Number(checkbox.dataset.affairsMaterial)];
  if (!task || !material) return;
  material.checked = checkbox.checked;
  saveAffairsTaskState();
  renderAffairsTasks();
  openAffairsTaskDetail(task.id);
});

backToChatBtn.addEventListener("click", showChatWorkspace);
uploadTriggerBtn.addEventListener("click", (event) => {
  event.stopPropagation();
  composerToolWrap.classList.toggle("open");
});

composerToolMenu.addEventListener("click", (event) => {
  const button = event.target.closest("[data-composer-tool]");
  if (!button) return;
  const tool = button.dataset.composerTool;
  if (tool === "files") {
    fileInput.click();
    closeComposerToolMenu();
  }
  if (tool === "phrases") {
    openCommonPhraseModal();
    closeComposerToolMenu();
  }
  if (tool === "web") {
    webSearchEnabled = !webSearchEnabled;
    webSearchState.textContent = webSearchEnabled ? "已开启" : "未开启";
    button.classList.toggle("active", webSearchEnabled);
  }
});

document.addEventListener("click", (event) => {
  if (!composerToolWrap.contains(event.target)) closeComposerToolMenu();
});

deepResearchBtn.addEventListener("click", () => {
  deepResearchEnabled = !deepResearchEnabled;
  deepResearchBtn.classList.toggle("active", deepResearchEnabled);
  deepResearchBtn.setAttribute("aria-pressed", String(deepResearchEnabled));
});

commonPhraseCloseBtn.addEventListener("click", closeCommonPhraseModal);
commonPhraseModal.addEventListener("click", (event) => {
  if (event.target === commonPhraseModal) closeCommonPhraseModal();
});
commonPhraseSearch.addEventListener("input", () => renderCommonPhrases(commonPhraseSearch.value));
addCommonPhraseBtn.addEventListener("click", addCustomPhrase);

[knowledgeUploadBtn, inlineUploadBtn].forEach((button) => {
  button.addEventListener("click", () => fileInput.click());
});
[timetableImportBtn, inlineTimetableBtn].forEach((button) => {
  button.addEventListener("click", () => timetableFileInput.click());
});

document.querySelectorAll("[data-knowledge-tab]").forEach((button) => {
  button.addEventListener("click", () => selectKnowledgeTab(button.dataset.knowledgeTab));
});

assetViewerCloseBtn.addEventListener("click", closeAssetViewer);
assetViewerModal.addEventListener("click", (event) => {
  if (event.target === assetViewerModal) closeAssetViewer();
});

createOutlineBtn.addEventListener("click", createOutlineFromKnowledge);

newSessionBtn.addEventListener("click", () => {
  currentSessionId = null;
  messages.innerHTML = "";
  input.value = "";
  input.focus();
});

exitFeatureBtn.addEventListener("click", exitFeatureWorkbench);

document.querySelectorAll("[data-translate-tab]").forEach((button) => {
  button.addEventListener("click", () => selectTranslateTab(button.dataset.translateTab));
});

swapTranslateLangBtn.addEventListener("click", () => {
  const source = instantSourceLang.value;
  instantSourceLang.value = instantTargetLang.value === "英语" ? "英语" : instantTargetLang.value;
  instantTargetLang.value = source === "auto" ? "中文" : source;
});

instantTranslateBtn.addEventListener("click", translateInstantText);
documentTranslateUploadBtn.addEventListener("click", () => {
  translateFileContext = "workbench";
  translateFileInput.click();
});
documentSummaryBtn.addEventListener("click", summarizeDocumentTranslation);
documentArchiveBtn.addEventListener("click", archiveCurrentDocumentTranslation);
mindmapGenerateBtn.addEventListener("click", generateMindmapInWorkbench);
mindmapAddBranchBtn.addEventListener("click", addManualMindmapBranch);
mindmapClearBtn.addEventListener("click", resetMindmapCanvas);
mindmapArchiveBtn.addEventListener("click", archiveCurrentMindmap);

[loginBtn, homeLoginBtn].forEach((button) => {
  button.addEventListener("click", () => {
    loginModal.hidden = false;
    loginUserInput.focus();
  });
});

loginCloseBtn.addEventListener("click", () => {
  loginModal.hidden = true;
});

loginModal.addEventListener("click", (event) => {
  if (event.target === loginModal) loginModal.hidden = true;
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = loginUserInput.value.trim();
  const password = loginPassInput.value.trim();
  if (!username || !password) {
    loginStatus.textContent = "请输入学号/工号和虚拟密码。";
    return;
  }
  const response = await fetch("/api/auth/mock-login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    loginStatus.textContent = `虚拟登录失败：HTTP ${response.status}`;
    return;
  }
  authState = await response.json();
  localStorage.setItem("mock_auth_state", JSON.stringify(authState));
  updateAuthUi();
  loginModal.hidden = true;
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST" }).catch(() => {});
  authState = null;
  localStorage.removeItem("mock_auth_state");
  updateAuthUi();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  lastPrompt = message;
  input.value = "";
  addMessage("user", message);
  currentAssistant = addMessage("assistant", "", { typing: true });
  setLoading(true);

  try {
    await streamChat(message);
  } catch (error) {
    updateAssistant(currentAssistant, `请求失败：${error.message}`, []);
  } finally {
    setLoading(false);
    currentAssistant?.classList.remove("typing");
    currentAssistant = null;
    await refreshAll();
  }
});

fileInput.addEventListener("change", async () => {
  const files = Array.from(fileInput.files || []);
  if (!files.length) return;
  knowledgeUploadBtn.disabled = true;
  inlineUploadBtn.disabled = true;
  for (const file of files) {
    const body = new FormData();
    body.append("file", file);
    body.append("scope", "knowledge");
    const response = await fetch("/api/upload", { method: "POST", body });
    if (response.ok) {
      const data = await response.json();
      if (!knowledgeWorkspace.hidden) {
        knowledgeUploadBtn.textContent = `已上传 ${data.source_name}`;
      } else {
        addMessage("assistant", `已保存资料：${data.source_name}，建立 ${data.chunk_count} 个检索片段。`);
      }
    } else {
      window.alert(`上传失败：${file.name}\n${await response.text()}`);
    }
  }
  fileInput.value = "";
  knowledgeUploadBtn.disabled = false;
  inlineUploadBtn.disabled = false;
  knowledgeUploadBtn.textContent = "上传学习资料";
  await refreshAll();
});

timetableFileInput.addEventListener("change", async () => {
  const file = timetableFileInput.files?.[0];
  if (!file) return;
  timetableImportBtn.disabled = true;
  inlineTimetableBtn.disabled = true;
  const body = new FormData();
  body.append("file", file);
  try {
    const response = await fetch("/api/timetable/import", { method: "POST", body });
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    await refreshAll();
    selectKnowledgeTab("timetable");
    window.alert(`已导入 ${data.imported_count} 条课程记录。`);
  } catch (error) {
    window.alert(`课程表导入失败：${error.message}`);
  } finally {
    timetableFileInput.value = "";
    timetableImportBtn.disabled = false;
    inlineTimetableBtn.disabled = false;
  }
});

translateFileInput.addEventListener("change", async () => {
  const file = translateFileInput.files?.[0];
  if (!file) return;
  if (translateFileContext === "workbench") {
    await translateDocumentForWorkbench(file);
    translateFileInput.value = "";
    translateFileContext = "chat";
    return;
  }
  const pending = addMessage("assistant", "正在翻译并导出 DOCX...");
  const body = new FormData();
  body.append("file", file);
  body.append("target_language", "中文");
  try {
    const response = await fetch("/api/translate/file", { method: "POST", body });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    updateAssistant(
      pending,
      `# 翻译完成\n\n源文件：${data.source_name}\n\n[下载中文译文](${data.download_url})\n\n## 预览\n${data.translation_preview}`,
      []
    );
  } catch (error) {
    updateAssistant(pending, `翻译失败：${error.message}`, []);
  } finally {
    translateFileInput.value = "";
    translateFileContext = "chat";
  }
});

function openAssistant(mode) {
  currentMode = mode;
  const config = assistantModes[currentMode];
  deepResearchEnabled = false;
  webSearchEnabled = false;
  deepResearchBtn.classList.remove("active");
  deepResearchBtn.setAttribute("aria-pressed", "false");
  webSearchState.textContent = "未开启";
  document.querySelector('[data-composer-tool="web"]')?.classList.remove("active");
  homePage.hidden = true;
  assistantPage.hidden = false;
  knowledgeWorkspace.hidden = true;
  const isAffairs = currentMode === "affairs";
  assistantPage.classList.toggle("affairs-mode", isAffairs);
  chatStage.hidden = isAffairs;
  affairsDashboard.hidden = !isAffairs;
  affairsProfileSwitch.hidden = !isAffairs;
  affairsSidebar.hidden = !isAffairs;
  affairsNotificationBtn.hidden = !isAffairs;
  modeTitle.textContent = config.title;
  modeSubtitle.textContent = config.subtitle;
  assistantLogo.textContent = config.logo;
  welcomeTitle.textContent = config.greeting;
  input.placeholder = config.placeholder;
  document.querySelectorAll(".learning-only").forEach((item) => {
    item.hidden = currentMode !== "learning";
  });
  messages.innerHTML = "";
  currentSessionId = null;
  exitFeatureWorkbench();
  if (isAffairs) {
    renderAffairsDashboard();
    affairsSearchInput.focus();
  } else {
    input.focus();
  }
  refreshAll().catch(() => {});
}

async function runFeature(feature) {
  if (feature === "knowledge") {
    openKnowledgeWorkspace();
    return;
  }
  if (feature === "translate") {
    openFeatureWorkbench("translate");
    return;
  }
  if (feature === "mindmap") {
    openFeatureWorkbench("mindmap");
    return;
  }
  if (feature === "quiz") {
    await runArtifact("/api/artifacts/quiz", "正在生成练习测验...", { question_count: 6 });
  }
}

function openFeatureWorkbench(feature) {
  activeFeature = feature;
  const toolMeta = {
    translate: { name: "翻译", symbol: "译" },
    mindmap: { name: "思维导图", symbol: "图" },
  }[feature];
  if (!toolMeta) return;

  activeToolName.textContent = toolMeta.name;
  activeToolSymbol.textContent = toolMeta.symbol;
  activeToolChip.dataset.feature = feature;
  featureWorkbench.hidden = false;
  translateWorkbench.hidden = feature !== "translate";
  mindmapWorkbench.hidden = feature !== "mindmap";
  assistantGreeting.hidden = true;
  messages.hidden = true;
  quickToolStrip.hidden = true;
  knowledgeFeatureEntry.hidden = true;
  utilityPanel.hidden = true;

  document.querySelectorAll(".quick-tool").forEach((button) => {
    button.classList.toggle("active", button.dataset.feature === feature);
  });

  if (feature === "translate") {
    selectTranslateTab("instant");
    const draft = input.value.trim();
    if (draft && !instantSourceText.value.trim()) instantSourceText.value = draft;
    setTimeout(() => instantSourceText.focus(), 0);
  }

  if (feature === "mindmap") {
    const config = assistantModes[currentMode];
    if (!mindmapTopicInput.value.trim()) {
      mindmapTopicInput.value = lastPrompt || input.value.trim() || config.defaultPrompt;
    }
    if (!mindmapBranches.length) {
      mindmapBranches = ["核心概念", "知识结构", "复习路径", "易错点"];
    }
    renderMindmapCanvas();
    setTimeout(() => mindmapTopicInput.focus(), 0);
  }
}

function exitFeatureWorkbench() {
  activeFeature = null;
  featureWorkbench.hidden = true;
  translateWorkbench.hidden = true;
  mindmapWorkbench.hidden = true;
  assistantGreeting.hidden = false;
  messages.hidden = false;
  quickToolStrip.hidden = false;
  knowledgeFeatureEntry.hidden = false;
  utilityPanel.hidden = false;
  document.querySelectorAll(".quick-tool").forEach((button) => {
    button.classList.remove("active");
  });
}

function selectTranslateTab(tab) {
  document.querySelectorAll("[data-translate-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.translateTab === tab);
  });
  document.querySelectorAll("[data-translate-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.translatePanel !== tab;
  });
}

async function translateInstantText() {
  const sourceText = instantSourceText.value.trim();
  if (!sourceText) {
    instantTargetText.textContent = "请先输入需要翻译的内容。";
    return;
  }
  instantTranslateBtn.disabled = true;
  instantTranslateBtn.textContent = "翻译中...";
  instantTargetText.innerHTML = '<div class="viewer-loading">正在翻译...</div>';
  try {
    const response = await fetch("/api/translate/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_text: sourceText,
        target_language: instantTargetLang.value,
      }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    instantTargetText.innerHTML = renderMarkdown(data.translation || "");
  } catch (error) {
    instantTargetText.textContent = `翻译失败：${error.message}`;
  } finally {
    instantTranslateBtn.disabled = false;
    instantTranslateBtn.textContent = "开始翻译";
  }
}

async function translateDocumentForWorkbench(file) {
  documentTranslateUploadBtn.disabled = true;
  documentSummaryBtn.disabled = true;
  documentArchiveBtn.disabled = true;
  documentArchiveBtn.textContent = "加入知识库";
  documentSummaryBtn.textContent = "生成双语要点总结";
  documentSummaryResult.innerHTML = "";
  documentTranslateResult.innerHTML = '<div class="viewer-loading">正在翻译并导出 DOCX...</div>';
  const body = new FormData();
  body.append("file", file);
  body.append("target_language", "中文");
  try {
    const response = await fetch("/api/translate/file", { method: "POST", body });
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    lastDocumentTranslation = data;
    lastDocumentArchivePayload = {
      title: `${data.source_name} 中文译文`,
      content: `# ${data.source_name} 中文译文\n\n${data.translation_preview || ""}`,
    };
    documentTranslateResult.innerHTML = `
      <div class="translation-file-result">
        <div>
          <strong>${escapeHtml(data.source_name)}</strong>
          <span>已生成中文 DOCX 译文，可继续总结或加入知识库。</span>
        </div>
        <a class="primary-btn" href="${data.download_url}" target="_blank" rel="noreferrer">下载译文</a>
      </div>
      <div class="artifact-preview markdown-body">${renderMarkdown(data.translation_preview || "")}</div>
    `;
    documentSummaryBtn.disabled = false;
    documentArchiveBtn.disabled = false;
  } catch (error) {
    documentTranslateResult.innerHTML = `<div class="empty-state">文档翻译失败：${escapeHtml(error.message)}</div>`;
  } finally {
    documentTranslateUploadBtn.disabled = false;
  }
}

async function summarizeDocumentTranslation() {
  if (!lastDocumentTranslation?.translation_preview) return;
  documentSummaryBtn.disabled = true;
  documentSummaryBtn.textContent = "总结中...";
  documentSummaryResult.innerHTML = '<div class="viewer-loading">正在生成双语要点总结...</div>';
  try {
    const response = await fetch("/api/translate/summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_text: lastDocumentTranslation.translation_preview,
        target_language: "中英双语",
      }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    documentSummaryResult.innerHTML = `<div class="artifact-preview markdown-body">${renderMarkdown(data.summary || "")}</div>`;
    lastDocumentArchivePayload = {
      title: `${lastDocumentTranslation.source_name} 双语总结`,
      content: `# ${lastDocumentTranslation.source_name} 双语总结\n\n${data.summary || ""}\n\n## 译文预览\n${lastDocumentTranslation.translation_preview}`,
    };
    documentArchiveBtn.disabled = false;
  } catch (error) {
    documentSummaryResult.innerHTML = `<div class="empty-state">总结失败：${escapeHtml(error.message)}</div>`;
  } finally {
    documentSummaryBtn.disabled = false;
    documentSummaryBtn.textContent = "生成双语要点总结";
  }
}

async function archiveCurrentDocumentTranslation() {
  if (!lastDocumentArchivePayload) return;
  documentArchiveBtn.disabled = true;
  documentArchiveBtn.textContent = "保存中...";
  try {
    await uploadGeneratedMarkdown(lastDocumentArchivePayload.title, lastDocumentArchivePayload.content);
    documentArchiveBtn.textContent = "已加入知识库";
    await refreshAll();
  } catch (error) {
    documentArchiveBtn.disabled = false;
    documentArchiveBtn.textContent = "重试加入知识库";
  }
}

async function generateMindmapInWorkbench() {
  const config = assistantModes[currentMode];
  const topic = mindmapTopicInput.value.trim() || lastPrompt || config.defaultPrompt;
  mindmapTopicInput.value = topic;
  mindmapGenerateBtn.disabled = true;
  mindmapGenerateBtn.textContent = "生成中...";
  mindmapArchiveBtn.textContent = "加入知识库";
  try {
    const response = await fetch("/api/artifacts/mindmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: config.apiMode, prompt: topic }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    lastMindmapArtifact = data;
    mindmapBranches = extractMindmapBranches(data.content);
    if (!mindmapBranches.length) {
      mindmapBranches = ["概念定义", "关键流程", "证据资料", "复习检测"];
    }
    renderMindmapCanvas();
    mindmapArchiveBtn.disabled = false;
    await loadArtifacts();
  } catch (error) {
    window.alert(`思维导图生成失败：${error.message}`);
  } finally {
    mindmapGenerateBtn.disabled = false;
    mindmapGenerateBtn.textContent = "AI 生成思维导图";
  }
}

function addManualMindmapBranch() {
  const branch = mindmapBranchInput.value.trim();
  if (!branch) return;
  mindmapBranches.push(branch);
  mindmapBranchInput.value = "";
  lastMindmapArtifact = null;
  mindmapArchiveBtn.disabled = false;
  mindmapArchiveBtn.textContent = "加入知识库";
  renderMindmapCanvas();
  mindmapBranchInput.focus();
}

function resetMindmapCanvas() {
  mindmapBranches = [];
  lastMindmapArtifact = null;
  mindmapArchiveBtn.disabled = true;
  mindmapArchiveBtn.textContent = "加入知识库";
  renderMindmapCanvas();
}

async function archiveCurrentMindmap() {
  mindmapArchiveBtn.disabled = true;
  mindmapArchiveBtn.textContent = "保存中...";
  try {
    if (lastMindmapArtifact?.artifact_id) {
      await archiveArtifact(lastMindmapArtifact.artifact_id);
    } else {
      const topic = mindmapTopicInput.value.trim() || "手绘思维导图";
      const content = `# ${topic}\n\n${mindmapBranches.map((branch) => `- ${branch}`).join("\n")}`;
      await uploadGeneratedMarkdown(`${topic} 思维导图`, content);
    }
    mindmapArchiveBtn.textContent = "已加入知识库";
    await refreshAll();
  } catch (error) {
    mindmapArchiveBtn.disabled = false;
    mindmapArchiveBtn.textContent = "重试加入知识库";
  }
}

function extractMindmapBranches(content = "") {
  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const branches = [];
  for (const line of lines) {
    const cleaned = line
      .replace(/^[-*]\s+/, "")
      .replace(/^#{1,4}\s+/, "")
      .replace(/^[\w\s-]*\)\s*/, "")
      .replace(/^root\(.+\)$/i, "")
      .replace(/^mindmap$/i, "")
      .trim();
    if (!cleaned || cleaned.includes("参考资料") || cleaned.includes("Mermaid")) continue;
    if (cleaned.length > 3 && !branches.includes(cleaned)) branches.push(cleaned.slice(0, 34));
    if (branches.length >= 8) break;
  }
  return branches;
}

function renderMindmapCanvas() {
  const topic = mindmapTopicInput.value.trim() || "课程思维导图";
  mindmapCanvas.innerHTML = "";
  const svgNS = "http://www.w3.org/2000/svg";
  const root = createMindmapNode(svgNS, 70, 245, 230, 70, topic, "root");
  mindmapCanvas.appendChild(root);

  if (!mindmapBranches.length) {
    const hint = document.createElementNS(svgNS, "text");
    hint.setAttribute("x", "430");
    hint.setAttribute("y", "284");
    hint.setAttribute("class", "mindmap-hint");
    hint.textContent = "点击 AI 生成，或在左侧手动添加节点";
    mindmapCanvas.appendChild(hint);
    renderMindmapBranchList();
    return;
  }

  const startY = Math.max(78, 280 - (mindmapBranches.length - 1) * 34);
  mindmapBranches.forEach((branch, index) => {
    const y = startY + index * 68;
    const path = document.createElementNS(svgNS, "path");
    path.setAttribute("d", `M 300 ${280} C 360 ${280}, 360 ${y + 30}, 430 ${y + 30}`);
    path.setAttribute("class", "mindmap-link");
    mindmapCanvas.appendChild(path);
    mindmapCanvas.appendChild(createMindmapNode(svgNS, 430, y, 300, 58, branch, "branch"));
  });
  renderMindmapBranchList();
}

function createMindmapNode(svgNS, x, y, width, height, text, type) {
  const group = document.createElementNS(svgNS, "g");
  group.setAttribute("class", `mindmap-node ${type}`);
  const rect = document.createElementNS(svgNS, "rect");
  rect.setAttribute("x", String(x));
  rect.setAttribute("y", String(y));
  rect.setAttribute("width", String(width));
  rect.setAttribute("height", String(height));
  rect.setAttribute("rx", "10");
  group.appendChild(rect);
  const label = document.createElementNS(svgNS, "text");
  label.setAttribute("x", String(x + 18));
  label.setAttribute("y", String(y + height / 2 + 6));
  label.textContent = text.length > 22 ? `${text.slice(0, 22)}...` : text;
  group.appendChild(label);
  return group;
}

function renderMindmapBranchList() {
  mindmapBranchList.innerHTML = mindmapBranches.length
    ? mindmapBranches
        .map(
          (branch, index) => `
            <button class="mindmap-branch-pill" type="button" data-remove-branch="${index}">
              <span>${escapeHtml(branch)}</span><strong>×</strong>
            </button>
          `
        )
        .join("")
    : '<div class="empty-state">画布还没有节点。</div>';
  mindmapBranchList.querySelectorAll("[data-remove-branch]").forEach((button) => {
    button.addEventListener("click", () => {
      mindmapBranches.splice(Number(button.dataset.removeBranch), 1);
      lastMindmapArtifact = null;
      renderMindmapCanvas();
    });
  });
}

async function uploadGeneratedMarkdown(title, content) {
  const safeTitle = title.replace(/[\\/:*?"<>|]+/g, "-").slice(0, 80) || "生成内容";
  const file = new File([content], `${safeTitle}.md`, { type: "text/markdown" });
  const body = new FormData();
  body.append("file", file);
  body.append("scope", "generated");
  const response = await fetch("/api/upload", { method: "POST", body });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function closeComposerToolMenu() {
  composerToolWrap.classList.remove("open");
  uploadTriggerBtn.blur();
}

function openCommonPhraseModal() {
  commonPhraseSearch.value = "";
  renderCommonPhrases();
  commonPhraseModal.hidden = false;
  commonPhraseSearch.focus();
}

function closeCommonPhraseModal() {
  commonPhraseModal.hidden = true;
}

function renderCommonPhrases(query = "") {
  const normalized = query.trim().toLowerCase();
  const groups = getCommonPhraseGroups();
  commonPhraseContent.innerHTML = groups
    .map((group) => {
      const items = group.items.filter(([title, content]) => {
        return !normalized || `${title} ${content}`.toLowerCase().includes(normalized);
      });
      if (!items.length) return "";
      return `
        <section class="phrase-group">
          <h3>${escapeHtml(group.category)}</h3>
          <div class="phrase-list">
            ${items
              .map(
                ([title, content]) => `
                <button class="phrase-item" type="button" data-phrase="${escapeHtml(content)}">
                  <strong>${escapeHtml(title)}</strong>
                  <span>${escapeHtml(content)}</span>
                </button>
              `
              )
              .join("")}
          </div>
        </section>
      `;
    })
    .join("");
  if (!commonPhraseContent.innerHTML.trim()) {
    commonPhraseContent.innerHTML = '<div class="empty-state">没有匹配的常用语。</div>';
  }
  commonPhraseContent.querySelectorAll("[data-phrase]").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.phrase;
      closeCommonPhraseModal();
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    });
  });
}

function getCommonPhraseGroups() {
  const custom = JSON.parse(localStorage.getItem(`custom_phrases_${currentMode}`) || "[]");
  const groups = presetPhrases[currentMode].map((group) => ({
    category: group.category,
    items: [...group.items],
  }));
  if (custom.length) {
    groups.push({ category: "我的常用语", items: custom });
  }
  return groups;
}

function addCustomPhrase() {
  const content = window.prompt("输入要保存的常用语");
  if (!content?.trim()) return;
  const key = `custom_phrases_${currentMode}`;
  const custom = JSON.parse(localStorage.getItem(key) || "[]");
  custom.push([content.trim().slice(0, 16), content.trim()]);
  localStorage.setItem(key, JSON.stringify(custom));
  renderCommonPhrases(commonPhraseSearch.value);
}

async function translateCurrentText(sourceText) {
  input.value = "";
  addMessage("user", sourceText);
  const pending = addMessage("assistant", "正在翻译文本...");
  try {
    const response = await fetch("/api/translate/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_text: sourceText, target_language: "中文" }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    updateAssistant(pending, data.translation, data.references || []);
  } catch (error) {
    updateAssistant(pending, `翻译失败：${error.message}`, []);
  }
}

async function runArtifact(endpoint, pendingText, extra = {}) {
  const config = assistantModes[currentMode];
  const prompt = lastPrompt || input.value.trim() || config.defaultPrompt;
  const pending = addMessage("assistant", pendingText);
  const payload = {
    mode: config.apiMode,
    prompt,
    ...extra,
  };
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    updateAssistant(pending, data.content, data.references || []);
    appendArchivePrompt(pending, data);
    await loadArtifacts();
  } catch (error) {
    updateAssistant(pending, `生成失败：${error.message}`, []);
  }
}

function openKnowledgeWorkspace() {
  chatStage.hidden = true;
  affairsDashboard.hidden = true;
  knowledgeWorkspace.hidden = false;
  backToChatBtn.textContent = `‹ 返回${assistantModes[currentMode].title}`;
  selectKnowledgeTab("documents");
  refreshAll().catch(() => {});
}

function showChatWorkspace() {
  knowledgeWorkspace.hidden = true;
  const isAffairs = currentMode === "affairs";
  affairsDashboard.hidden = !isAffairs;
  chatStage.hidden = isAffairs;
  if (isAffairs) affairsSearchInput.focus();
  else input.focus();
}

function selectKnowledgeTab(tab) {
  document.querySelectorAll("[data-knowledge-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.knowledgeTab === tab);
  });
  document.querySelectorAll("[data-knowledge-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.knowledgePanel !== tab;
  });
}

async function createOutlineFromKnowledge() {
  const config = assistantModes[currentMode];
  const topic = window.prompt("输入需要生成文件大纲的主题", lastPrompt || config.defaultPrompt);
  if (!topic?.trim()) return;
  createOutlineBtn.disabled = true;
  createOutlineBtn.textContent = "正在生成...";
  try {
    const response = await fetch("/api/artifacts/outline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: config.apiMode, prompt: topic.trim() }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const artifact = await response.json();
    await loadArtifacts();
    openArtifactViewer(artifact);
  } catch (error) {
    window.alert(`文件大纲生成失败：${error.message}`);
  } finally {
    createOutlineBtn.disabled = false;
    createOutlineBtn.textContent = "生成文件大纲";
  }
}

function appendArchivePrompt(messageElement, artifact) {
  if (!messageElement || !artifact?.artifact_id) return;
  const prompt = document.createElement("div");
  prompt.className = "archive-prompt";
  prompt.innerHTML = `
    <span>是否将本次${artifactTypeLabel(artifact.artifact_type)}加入知识库？</span>
    <button type="button">加入知识库</button>
  `;
  const button = prompt.querySelector("button");
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "正在保存...";
    try {
      await archiveArtifact(artifact.artifact_id);
      button.textContent = "已加入知识库";
      prompt.classList.add("archived");
      await refreshAll();
    } catch (error) {
      button.disabled = false;
      button.textContent = "重试";
    }
  });
  messageElement.appendChild(prompt);
}

async function archiveArtifact(artifactId) {
  const response = await fetch(`/api/artifacts/${artifactId}/archive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function openDocumentViewer(documentId) {
  const documentData = latestDocuments.find((item) => item.id === documentId) ||
    (await fetchJson(`/api/documents/${documentId}`));
  assetViewerTitle.textContent = documentData.source_name;
  assetDownloadLink.hidden = false;
  assetDownloadLink.href = documentData.download_url;
  assetViewerBody.innerHTML = '<div class="viewer-loading">正在读取资料...</div>';
  assetViewerModal.hidden = false;

  if (documentData.preview_kind === "image") {
    assetViewerBody.innerHTML = `<img class="asset-image-preview" src="${documentData.view_url}" alt="${escapeHtml(documentData.source_name)}" />`;
    return;
  }
  if (documentData.preview_kind === "pdf") {
    assetViewerBody.innerHTML = `<iframe class="asset-pdf-preview" src="${documentData.view_url}" title="${escapeHtml(documentData.source_name)}"></iframe>`;
    return;
  }
  const details = documentData.content === undefined
    ? await fetchJson(`/api/documents/${documentId}`)
    : documentData;
  assetViewerBody.innerHTML = details.content
    ? `<pre class="asset-text-preview">${escapeHtml(details.content)}</pre>`
    : '<div class="empty-state">该文件没有可显示的文本，可下载原文件查看。</div>';
}

async function openArtifactViewer(artifactOrId) {
  const artifact = typeof artifactOrId === "string"
    ? await fetchJson(`/api/artifacts/${artifactOrId}`)
    : artifactOrId;
  assetViewerTitle.textContent = artifact.title || artifactTypeLabel(artifact.artifact_type);
  assetDownloadLink.hidden = true;
  assetViewerBody.innerHTML = `
    <div class="artifact-preview markdown-body">${renderMarkdown(artifact.content || "")}</div>
    <div class="viewer-archive-action">
      <span>${artifact.archived ? "该内容已加入知识库" : "需要在资料检索中继续使用？"}</span>
      ${artifact.archived ? "" : '<button id="viewerArchiveBtn" class="primary-btn" type="button">加入知识库</button>'}
    </div>
  `;
  assetViewerModal.hidden = false;
  const archiveButton = document.querySelector("#viewerArchiveBtn");
  archiveButton?.addEventListener("click", async () => {
    archiveButton.disabled = true;
    await archiveArtifact(artifact.artifact_id || artifact.id);
    archiveButton.textContent = "已加入知识库";
    await refreshAll();
  });
}

function closeAssetViewer() {
  assetViewerModal.hidden = true;
  assetViewerBody.innerHTML = "";
}

function artifactTypeLabel(type) {
  return {
    mindmap: "思维导图",
    quiz: "练习测验",
    outline: "文件大纲",
  }[type] || "生成内容";
}

async function streamChat(message) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: assistantModes[currentMode].apiMode,
      message,
      session_id: currentSessionId,
      deep_research: deepResearchEnabled,
      web_search: webSearchEnabled,
    }),
  });
  if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let answer = "";
  let references = [];

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const raw of events) {
      const parsed = parseSse(raw);
      if (!parsed) continue;
      if (parsed.event === "meta") {
        currentSessionId = parsed.data.session_id;
        setApiLabel(parsed.data.mock);
      }
      if (parsed.event === "token") {
        answer += parsed.data.text || "";
        updateAssistant(currentAssistant, answer, references);
      }
      if (parsed.event === "references") {
        references = parsed.data.references || [];
        updateAssistant(currentAssistant, answer, references);
      }
      if (parsed.event === "error") {
        answer += `\n\n调用出错：${parsed.data.message}`;
        updateAssistant(currentAssistant, answer, references);
      }
    }
  }
}

function parseSse(raw) {
  const lines = raw.split("\n");
  const eventLine = lines.find((line) => line.startsWith("event:"));
  const dataLine = lines.find((line) => line.startsWith("data:"));
  if (!eventLine || !dataLine) return null;
  try {
    return {
      event: eventLine.slice(6).trim(),
      data: JSON.parse(dataLine.slice(5).trim()),
    };
  } catch {
    return null;
  }
}

function addMessage(role, text, options = {}) {
  const article = document.createElement("article");
  article.className = `message ${role}${options.typing ? " typing" : ""}`;
  const speaker = role === "user" ? "我" : assistantModes[currentMode].title;
  article.innerHTML = `
    <strong>${speaker}</strong>
    <div class="markdown-body">${renderMarkdown(text || "正在思考...")}</div>
    <div class="references"></div>
  `;
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function updateAssistant(element, text, references) {
  if (!element) return;
  element.querySelector(".markdown-body").innerHTML = renderMarkdown(text || "正在思考...");
  element.querySelector(".references").innerHTML = renderReferences(references);
  messages.scrollTop = messages.scrollHeight;
}

function renderReferences(references = []) {
  if (!references.length) return "";
  return `
    <div class="reference-title">参考资料</div>
    ${references
      .map(
        (ref) => `
        <div class="reference-item">
          <strong>${escapeHtml(ref.source_name)}</strong>
          <span>片段 ${Number(ref.chunk_index) + 1} · 匹配分 ${ref.score}</span>
          <p>${escapeHtml(ref.snippet)}</p>
        </div>
      `
      )
      .join("")}
  `;
}

function renderMarkdown(text) {
  const escaped = escapeHtml(text);
  return escaped
    .replace(/```(?:\w+)?\n([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^\- (.*)$/gm, "<li>$1</li>")
    .replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, url) => {
      const safeUrl = String(url || "").trim();
      if (/^(https?:\/\/|\/api\/reports\/|\/api\/exports\/)/i.test(safeUrl)) {
        return `<a href="${safeUrl}" target="_blank" rel="noreferrer">${label}</a>`;
      }
      return label;
    })
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/^(.+)$/s, "<p>$1</p>")
    .replace(/<p>(<h[123]>)/g, "$1")
    .replace(/(<\/h[123]>)<\/p>/g, "$1")
    .replace(/<p>(<ul>)/g, "$1")
    .replace(/(<\/ul>)<\/p>/g, "$1")
    .replace(/<p>(<pre>)/g, "$1")
    .replace(/(<\/pre>)<\/p>/g, "$1");
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setLoading(isLoading) {
  sendBtn.disabled = isLoading;
  sendBtn.textContent = isLoading ? "…" : "↑";
}

function updateAuthUi() {
  const signedIn = authState?.authenticated;
  const label = signedIn ? authState.user.name : "登录信息门户";
  loginBtn.textContent = label;
  homeLoginBtn.textContent = label;
  loginBtn.classList.toggle("signed-in", signedIn);
  homeLoginBtn.classList.toggle("signed-in", signedIn);
  loginStatus.textContent = signedIn ? `已虚拟登录：${authState.user.name}（${authState.user.school}）` : "未登录";
}

async function loadAuthPortal() {
  try {
    const data = await fetchJson("/api/auth/status");
    authPortalLink.href = data.portal_url;
  } catch {
    authPortalLink.href = "https://my.nau.edu.cn/index.html#/";
  }
  updateAuthUi();
}

async function refreshAll() {
  await Promise.all([
    loadStatus(),
    loadDocuments(),
    loadArtifacts(),
    loadTimetable(),
    loadSessions(),
    loadApiCalls(),
  ]);
}

async function loadStatus() {
  const data = await fetchJson("/api/status");
  setApiLabel(data.mock_mode);
  apiStatus.textContent = `${data.model_name} · 文档 ${data.document_count} · 片段 ${data.chunk_count}`;
}

function setApiLabel(isMock) {
  const label = isMock ? "API 服务 · 模拟模式" : "API 服务 · 真实 API";
  statusBadge.textContent = label;
  homeStatusBadge.textContent = label;
}

async function loadDocuments() {
  const docs = await fetchJson("/api/documents");
  latestDocuments = docs;
  knowledgeDocCount.textContent = docs.length;
  documentList.innerHTML = docs.length
    ? docs
        .slice(0, 4)
        .map(
          (doc) => `
          <button class="list-button" data-view-document="${doc.id}">
            ${escapeHtml(doc.source_name)}
            <small>${doc.file_type} · ${doc.chunk_count} 片段 · 查看或下载</small>
          </button>
        `
        )
        .join("")
    : '<div class="muted">暂无资料</div>';
  knowledgeDocumentList.innerHTML = docs.length
    ? docs
        .map(
          (doc) => `
          <article class="asset-row">
            <span class="file-badge">${escapeHtml(doc.file_type)}</span>
            <div class="asset-info">
              <strong>${escapeHtml(doc.source_name)}</strong>
              <span>${scopeLabel(doc.scope)} · ${doc.chunk_count} 个检索片段</span>
            </div>
            <div class="asset-actions">
              <button type="button" data-view-document="${doc.id}">在线查看</button>
              <a href="${doc.download_url}" target="_blank" rel="noreferrer">下载</a>
            </div>
          </article>
        `
        )
        .join("")
    : '<div class="empty-state">还没有学习资料。</div>';
  document.querySelectorAll("[data-view-document]").forEach((button) => {
    button.addEventListener("click", () => openDocumentViewer(button.dataset.viewDocument));
  });
}

async function loadArtifacts() {
  const artifacts = await fetchJson("/api/artifacts");
  latestArtifacts = artifacts;
  knowledgeArtifactCount.textContent = artifacts.length;
  knowledgeArtifactList.innerHTML = artifacts.length
    ? artifacts
        .map(
          (artifact) => `
          <article class="asset-row">
            <span class="file-badge generated">${artifactTypeLabel(artifact.artifact_type).slice(0, 2)}</span>
            <div class="asset-info">
              <strong>${escapeHtml(artifact.title)}</strong>
              <span>${artifactTypeLabel(artifact.artifact_type)} · ${artifact.archived ? "已加入知识库" : "历史生成记录"}</span>
            </div>
            <div class="asset-actions">
              <button type="button" data-view-artifact="${artifact.id}">直接查看</button>
              ${
                artifact.archived
                  ? '<span class="archived-label">已归档</span>'
                  : `<button type="button" data-archive-artifact="${artifact.id}">加入知识库</button>`
              }
            </div>
          </article>
        `
        )
        .join("")
    : '<div class="empty-state">还没有思维导图、文件大纲或练习测验。</div>';
  knowledgeArtifactList.querySelectorAll("[data-view-artifact]").forEach((button) => {
    button.addEventListener("click", () => openArtifactViewer(button.dataset.viewArtifact));
  });
  knowledgeArtifactList.querySelectorAll("[data-archive-artifact]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      await archiveArtifact(button.dataset.archiveArtifact);
      await refreshAll();
    });
  });
}

async function loadTimetable() {
  const entries = await fetchJson("/api/timetable");
  knowledgeCourseCount.textContent = entries.length;
  timetableBody.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
          <tr>
            <td><strong>${escapeHtml(entry.course_name)}</strong></td>
            <td>${escapeHtml(entry.day_of_week || "-")}</td>
            <td>${escapeHtml(entry.class_time || "-")}</td>
            <td>${escapeHtml(entry.teacher || "-")}</td>
            <td>${escapeHtml(entry.location || "-")}</td>
            <td>${escapeHtml(entry.weeks || "-")}</td>
          </tr>
        `
        )
        .join("")
    : '<tr><td colspan="6" class="empty-cell">尚未导入课程表</td></tr>';
}

function scopeLabel(scope) {
  return {
    builtin: "系统资料",
    knowledge: "个人上传",
    generated: "生成内容",
    timetable: "课程表",
  }[scope] || "学习资料";
}

async function loadSessions() {
  const sessions = await fetchJson("/api/sessions");
  sessionList.innerHTML = sessions.length
    ? sessions
        .slice(0, 4)
        .map(
          (session) => `
          <button class="list-button" data-session="${session.id}">
            ${escapeHtml(session.title)}
            <small>${session.mode === "audit" ? "学生助手" : escapeHtml(session.mode)}</small>
          </button>
        `
        )
        .join("")
    : '<div class="muted">暂无对话</div>';
  sessionList.querySelectorAll("[data-session]").forEach((button) => {
    button.addEventListener("click", () => restoreSession(button.dataset.session));
  });
}

async function restoreSession(sessionId) {
  const data = await fetchJson(`/api/sessions/${sessionId}`);
  currentSessionId = sessionId;
  const mode = data.session.mode === "audit" ? "learning" : data.session.mode;
  openAssistant(assistantModes[mode] ? mode : "learning");
  currentSessionId = sessionId;
  messages.innerHTML = "";
  data.messages.forEach((msg) => addMessage(msg.role, msg.content));
}

async function loadApiCalls() {
  const calls = await fetchJson("/api/api-calls");
  callList.innerHTML = calls.length
    ? calls
        .slice(0, 3)
        .map(
          (call) => `
          <div class="call-item ${call.success ? "ok" : "fail"}">
            <span>${call.mock ? "Mock" : escapeHtml(call.model_name)}</span>
            <small>${call.duration_ms}ms</small>
          </div>
        `
        )
        .join("")
    : '<div class="muted">暂无调用</div>';
}

function getAffairsData() {
  return window.AFFAIRS_DEMO_DATA || { profiles: {}, sharedServices: [], updatedAt: "" };
}

function getAffairsProfile() {
  const profiles = getAffairsData().profiles;
  if (!profiles[currentAffairsProfileId]) currentAffairsProfileId = "undergraduate";
  return profiles[currentAffairsProfileId];
}

function getAffairsStorageKey(type) {
  return `affairs_${type}_${currentAffairsProfileId}`;
}

function loadAffairsTaskState() {
  const profile = getAffairsProfile();
  affairsTasks = JSON.parse(JSON.stringify(profile.tasks || []));
  const saved = JSON.parse(localStorage.getItem(getAffairsStorageKey("tasks")) || "{}");
  affairsTasks.forEach((task) => {
    const checked = saved[task.id];
    if (!Array.isArray(checked)) return;
    task.materials.forEach((material, index) => {
      if (typeof checked[index] === "boolean") material.checked = checked[index];
    });
  });
}

function saveAffairsTaskState() {
  const state = Object.fromEntries(
    affairsTasks.map((task) => [task.id, task.materials.map((material) => Boolean(material.checked))])
  );
  localStorage.setItem(getAffairsStorageKey("tasks"), JSON.stringify(state));
}

function renderAffairsDashboard() {
  const profile = getAffairsProfile();
  if (!profile) return;
  loadAffairsTaskState();
  affairsProfileSelect.value = profile.id;
  affairsProfileAvatar.textContent = profile.name.slice(0, 1);
  affairsProfileName.textContent = profile.name;
  affairsProfileMeta.textContent = `${profile.level} · ${profile.role}`;
  affairsGreetingTitle.innerHTML = `你好，${escapeHtml(profile.name)} <span aria-hidden="true">👋</span>`;
  affairsGreetingText.textContent = profile.greeting;
  affairsProfileFacts.innerHTML = [profile.level, profile.grade, profile.college, profile.campus]
    .map((item) => `<span>${escapeHtml(item)}</span>`)
    .join("");
  affairsQuickQuestions.innerHTML = profile.quickQuestions
    .map((question) => `<button type="button" data-affairs-query="${escapeHtml(question)}">${escapeHtml(question)}</button>`)
    .join("");
  affairsDataUpdatedAt.textContent = `演示数据更新：${getAffairsData().updatedAt}`;
  renderAffairsTasks();
  renderAffairsPriorities();
  renderAffairsServices();
  renderAffairsNotices([], { loading: true });
  loadAffairsNotices();
  renderAffairsRecent();
}

function renderAffairsTasks() {
  affairsTaskCount.textContent = `共 ${affairsTasks.length} 项`;
  affairsTaskGrid.innerHTML = affairsTasks
    .map((task) => {
      const done = task.materials.filter((item) => item.checked).length;
      const total = task.materials.length || 1;
      const progress = task.status === "completed" ? 100 : Math.round((done / total) * 100);
      const status = affairsStatusMeta(task.status);
      const deadline = `<span>${escapeHtml(formatAffairsTime(task, "无统一截止时间"))}</span>`;
      return `
        <article class="affairs-task-card">
          <div class="affairs-card-title-row">
            <h4>${escapeHtml(task.title)}</h4>
            <span class="source-badge ${sourceStatusClass(task.sourceStatus)}">${escapeHtml(task.sourceStatus)}</span>
          </div>
          <div class="affairs-task-status"><strong class="${status.className}">${status.label}</strong><span>${done}/${total}</span></div>
          <div class="affairs-progress"><i style="width:${progress}%"></i></div>
          <p><b>下一步：</b>${escapeHtml(task.nextStep)}</p>
          <div class="affairs-card-meta">${deadline}<span>${escapeHtml(task.department)}</span></div>
          <button class="affairs-outline-btn" type="button" data-affairs-action="task-detail" data-task-id="${escapeHtml(task.id)}">
            ${task.status === "completed" ? "查看结果" : progress > 0 ? "继续办理" : "查看流程"}
          </button>
        </article>`;
    })
    .join("");
}

function renderAffairsPriorities() {
  const profile = getAffairsProfile();
  const saved = new Set(JSON.parse(localStorage.getItem(getAffairsStorageKey("priorities")) || "[]"));
  affairsPriorityGrid.innerHTML = profile.priorities
    .map((item) => `
      <article class="affairs-priority-card ${escapeHtml(item.tone)}">
        <div class="priority-icon">${escapeHtml(item.icon)}</div>
        <span class="source-badge ${sourceStatusClass(item.sourceStatus)}">${escapeHtml(item.sourceStatus)}</span>
        <h4>${escapeHtml(item.title)}</h4>
        <p>${escapeHtml(item.description)}</p>
        <strong class="priority-deadline">${formatAffairsDeadline(item)}</strong>
        <div class="priority-actions">
          <button type="button" data-affairs-action="priority-source" data-priority-id="${escapeHtml(item.id)}">${item.timeBasis ? "查看依据" : "查看详情"}</button>
          <button class="priority-add ${saved.has(item.id) ? "added" : ""}" type="button" data-affairs-action="priority-add" data-priority-id="${escapeHtml(item.id)}">${saved.has(item.id) ? "已加入" : "+ 待办"}</button>
        </div>
      </article>`)
    .join("");
}

function renderAffairsServices() {
  const isGraduate = currentAffairsProfileId === "graduate";
  affairsServiceGrid.innerHTML = getAffairsData().sharedServices
    .map((service) => `
      <a class="affairs-service-card" href="${escapeHtml(service.sourceUrl)}" target="_blank" rel="noreferrer">
        <span>${escapeHtml(service.icon)}</span>
        <strong>${escapeHtml(service.title)}</strong>
        <small>${escapeHtml(isGraduate ? service.graduateDesc : service.undergradDesc)}</small>
        <em class="${sourceStatusClass(service.sourceStatus)}">${escapeHtml(service.sourceStatus)}</em>
      </a>`)
    .join("");
}

function renderAffairsNotices(notices = [], options = {}) {
  if (options.loading) {
    affairsNoticeList.innerHTML = Array.from({ length: 4 }, () => `
      <article class="affairs-notice-card news-loading-card">
        <span class="notice-icon"></span><div><i></i><i></i><i></i></div>
      </article>`).join("");
    return;
  }
  if (!notices.length) {
    affairsNoticeList.innerHTML = `
      <div class="affairs-news-empty">
        <strong>暂未读取到匹配通知</strong>
        <span>${escapeHtml(options.message || "请稍后刷新，或检查本地服务的网络连接。")}</span>
      </div>`;
    return;
  }
  affairsNoticeList.innerHTML = notices
    .map((notice) => `
      <article class="affairs-notice-card">
        <span class="notice-icon">${escapeHtml(notice.icon || "📢")}</span>
        <div>
          <div class="affairs-card-title-row">
            <h4>${escapeHtml(notice.title)}</h4>
            <span class="source-badge ${sourceStatusClass(notice.sourceStatus)}">${escapeHtml(notice.sourceStatus)}</span>
          </div>
          <p>${escapeHtml(notice.summary)}</p>
          <div class="affairs-news-meta">
            <span>${escapeHtml(notice.matchReason)}</span>
            <span>发布于 ${escapeHtml(notice.publishedDate)}</span>
            <b class="${notice.statusLabel === "已截止" ? "expired" : ""}">${escapeHtml(notice.statusLabel)}</b>
          </div>
        </div>
        <div class="notice-actions">
          <strong>${escapeHtml(notice.sourceName)}</strong>
          <a href="${escapeHtml(notice.sourceUrl)}" target="_blank" rel="noreferrer">查看具体通知 ↗</a>
        </div>
      </article>`)
    .join("");
}

async function loadAffairsNotices(forceRefresh = false) {
  const profile = getAffairsProfile();
  const requestedProfile = profile.id;
  const requestId = ++affairsNewsRequestId;
  affairsNewsRefreshBtn.disabled = true;
  affairsNewsRefreshBtn.textContent = "更新中…";
  affairsNoticeMeta.textContent = `${profile.level} · 按发布时间排序`;
  try {
    const params = new URLSearchParams({
      profile: requestedProfile,
      grade: profile.grade,
      limit: "6",
    });
    if (forceRefresh) params.set("refresh", "true");
    const response = await fetch(`/api/affairs/notices?${params}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (requestId !== affairsNewsRequestId || requestedProfile !== currentAffairsProfileId) return;
    renderAffairsNotices(data.items || []);
    const updateTime = new Date(data.generatedAt).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    affairsNoticeMeta.textContent = data.liveCount
      ? `${profile.level} · 官网实时聚合 · ${updateTime}`
      : `${profile.level} · 已核验回退数据 · ${updateTime}`;
  } catch (error) {
    if (requestId !== affairsNewsRequestId) return;
    affairsNoticeMeta.textContent = `${profile.level} · 更新失败`;
    renderAffairsNotices([], { message: `资讯接口暂不可用：${error.message}` });
  } finally {
    if (requestId === affairsNewsRequestId) {
      affairsNewsRefreshBtn.disabled = false;
      affairsNewsRefreshBtn.textContent = "↻ 刷新资讯";
    }
  }
}

function renderAffairsRecent() {
  const profile = getAffairsProfile();
  const saved = JSON.parse(localStorage.getItem(getAffairsStorageKey("recent")) || "[]");
  const items = [...new Set([...saved, ...profile.recent])].slice(0, 4);
  affairsRecentList.innerHTML = items
    .map((question) => `<button type="button" data-affairs-query="${escapeHtml(question)}"><span>${escapeHtml(question)}</span><small>点击再次询问</small><b>→</b></button>`)
    .join("");
}

function affairsStatusMeta(status) {
  return {
    preparing: { label: "材料准备中", className: "preparing" },
    ready: { label: "可办理", className: "ready" },
    not_started: { label: "待开始", className: "not-started" },
    completed: { label: "已完成", className: "completed" },
  }[status] || { label: "进行中", className: "preparing" };
}

function sourceStatusClass(status) {
  if (String(status).includes("演示")) return "demo";
  if (String(status).includes("核验") || String(status).includes("实时")) return "official";
  return "pending";
}

function formatAffairsTime(item, emptyLabel = "可随时查看") {
  if (item.deadline) {
    const deadline = new Date(`${item.deadline}T23:59:59`);
    const days = Math.ceil((deadline.getTime() - Date.now()) / 86400000);
    const countdown = days >= 0 ? `还有 ${days} 天` : `已过 ${Math.abs(days)} 天`;
    return `${item.deadline} · ${countdown}`;
  }
  if (item.expectedWindow) return `${item.expectedWindow} · 待官方通知`;
  return emptyLabel;
}

function formatAffairsDeadline(item) {
  return formatAffairsTime(item);
}

function handleAffairsDashboardClick(event) {
  const queryButton = event.target.closest("[data-affairs-query]");
  if (queryButton) {
    affairsSearchInput.value = queryButton.dataset.affairsQuery;
    answerAffairsQuestion(queryButton.dataset.affairsQuery);
    return;
  }
  const actionButton = event.target.closest("[data-affairs-action]");
  if (!actionButton) return;
  const action = actionButton.dataset.affairsAction;
  if (action === "task-detail" || action === "notice-task") {
    openAffairsTaskDetail(actionButton.dataset.taskId);
  }
  if (action === "priority-source") {
    const item = getAffairsProfile().priorities.find((priority) => priority.id === actionButton.dataset.priorityId);
    if (item) window.open(item.sourceUrl, "_blank", "noopener,noreferrer");
  }
  if (action === "priority-add") toggleAffairsPriority(actionButton.dataset.priorityId);
}

function toggleAffairsPriority(priorityId) {
  const key = getAffairsStorageKey("priorities");
  const saved = new Set(JSON.parse(localStorage.getItem(key) || "[]"));
  if (saved.has(priorityId)) saved.delete(priorityId);
  else saved.add(priorityId);
  localStorage.setItem(key, JSON.stringify([...saved]));
  renderAffairsPriorities();
}

function openAffairsTaskDetail(taskId) {
  const task = affairsTasks.find((item) => item.id === taskId);
  if (!task) return;
  const done = task.materials.filter((item) => item.checked).length;
  affairsDetailBody.innerHTML = `
    <p class="affairs-eyebrow">${escapeHtml(task.department)}</p>
    <h2 id="affairsDetailTitle">${escapeHtml(task.title)}</h2>
    <div class="affairs-detail-badges">
      <span class="source-badge ${sourceStatusClass(task.sourceStatus)}">${escapeHtml(task.sourceStatus)}</span>
      <span>${affairsStatusMeta(task.status).label}</span>
    </div>
    <p class="affairs-detail-summary">${escapeHtml(task.summary)}</p>
    <dl class="affairs-detail-list">
      <div><dt>当前进度</dt><dd>${done}/${task.materials.length} 项已完成</dd></div>
      <div><dt>下一步</dt><dd>${escapeHtml(task.nextStep)}</dd></div>
      <div><dt>时间状态</dt><dd>${escapeHtml(formatAffairsTime(task, "以官方通知或办理窗口为准"))}</dd></div>
      ${task.timeBasis ? `<div><dt>时间依据</dt><dd>${escapeHtml(task.timeBasis)}</dd></div>` : ""}
    </dl>
    <h3 class="affairs-material-title">材料与步骤</h3>
    <div class="affairs-material-list">
      ${task.materials.map((material, index) => `
        <label>
          <input type="checkbox" data-affairs-material="${index}" data-task-id="${escapeHtml(task.id)}" ${material.checked ? "checked" : ""} />
          <span>${escapeHtml(material.name)}</span>
        </label>`).join("")}
    </div>
    ${renderAffairsSourceLinks(task)}`;
  affairsDetailModal.hidden = false;
}

function renderAffairsSourceLinks(record) {
  const sources = Array.isArray(record.sourceUrls) && record.sourceUrls.length
    ? record.sourceUrls
    : [{ title: record.sourceTitle || "官方来源", url: record.sourceUrl }];
  return sources
    .filter((source) => source?.url)
    .map((source) => `<a class="affairs-source-link" href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">查看${escapeHtml(source.title || "官方来源")} ↗</a>`)
    .join("");
}

function closeAffairsDetail() {
  affairsDetailModal.hidden = true;
}

function rememberAffairsQuestion(question) {
  const key = getAffairsStorageKey("recent");
  const saved = JSON.parse(localStorage.getItem(key) || "[]");
  localStorage.setItem(key, JSON.stringify([question, ...saved.filter((item) => item !== question)].slice(0, 4)));
  renderAffairsRecent();
}

function findLocalAffairsAnswer(question) {
  const profile = getAffairsProfile();
  const tests = [
    { regex: /图书|借阅/, keywords: ["图书", "借阅"] },
    { regex: /校园卡|一卡通|挂失/, keywords: ["校园卡", "一卡通", "挂失"] },
    { regex: /成绩单|证明|打印/, keywords: ["成绩单", "证明", "打印"] },
    { regex: /奖学金|助学金|奖助/, keywords: ["奖学金", "助学金", "奖助"] },
    { regex: /四六级|四级|六级|CET/i, keywords: ["四六级", "四级", "六级"] },
    { regex: /开题|论文|培养计划/, keywords: ["开题", "论文", "培养"] },
  ];
  if (/学生证/.test(question)) {
    return `### 学生证补办\n\n公开网站暂未披露完整办理流程，当前状态为 **待学校确认**。建议先咨询所在学院或书院辅导员，确认申请表、照片、遗失说明及办理地点后再前往，避免依据演示信息办理。`;
  }
  const matched = tests.find((item) => item.regex.test(question));
  if (!matched) return "";
  const records = [
    ...affairsTasks.map((item) => ({ ...item, kind: "事务", text: `${item.title}${item.summary}${item.nextStep}` })),
    ...profile.priorities.map((item) => ({ ...item, kind: "重点", text: `${item.title}${item.description}` })),
    ...profile.notices.map((item) => ({ ...item, kind: "通知", text: `${item.title}${item.summary}` })),
    ...getAffairsData().sharedServices.map((item) => ({ ...item, kind: "服务", text: `${item.title}${item.undergradDesc}${item.graduateDesc}` })),
  ];
  const record = records.find((item) => matched.keywords.some((keyword) => item.text.includes(keyword)));
  if (!record) return "";
  const detail = record.nextStep || record.description || record.summary || (currentAffairsProfileId === "graduate" ? record.graduateDesc : record.undergradDesc);
  const materialText = record.materials?.length
    ? `\n\n**材料与步骤**\n${record.materials.map((item) => `- ${item.checked ? "已完成" : "待完成"}：${item.name}`).join("\n")}`
    : "";
  const timeText = record.deadline || record.expectedWindow
    ? `\n\n**时间**：${formatAffairsTime(record, "待官方通知")}`
    : "";
  const timeBasis = record.timeBasis ? `\n\n**时间依据**：${record.timeBasis}` : "";
  const sources = Array.isArray(record.sourceUrls) && record.sourceUrls.length
    ? record.sourceUrls
    : [{ title: record.sourceTitle || "官方来源", url: record.sourceUrl }];
  const sourceLinks = sources.filter((source) => source?.url).map((source) => `[${source.title || "官方来源"}](${source.url})`).join(" · ");
  return `### ${record.title}\n\n**身份匹配**：${profile.level} · ${record.kind}\n\n**办理提示**：${detail}${materialText}${timeText}${timeBasis}\n\n**信息状态**：${record.sourceStatus}\n\n${sourceLinks}`;
}

async function answerAffairsQuestion(rawQuestion) {
  const question = String(rawQuestion || "").trim();
  if (!question) return;
  affairsSearchInput.value = "";
  affairsAgentResult.hidden = false;
  affairsAgentResultBody.innerHTML = "<p>正在根据学生身份检索事务、通知与官方入口…</p>";
  rememberAffairsQuestion(question);
  const localAnswer = findLocalAffairsAnswer(question);
  if (localAnswer) {
    affairsAgentResultBody.innerHTML = renderMarkdown(localAnswer);
    affairsAgentResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
    return;
  }
  const profile = getAffairsProfile();
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "affairs",
        message: `用户身份：${profile.level}，${profile.grade}，${profile.college}。问题：${question}。请按办理条件、材料、步骤、时间、入口和待确认项回答；不确定的信息必须明确说明。`,
        session_id: localStorage.getItem(getAffairsStorageKey("session")) || null,
      }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    localStorage.setItem(getAffairsStorageKey("session"), data.session_id);
    affairsAgentResultBody.innerHTML = `${renderMarkdown(data.answer)}${renderReferences(data.references || [])}`;
  } catch (error) {
    affairsAgentResultBody.innerHTML = renderMarkdown(`事务检索暂时不可用：${error.message}\n\n你仍可使用下方事务卡片和官方入口。`);
  }
  affairsAgentResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

loadAuthPortal();
openAssistant("affairs");
