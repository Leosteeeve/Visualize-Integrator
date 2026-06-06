const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const rawMath = String.raw;

const elements = {
  sections: {
    learn: $("#learnSection"),
    practice: $("#practiceSection"),
    qa: $("#qaSection"),
    tool: $("#toolSection"),
  },
  modeTabs: $$(".mode-tab"),
  expression: $("#expression"),
  expressionLabel: $("#expressionLabel"),
  lower: $("#lower"),
  upper: $("#upper"),
  xLower: $("#xLower"),
  xUpper: $("#xUpper"),
  yLower: $("#yLower"),
  yUpper: $("#yUpper"),
  boundsGrid: $("#boundsGrid"),
  doubleBoundsGrid: $("#doubleBoundsGrid"),
  polarBoundsGrid: $("#polarBoundsGrid"),
  innerExpression: $("#innerExpression"),
  rLower: $("#rLower"),
  rUpper: $("#rUpper"),
  thetaLower: $("#thetaLower"),
  thetaUpper: $("#thetaUpper"),
  polarAreaFields: $$(".polar-area-field"),
  polarDoubleFields: $$(".polar-double-field"),
  calculate: $("#calculate"),
  statusLine: $("#statusLine"),
  modeButtons: $$(".segment"),
  palette: $("#palette"),
  qaPalette: $("#qaPalette"),
  examples: $("#examples"),
  plot: $("#plot"),
  plotTitle: $("#plotTitle"),
  numericChip: $("#numericChip"),
  engineBadge: $("#engineBadge"),
  statusResult: $("#statusResult"),
  exactResult: $("#exactResult"),
  numericResult: $("#numericResult"),
  fourthResultLabel: $("#fourthResultLabel"),
  antiderivativeResult: $("#antiderivativeResult"),
  errorResult: $("#errorResult"),
  messages: $("#messages"),
  lessonTabs: $("#lessonTabs"),
  lessonContent: $("#lessonContent"),
  lessonSolutionTitle: $("#lessonSolutionTitle"),
  lessonSolutionBody: $("#lessonSolutionBody"),
  practiceKind: $("#practiceKind"),
  practiceLevel: $("#practiceLevel"),
  generatePractice: $("#generatePractice"),
  practiceProblem: $("#practiceProblem"),
  practiceSolutionTitle: $("#practiceSolutionTitle"),
  practiceSolutionBody: $("#practiceSolutionBody"),
  qaRaw: $("#qaRaw"),
  qaMode: $("#qaMode"),
  qaExpression: $("#qaExpression"),
  qaExpressionLabel: $("#qaExpressionLabel"),
  qaLower: $("#qaLower"),
  qaUpper: $("#qaUpper"),
  qaXLower: $("#qaXLower"),
  qaXUpper: $("#qaXUpper"),
  qaYLower: $("#qaYLower"),
  qaYUpper: $("#qaYUpper"),
  qaBounds: $("#qaBounds"),
  qaDoubleBounds: $("#qaDoubleBounds"),
  qaPolarBounds: $("#qaPolarBounds"),
  qaInnerExpression: $("#qaInnerExpression"),
  qaRLower: $("#qaRLower"),
  qaRUpper: $("#qaRUpper"),
  qaThetaLower: $("#qaThetaLower"),
  qaThetaUpper: $("#qaThetaUpper"),
  qaPolarAreaFields: $$(".qa-polar-area-field"),
  qaPolarDoubleFields: $$(".qa-polar-double-field"),
  askQuestion: $("#askQuestion"),
  qaSolutionTitle: $("#qaSolutionTitle"),
  qaSolutionBody: $("#qaSolutionBody"),
};

let currentMode = "definite";
let currentLesson = "zero";
let lastPlot = null;
let lastPracticeProblem = null;
const PRACTICE_SIGNATURE_STORAGE_KEY = "calculus.practice.signatures.v1";

function apiBaseUrl() {
  const configured = window.CALCULUS_API_BASE || "";
  const params = new URLSearchParams(window.location.search);
  const queryApi = params.get("api");
  if (queryApi) {
    try {
      window.localStorage?.setItem("calculus.apiBase", queryApi);
    } catch {
      // Ignore private browsing or storage-denied modes.
    }
    return queryApi.replace(/\/+$/, "");
  }
  if (configured) return String(configured).replace(/\/+$/, "");
  try {
    return (window.localStorage?.getItem("calculus.apiBase") || "").replace(/\/+$/, "");
  } catch {
    return "";
  }
}

function apiUrl(path) {
  return `${apiBaseUrl()}${path}`;
}

const quickTemplates = [
  { label: "x", insert: "x" },
  { label: "y", insert: "y" },
  { label: "r", insert: "r" },
  { label: "θ", insert: "theta" },
  { label: "□²", insert: "^2" },
  { label: "√", insert: "sqrt()" },
  { label: "分数", insert: "1/()" },
  { label: "sin", insert: "sin()" },
  { label: "cos", insert: "cos()" },
  { label: "exp", insert: "exp()" },
  { label: "ln", insert: "log()" },
  { label: "π", insert: "pi" },
  { label: "∞", insert: "oo" },
];

const cannedProblems = {
  powerArea: {
    id: "powerArea",
    title: "幂函数面积",
    mode: "definite",
    expression: "x^2",
    lower: "0",
    upper: "1",
    statement: rawMath`\int_0^1 x^2\,dx`,
  },
  sinArea: {
    id: "sinArea",
    title: "正弦半波面积",
    mode: "definite",
    expression: "sin(x)",
    lower: "0",
    upper: "pi",
    statement: rawMath`\int_0^\pi \sin x\,dx`,
  },
  uSub: {
    id: "uSub",
    title: "换元法",
    mode: "definite",
    expression: "2*x*cos(x^2)",
    lower: "0",
    upper: "1",
    statement: rawMath`\int_0^1 2x\cos(x^2)\,dx`,
  },
  parts: {
    id: "parts",
    title: "分部积分",
    mode: "definite",
    expression: "x*exp(x)",
    lower: "0",
    upper: "1",
    statement: rawMath`\int_0^1 xe^x\,dx`,
  },
  pConverges: {
    id: "pConverges",
    title: "p 型收敛",
    mode: "improper",
    expression: "1/x^2",
    lower: "1",
    upper: "oo",
    statement: rawMath`\int_1^\infty \frac{1}{x^2}\,dx`,
  },
  pDiverges: {
    id: "pDiverges",
    title: "调和尾部发散",
    mode: "improper",
    expression: "1/x",
    lower: "1",
    upper: "oo",
    statement: rawMath`\int_1^\infty \frac{1}{x}\,dx`,
  },
  endpoint: {
    id: "endpoint",
    title: "端点奇异但收敛",
    mode: "improper",
    expression: "1/sqrt(x)",
    lower: "0",
    upper: "1",
    statement: rawMath`\int_0^1 \frac{1}{\sqrt{x}}\,dx`,
  },
  doubleXY: {
    id: "doubleXY",
    title: "二重积分体积",
    mode: "double",
    expression: "x*y",
    xLower: "0",
    xUpper: "1",
    yLower: "0",
    yUpper: "1",
    statement: rawMath`\int_0^1\int_0^1 xy\,dy\,dx`,
  },
  paraboloid: {
    id: "paraboloid",
    title: "抛物面体积",
    mode: "double",
    expression: "x^2+y^2",
    xLower: "-1",
    xUpper: "1",
    yLower: "-1",
    yUpper: "1",
    statement: rawMath`\int_{-1}^1\int_{-1}^1(x^2+y^2)\,dy\,dx`,
  },
  gaussian: {
    id: "gaussian",
    title: "高斯曲面窗口",
    mode: "double",
    expression: "exp(-(x^2+y^2))",
    xLower: "-2",
    xUpper: "2",
    yLower: "-2",
    yUpper: "2",
    statement: rawMath`\int_{-2}^2\int_{-2}^2 e^{-(x^2+y^2)}\,dy\,dx`,
  },
  polarCircle: {
    id: "polarCircle",
    title: "极坐标圆面积",
    mode: "polar_area",
    expression: "1",
    innerExpression: "0",
    thetaLower: "0",
    thetaUpper: "2*pi",
    statement: rawMath`\frac12\int_0^{2\pi}1^2\,d\theta`,
  },
  polarRose: {
    id: "polarRose",
    title: "玫瑰线单瓣",
    mode: "polar_area",
    expression: "2*sin(3*theta)",
    innerExpression: "0",
    thetaLower: "0",
    thetaUpper: "pi/3",
    statement: rawMath`\frac12\int_0^{\pi/3}(2\sin 3\theta)^2\,d\theta`,
  },
  polarDoubleUnit: {
    id: "polarDoubleUnit",
    title: "极坐标二重积分",
    mode: "polar_double",
    expression: "1",
    rLower: "0",
    rUpper: "1",
    thetaLower: "0",
    thetaUpper: "2*pi",
    statement: rawMath`\int_0^{2\pi}\int_0^1 r\,dr\,d\theta`,
  },
};

const lessons = [
  {
    id: "zero",
    title: "0. 积分到底在做什么",
    preview: "powerArea",
    cards: [
      {
        title: "从“小矩形相加”开始",
        body: [
          "假设你想知道曲线下面有多少面积。最朴素的方法不是马上写公式，而是把横轴切成很多小段。",
          "每一小段都有一个宽度，记作 \\(\\Delta x\\)。在这段上取一个高度 \\(f(x_i^*)\\)，就得到一个小矩形面积 \\(f(x_i^*)\\Delta x\\)。",
          "把所有小矩形加起来，会得到一个粗略面积；切得越细，结果越接近真正面积。积分符号 \\(\\int\\) 就是在表达“无限多小量相加”。",
        ],
        formula: rawMath`\[\int_a^b f(x)\,dx=\lim_{n\to\infty}\sum_{i=1}^{n}f(x_i^*)\Delta x\]`,
        symbols: [
          "\\(a,b\\)：从哪里开始加，到哪里结束。",
          "\\(f(x)\\)：每个位置的高度。",
          "\\(dx\\)：非常小的一段宽度。",
          "\\(\\int\\)：把所有小面积加起来。",
        ],
        examples: ["powerArea"],
      },
      {
        title: "面积、净面积和累积量",
        body: [
          "如果曲线在 x 轴上方，积分值是正的；如果在下方，积分值是负的。所以积分更准确地说是“有向面积”。",
          "在物理里，如果 \\(f(x)\\) 是速度，积分就不是面积题，而是在累积位移；如果是密度，积分就在累积质量。",
        ],
        formula: rawMath`\[\text{净变化量}=\int_a^b \text{变化率}\,dx\]`,
        symbols: ["变化率表示“每单位 x 改变多少”。积分把这些小变化累加成总变化。"],
        examples: ["sinArea"],
      },
    ],
  },
  {
    id: "basic",
    title: "1. 常积分和基本技巧",
    preview: "uSub",
    cards: [
      {
        title: "微积分基本定理",
        body: [
          "如果你找到一个函数 \\(F(x)\\)，它求导后正好等于 \\(f(x)\\)，那么 \\(F\\) 就叫 \\(f\\) 的一个原函数。",
          "定积分可以不用真的把无数小矩形相加，而是直接计算 \\(F(b)-F(a)\\)。这就是微积分基本定理。",
        ],
        formula: rawMath`\[\int_a^b f(x)\,dx=F(b)-F(a),\quad F'(x)=f(x)\]`,
        symbols: ["\\(F'(x)=f(x)\\)：F 的斜率等于 f。", "\\(F(b)-F(a)\\)：总累积量。"],
        examples: ["powerArea", "sinArea"],
      },
      {
        title: "换元法：把复杂里面那层拿出来",
        body: [
          "看到 \\(\\cos(x^2)\\)、\\(e^{x^2}\\) 这类复合函数时，要问：里面的 \\(x^2\\) 的导数有没有同时出现？",
          "如果出现了，比如 \\(2x\\cos(x^2)\\)，就令 \\(u=x^2\\)，题目会立刻变简单。",
        ],
        formula: rawMath`\[\int f(g(x))g'(x)\,dx=\int f(u)\,du\]`,
        symbols: ["\\(u=g(x)\\)：给复杂内层换一个名字。", "\\(du=g'(x)dx\\)：同步替换微小变化。"],
        examples: ["uSub"],
      },
      {
        title: "分部积分：乘积求导的反向",
        body: [
          "当题目里有两个不同类型函数相乘，比如 \\(xe^x\\)、\\(x\\sin x\\)、\\(\\ln x\\)，常常考虑分部积分。",
          "诀窍是把会变简单的部分选作 \\(u\\)，比如 \\(x\\) 求导后变成 1。",
        ],
        formula: rawMath`\[\int u\,dv=uv-\int v\,du\]`,
        symbols: ["\\(u\\)：通常选求导后更简单的部分。", "\\(dv\\)：剩下能直接积分的部分。"],
        examples: ["parts"],
      },
    ],
  },
  {
    id: "improper",
    title: "2. 反常积分",
    preview: "pConverges",
    cards: [
      {
        title: "无穷不是数字，要先写成极限",
        body: [
          "像 \\(\\int_1^\\infty\\frac1{x^2}dx\\) 这样的题，上限不是普通数字，不能直接代入。",
          "正确做法是先把 \\(\\infty\\) 换成一个很大的 \\(b\\)，算完 \\(\\int_1^b\\)，再让 \\(b\\to\\infty\\)。",
        ],
        formula: rawMath`\[\int_a^\infty f(x)\,dx=\lim_{b\to\infty}\int_a^b f(x)\,dx\]`,
        symbols: ["如果极限是有限数，就收敛。", "如果极限变成无穷或不存在，就发散。"],
        examples: ["pConverges", "pDiverges"],
      },
      {
        title: "函数无限高，也可能面积有限",
        body: [
          "\\(1/\\sqrt{x}\\) 在 \\(x=0\\) 附近会冲向无穷，但它冲得不够快，所以总面积仍然有限。",
          "这类题要用单侧极限：从右边一点点靠近奇点，而不是直接把 0 代进去。",
        ],
        formula: rawMath`\[\int_0^1 \frac1{\sqrt{x}}dx=\lim_{a\to0^+}\int_a^1 x^{-1/2}dx\]`,
        symbols: ["\\(a\\to0^+\\)：a 从 0 的右侧靠近 0。", "奇点：函数无定义或无界的位置。"],
        examples: ["endpoint"],
      },
    ],
  },
  {
    id: "double",
    title: "3. 二重积分和体积",
    preview: "paraboloid",
    cards: [
      {
        title: "从面积升级到体积",
        body: [
          "一元积分把一条线上的高度累积成面积；二重积分把一个平面区域上的高度 \\(z=f(x,y)\\) 累积成体积。",
          "在图中，底面是 \\(x-y\\) 区域，曲面的高度是 \\(z\\)。曲面越高、底面越大，体积越大。",
        ],
        formula: rawMath`\[\iint_R f(x,y)\,dA\approx \sum f(x_i,y_j)\Delta A\]`,
        symbols: ["\\(R\\)：平面上的积分区域。", "\\(dA\\)：非常小的一块面积。", "\\(z=f(x,y)\\)：每个底面点上方的高度。"],
        examples: ["doubleXY", "paraboloid"],
      },
      {
        title: "矩形区域可以一层一层算",
        body: [
          "当前工具先支持矩形区域。你可以先固定 \\(x\\)，沿着 \\(y\\) 方向积分；再让 \\(x\\) 从左到右扫过去。",
          "如果函数能拆成 \\(p(x)q(y)\\)，并且区域是矩形，就可以把二重积分拆成两个一元积分的乘积。",
        ],
        formula: rawMath`\[\int_a^b\int_c^d p(x)q(y)\,dy\,dx=\left(\int_a^b p(x)dx\right)\left(\int_c^d q(y)dy\right)\]`,
        symbols: ["内层积分先处理一个方向。", "外层积分把所有切片继续累加。"],
        examples: ["gaussian"],
      },
    ],
  },
  {
    id: "polar",
    title: "4. 极坐标积分",
    preview: "polarRose",
    cards: [
      {
        title: "从直角坐标换到极坐标",
        body: [
          "极坐标不用 \\(x,y\\) 直接描述点，而是用半径 \\(r\\) 和角度 \\(\\theta\\)。它们和直角坐标的关系是 \\(x=r\\cos\\theta\\)、\\(y=r\\sin\\theta\\)。",
          "当图形天然围绕原点旋转、像圆、玫瑰线、心形线或扇形时，用极坐标通常比直角坐标更直接。",
        ],
        formula: rawMath`\[x=r\cos\theta,\qquad y=r\sin\theta\]`,
        symbols: ["\\(r\\)：点到原点的距离。", "\\(\\theta\\)：从正 x 轴转到这个点的角度。"],
        examples: ["polarCircle"],
      },
      {
        title: "极坐标面积为什么有二分之一",
        body: [
          "当角度只增加一点点 \\(d\\theta\\) 时，曲线 \\(r=f(\\theta)\\) 扫过的是很薄的扇形。扇形面积近似是 \\(\\frac12r^2d\\theta\\)。",
          "如果区域夹在内半径和外半径之间，就用外半径平方减内半径平方。",
        ],
        formula: rawMath`\[A=\frac12\int_\alpha^\beta\left(r_{out}(\theta)^2-r_{in}(\theta)^2\right)d\theta\]`,
        symbols: ["\\(r_{out}\\)：外侧曲线。", "\\(r_{in}\\)：内侧曲线，没有内曲线时就是 0。"],
        examples: ["polarRose"],
      },
      {
        title: "极坐标二重积分必须乘 r",
        body: [
          "二重积分里的小面积块 \\(dA\\) 换成极坐标后，不是简单的 \\(drd\\theta\\)，而是 \\(rdrd\\theta\\)。",
          "这个额外的 \\(r\\) 来自坐标变换：离原点越远，同样的角度宽度扫出来的弧越长。",
        ],
        formula: rawMath`\[\iint_R f(x,y)\,dA=\int_\alpha^\beta\int_{r_{in}}^{r_{out}} f(r,\theta)\,r\,dr\,d\theta\]`,
        symbols: ["\\(r\\,dr\\,d\\theta\\)：极坐标面积微元。", "\\(f(r,\\theta)\\)：用极坐标写出的高度或密度。"],
        examples: ["polarDoubleUnit"],
      },
    ],
  },
];

function loadPracticeSignatures() {
  try {
    const raw = window.localStorage?.getItem(PRACTICE_SIGNATURE_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string").slice(0, 300) : [];
  } catch {
    return [];
  }
}

function rememberPracticeSignature(signature) {
  if (!signature) return;
  try {
    const signatures = loadPracticeSignatures().filter((item) => item !== signature);
    signatures.unshift(signature);
    window.localStorage?.setItem(PRACTICE_SIGNATURE_STORAGE_KEY, JSON.stringify(signatures.slice(0, 300)));
  } catch {
    // Local storage is optional; generation still works without persistent de-duplication.
  }
}

function setSection(section) {
  for (const tab of elements.modeTabs) {
    tab.classList.toggle("active", tab.dataset.section === section);
  }
  for (const [key, node] of Object.entries(elements.sections)) {
    if (key !== "tool") {
      node.classList.toggle("active", key === section);
    }
  }
  elements.sections.tool.classList.toggle("tool-only", section === "tool");
  if (section === "tool") {
    elements.sections.tool.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function setMode(mode, shouldCalculate = true) {
  currentMode = mode;
  const isDouble = mode === "double";
  const isPolarArea = mode === "polar_area";
  const isPolarDouble = mode === "polar_double";
  const isPolar = isPolarArea || isPolarDouble;
  for (const button of elements.modeButtons) {
    button.classList.toggle("active", button.dataset.mode === mode);
  }
  elements.boundsGrid.style.display = mode === "indefinite" || isDouble || isPolar ? "none" : "grid";
  elements.doubleBoundsGrid.style.display = isDouble ? "grid" : "none";
  elements.polarBoundsGrid.style.display = isPolar ? "grid" : "none";
  for (const node of elements.polarAreaFields) node.style.display = isPolarArea ? "grid" : "none";
  for (const node of elements.polarDoubleFields) node.style.display = isPolarDouble ? "grid" : "none";
  elements.expressionLabel.textContent = isDouble ? "f(x, y)" : isPolarArea ? "r_out(theta)" : isPolarDouble ? "f(r, theta)" : "f(x)";
  if (isPolarArea && elements.expression.value === "x^2") {
    elements.expression.value = "2*sin(theta)";
  } else if (isPolarDouble && elements.expression.value === "x^2") {
    elements.expression.value = "1";
  }
  if (shouldCalculate) {
    calculate();
  }
}

function insertAtCursor(input, value) {
  input.focus();
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? input.value.length;
  input.value = input.value.slice(0, start) + value + input.value.slice(end);
  const cursor = start + (value.endsWith("()") ? value.length - 1 : value.length);
  input.setSelectionRange(cursor, cursor);
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  if (Math.abs(numeric) >= 1e6 || (Math.abs(numeric) > 0 && Math.abs(numeric) < 1e-5)) {
    return numeric.toExponential(8);
  }
  return numeric.toPrecision(11).replace(/\.?0+$/, "");
}

function requestPayload() {
  return {
    mode: currentMode,
    expression: elements.expression.value,
    lower: elements.lower.value,
    upper: elements.upper.value,
    xLower: elements.xLower.value,
    xUpper: elements.xUpper.value,
    yLower: elements.yLower.value,
    yUpper: elements.yUpper.value,
    innerExpression: elements.innerExpression.value,
    rLower: elements.rLower.value,
    rUpper: elements.rUpper.value,
    thetaLower: elements.thetaLower.value,
    thetaUpper: elements.thetaUpper.value,
    epsilon: 1e-8,
  };
}

function payloadFromProblem(item) {
  return {
    mode: item.mode,
    expression: item.expression,
    lower: item.lower ?? "0",
    upper: item.upper ?? "1",
    xLower: item.xLower ?? "0",
    xUpper: item.xUpper ?? "1",
    yLower: item.yLower ?? "0",
    yUpper: item.yUpper ?? "1",
    innerExpression: item.innerExpression ?? "0",
    rLower: item.rLower ?? "0",
    rUpper: item.rUpper ?? "1",
    thetaLower: item.thetaLower ?? "0",
    thetaUpper: item.thetaUpper ?? "2*pi",
    epsilon: 1e-8,
  };
}

async function solve(payload) {
  const response = await fetch(apiUrl("/api/solve"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!data.ok) throw new Error(data.error || "计算失败");
  return data;
}

async function calculate() {
  elements.calculate.disabled = true;
  elements.statusLine.textContent = "计算中";
  setMessages([]);
  try {
    const payload = requestPayload();
    const response = await fetch(apiUrl("/api/integrate"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!result.ok) throw new Error(result.error || "计算失败");
    renderResult(result);
    elements.statusLine.textContent = "完成";
  } catch (error) {
    clearResult();
    setMessages([error.message], true);
    elements.statusLine.textContent = "输入需要调整";
  } finally {
    elements.calculate.disabled = false;
  }
}

function setMessages(messages, isError = false) {
  elements.messages.innerHTML = "";
  const list = Array.isArray(messages) ? messages.filter(Boolean) : [];
  elements.messages.classList.toggle("active", list.length > 0);
  for (const message of list) {
    const item = document.createElement("div");
    item.className = `message${isError ? " error" : ""}`;
    item.textContent = message;
    elements.messages.appendChild(item);
  }
}

function clearResult() {
  elements.exactResult.textContent = "-";
  elements.numericResult.textContent = "-";
  elements.antiderivativeResult.textContent = "-";
  elements.errorResult.textContent = "-";
  elements.statusResult.textContent = "-";
  elements.numericChip.textContent = "-";
  elements.engineBadge.textContent = "待机";
}

function renderResult(payload) {
  elements.plotTitle.textContent =
    payload.mode === "double"
      ? `z = ${payload.expression}`
      : payload.mode === "polar_area"
        ? `r = ${payload.polar?.outer || payload.expression}`
        : payload.mode === "polar_double"
          ? `z = ${payload.expression}, dA = r dr dθ`
          : `f(x) = ${payload.expression}`;
  const exact = payload.exact?.available ? payload.exact.text : "-";
  const numeric = payload.numeric?.ok !== false ? formatNumber(payload.numeric?.value) : "-";
  const error = payload.numeric?.ok !== false ? formatNumber(payload.numeric?.estimated_error) : "-";
  elements.exactResult.textContent = exact;
  elements.numericResult.textContent = numeric;
  elements.errorResult.textContent = error;
  elements.numericChip.textContent = payload.mode === "improper" ? statusLabel(payload.improper?.status) : numeric;

  if (payload.mode === "polar_area") {
    elements.statusResult.textContent = "极坐标面积";
    elements.engineBadge.textContent = payload.numeric?.engine === "cpp" ? "C++ polar" : "SciPy polar";
    elements.fourthResultLabel.textContent = "极坐标区域";
    elements.antiderivativeResult.textContent = payload.polar?.region_text || "r(theta)";
  } else if (payload.mode === "polar_double") {
    elements.statusResult.textContent = "极坐标二重积分";
    elements.engineBadge.textContent = payload.numeric?.engine === "cpp" ? "C++ polar 2D" : "SciPy polar";
    elements.fourthResultLabel.textContent = "极坐标区域";
    elements.antiderivativeResult.textContent = payload.polar?.region_text || "r-theta region";
  } else if (payload.mode === "double") {
    elements.statusResult.textContent = "二重积分";
    elements.engineBadge.textContent = payload.numeric?.engine === "cpp" ? "C++ 2D" : "SciPy 2D";
    elements.fourthResultLabel.textContent = "区域";
    elements.antiderivativeResult.textContent = payload.double?.region_text || "矩形区域";
  } else if (payload.mode === "improper") {
    elements.statusResult.textContent = statusLabel(payload.improper?.status);
    elements.engineBadge.textContent = payload.improper?.status === "divergent" ? "判定" : "SciPy";
    elements.fourthResultLabel.textContent = "原函数";
    elements.antiderivativeResult.textContent = payload.antiderivative?.available ? `${payload.antiderivative.text} + C` : "未得到闭式";
  } else if (payload.mode === "indefinite") {
    elements.statusResult.textContent = "不定积分";
    elements.engineBadge.textContent = "SymPy";
    elements.exactResult.textContent = "-";
    elements.numericResult.textContent = "-";
    elements.errorResult.textContent = "-";
    elements.numericChip.textContent = "F(x)";
    elements.fourthResultLabel.textContent = "原函数";
    elements.antiderivativeResult.textContent = payload.antiderivative?.available ? `${payload.antiderivative.text} + C` : "未得到闭式";
  } else {
    elements.statusResult.textContent = "有限区间";
    elements.engineBadge.textContent = payload.numeric?.engine === "cpp" ? "C++" : "SciPy";
    elements.fourthResultLabel.textContent = "原函数";
    elements.antiderivativeResult.textContent = payload.antiderivative?.available ? `${payload.antiderivative.text} + C` : "未得到闭式";
  }

  const messages = [...(payload.warnings || [])];
  if (payload.improper?.reason) messages.unshift(payload.improper.reason);
  setMessages(messages);
  lastPlot = payload.plot;
  drawPlot(lastPlot);
}

function statusLabel(status) {
  return { convergent: "收敛", divergent: "发散", unknown: "待判定" }[status] || "-";
}

function renderSolution(containerTitle, containerBody, payload, title = "解答") {
  containerTitle.textContent = title;
  const steps = (payload.steps || []).map((step) => `<li>${step}</li>`).join("");
  const algebra = payload.algebra_steps || {};
  const algebraNotes = (algebra.notes || []).map((note) => `<li>${note}</li>`).join("");
  const algebraHtml = algebra.available
    ? `
      <div class="formula-box algebra-box">
        <p><strong>代数推导：</strong><span class="tag">${algebraLabel(algebra.explainability)}</span></p>
        \\[${algebra.latex || ""}\\]
        ${algebraNotes ? `<ul class="symbol-list">${algebraNotes}</ul>` : ""}
      </div>
    `
    : algebra.reason
      ? `<div class="message">${algebra.reason}</div>`
      : "";
  containerBody.innerHTML = `
    <div class="formula-box">\\[${payload.statement_latex || ""}\\]</div>
    <p><strong>推荐方法：</strong>${payload.method || "符号计算 + 数值核验"}</p>
    <p>${payload.method_explanation || ""}</p>
    ${algebraHtml}
    <ol>${steps}</ol>
    <div class="solution-result">答案：\\(${payload.result_latex || "-"}\\)</div>
  `;
  typesetMath();
}

function algebraLabel(value) {
  return { full: "完整推导", partial: "部分推导", "result-only": "结果校验" }[value] || value || "推导";
}

function applyProblem(item) {
  elements.expression.value = item.expression;
  if (item.lower !== undefined) elements.lower.value = item.lower;
  if (item.upper !== undefined) elements.upper.value = item.upper;
  if (item.xLower !== undefined) elements.xLower.value = item.xLower;
  if (item.xUpper !== undefined) elements.xUpper.value = item.xUpper;
  if (item.yLower !== undefined) elements.yLower.value = item.yLower;
  if (item.yUpper !== undefined) elements.yUpper.value = item.yUpper;
  if (item.innerExpression !== undefined) elements.innerExpression.value = item.innerExpression;
  if (item.rLower !== undefined) elements.rLower.value = item.rLower;
  if (item.rUpper !== undefined) elements.rUpper.value = item.rUpper;
  if (item.thetaLower !== undefined) elements.thetaLower.value = item.thetaLower;
  if (item.thetaUpper !== undefined) elements.thetaUpper.value = item.thetaUpper;
  setMode(item.mode, false);
}

async function solveProblem(item, titleNode, bodyNode, scroll = false) {
  applyProblem(item);
  const result = await solve(payloadFromProblem(item));
  renderResult(result);
  renderSolution(titleNode, bodyNode, result, item.title);
  if (scroll) elements.sections.tool.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderCommonExamples() {
  const ids = ["powerArea", "sinArea", "pConverges", "endpoint", "doubleXY", "paraboloid", "polarCircle", "polarRose"];
  elements.examples.innerHTML = ids
    .map((id) => {
      const item = cannedProblems[id];
      return `<button type="button" data-example="${id}">${item.title}</button>`;
    })
    .join("");
}

function renderPalettes() {
  const html = quickTemplates.map((item) => `<button type="button" data-insert="${item.insert}">${item.label}</button>`).join("");
  elements.palette.innerHTML = html;
  elements.qaPalette.innerHTML = html;
}

function renderLessons() {
  elements.lessonTabs.innerHTML = lessons
    .map((lesson) => `<button class="guide-tab${lesson.id === currentLesson ? " active" : ""}" data-lesson="${lesson.id}" type="button">${lesson.title}</button>`)
    .join("");
  const lesson = lessons.find((item) => item.id === currentLesson) || lessons[0];
  elements.lessonContent.innerHTML = lesson.cards
    .map((card) => {
      const symbols = card.symbols.map((s) => `<li>${s}</li>`).join("");
      const examples = card.examples
        .map((id) => {
          const item = cannedProblems[id];
          return `<button class="mini-action" type="button" data-lesson-problem="${id}">${item.title}</button>`;
        })
        .join("");
      return `
        <section class="lesson-card">
          <div class="lesson-main">
            <div>
              <h3>${card.title}</h3>
              ${card.body.map((p) => `<p>${p}</p>`).join("")}
              <div class="formula-box">${card.formula}</div>
              <ul class="symbol-list">${symbols}</ul>
              <div class="example-actions">${examples}</div>
            </div>
            <canvas class="mini-visual" data-preview="${lesson.preview}" width="360" height="220"></canvas>
          </div>
        </section>
      `;
    })
    .join("");
  typesetMath();
  drawMiniVisuals();
}

async function drawMiniVisuals() {
  for (const canvas of $$(".mini-visual")) {
    const item = cannedProblems[canvas.dataset.preview];
    if (!item) continue;
    try {
      const payload = await solve(payloadFromProblem(item));
      drawMiniPlot(canvas, payload.plot);
    } catch {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }
}

function renderPracticeProblem(item, result, meta = {}) {
  const concepts = (meta.concepts || item.concepts || []).slice(0, 3);
  const conceptTags = concepts.map((concept) => `<span class="tag">${concept}</span>`).join("");
  const seedTag = meta.seed ? `<span class="tag">种子 ${String(meta.seed).slice(0, 8)}</span>` : "";
  const capacityTag = meta.capacity_estimate ? `<span class="tag">候选约 ${formatNumber(meta.capacity_estimate)}</span>` : "";
  elements.practiceProblem.innerHTML = `
    <strong>${item.title}</strong>
    <span class="tag">${kindLabel(item.mode)} · ${levelLabel(item.level || elements.practiceLevel.value)}</span>
    ${conceptTags}
    ${seedTag}
    ${capacityTag}
    <p class="practice-target">${item.target || "根据题目结构选择可靠方法，并用计算结果校验。"}</p>
    <div class="formula-box">\\[${item.statement || result.statement_latex}\\]</div>
    <div class="example-actions">
      <button class="mini-action" type="button" id="practiceVisualize">查看上方图像</button>
      <button class="mini-action" type="button" id="practiceRegenerate">再来一题</button>
    </div>
  `;
  $("#practiceVisualize")?.addEventListener("click", () => elements.sections.tool.scrollIntoView({ behavior: "smooth", block: "start" }));
  $("#practiceRegenerate")?.addEventListener("click", generatePractice);
  typesetMath();
}

async function generatePractice() {
  const kind = elements.practiceKind.value;
  const level = elements.practiceLevel.value;
  elements.practiceSolutionTitle.textContent = "正在生成";
  elements.practiceSolutionBody.innerHTML = "<p>正在从后端随机生成题目、去重并校验解答...</p>";
  elements.generatePractice.disabled = true;
  try {
    const response = await fetch(apiUrl("/api/practice/generate"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind,
        level,
        avoid_signatures: loadPracticeSignatures(),
        max_attempts: 160,
      }),
    });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "题目生成失败");
    rememberPracticeSignature(data.signature);
    const item = data.problem;
    const result = data.solution;
    lastPracticeProblem = item;
    applyProblem(item);
    renderResult(result);
    renderPracticeProblem(item, result, data);
    renderSolution(elements.practiceSolutionTitle, elements.practiceSolutionBody, result, item.title);
  } catch (error) {
    elements.practiceSolutionTitle.textContent = "生成失败";
    elements.practiceSolutionBody.innerHTML = `<div class="message error">${error.message}</div>`;
  } finally {
    elements.generatePractice.disabled = false;
  }
}

function kindLabel(kind) {
  return {
    definite: "定积分",
    indefinite: "不定积分",
    improper: "反常积分",
    double: "二重积分",
    polar: "极坐标积分",
    polar_area: "极坐标面积",
    polar_double: "极坐标二重积分",
  }[kind] || kind;
}

function levelLabel(level) {
  return { easy: "简单", ap: "AP", advanced: "高等技巧", mit: "MIT/挑战" }[level] || level;
}

function qaPayload() {
  if (elements.qaRaw.value.trim()) {
    return {
      raw: elements.qaRaw.value,
      mode: elements.qaMode.value,
      expression: elements.qaExpression.value,
      lower: elements.qaLower.value,
      upper: elements.qaUpper.value,
      xLower: elements.qaXLower.value,
      xUpper: elements.qaXUpper.value,
      yLower: elements.qaYLower.value,
      yUpper: elements.qaYUpper.value,
      innerExpression: elements.qaInnerExpression.value,
      rLower: elements.qaRLower.value,
      rUpper: elements.qaRUpper.value,
      thetaLower: elements.qaThetaLower.value,
      thetaUpper: elements.qaThetaUpper.value,
    };
  }
  return {
    mode: elements.qaMode.value,
    expression: elements.qaExpression.value,
    lower: elements.qaLower.value,
    upper: elements.qaUpper.value,
    xLower: elements.qaXLower.value,
    xUpper: elements.qaXUpper.value,
    yLower: elements.qaYLower.value,
    yUpper: elements.qaYUpper.value,
    innerExpression: elements.qaInnerExpression.value,
    rLower: elements.qaRLower.value,
    rUpper: elements.qaRUpper.value,
    thetaLower: elements.qaThetaLower.value,
    thetaUpper: elements.qaThetaUpper.value,
  };
}

async function askQuestion() {
  elements.qaSolutionTitle.textContent = "正在解答";
  elements.qaSolutionBody.innerHTML = "<p>正在解析题目、计算并生成步骤...</p>";
  try {
    const result = await solve(qaPayload());
    applyProblem({
      mode: result.mode,
      expression: result.expression,
      lower: result.bounds?.lower,
      upper: result.bounds?.upper,
      xLower: result.bounds?.x_lower,
      xUpper: result.bounds?.x_upper,
      yLower: result.bounds?.y_lower,
      yUpper: result.bounds?.y_upper,
      innerExpression: result.polar?.inner,
      rLower: result.bounds?.r_lower,
      rUpper: result.bounds?.r_upper,
      thetaLower: result.bounds?.theta_lower,
      thetaUpper: result.bounds?.theta_upper,
    });
    renderResult(result);
    renderSolution(elements.qaSolutionTitle, elements.qaSolutionBody, result, "问答解答");
  } catch (error) {
    elements.qaSolutionTitle.textContent = "无法解答";
    elements.qaSolutionBody.innerHTML = `<div class="message error">${error.message}</div>`;
  }
}

function updateQaBounds() {
  const isDouble = elements.qaMode.value === "double";
  const isPolarArea = elements.qaMode.value === "polar_area";
  const isPolarDouble = elements.qaMode.value === "polar_double";
  const isPolar = isPolarArea || isPolarDouble;
  elements.qaBounds.style.display = elements.qaMode.value === "indefinite" || isDouble || isPolar ? "none" : "grid";
  elements.qaDoubleBounds.style.display = isDouble ? "grid" : "none";
  elements.qaPolarBounds.style.display = isPolar ? "grid" : "none";
  for (const node of elements.qaPolarAreaFields) node.style.display = isPolarArea ? "grid" : "none";
  for (const node of elements.qaPolarDoubleFields) node.style.display = isPolarDouble ? "grid" : "none";
  elements.qaExpressionLabel.textContent = isPolarArea ? "外半径 r_out(theta)" : isPolarDouble ? "函数 f(r, theta)" : "函数表达式";
  if (isPolarArea && elements.qaExpression.value === "x^2") elements.qaExpression.value = "2*sin(theta)";
  if (isPolarDouble && elements.qaExpression.value === "x^2") elements.qaExpression.value = "1";
}

function typesetMath() {
  if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise().catch(() => {});
}

function resizeCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const width = Math.max(320, Math.floor(rect.width * dpr));
  const height = Math.max(260, Math.floor(rect.height * dpr));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { width: rect.width, height: rect.height, ctx };
}

function drawPlot(plot) {
  const canvas = elements.plot;
  const { width, height, ctx } = resizeCanvas(canvas);
  ctx.clearRect(0, 0, width, height);
  if (plot?.kind === "surface") {
    drawSurfacePlot(ctx, width, height, plot);
    return;
  }
  if (plot?.kind === "polar_area" || plot?.kind === "polar_surface") {
    drawPolarPlot(ctx, width, height, plot);
    return;
  }
  drawCurvePlot(ctx, width, height, plot);
}

function drawPolarPlot(ctx, width, height, plot) {
  const cx = width * 0.5;
  const cy = height * 0.5;
  const radius = Math.max(40, Math.min(width, height) * 0.39);
  const rMax = Math.max(1e-9, plot.rMax || 1);
  const toPx = (point) => {
    if (!point || point.x === null || point.y === null) return null;
    return {
      x: cx + (point.x / rMax) * radius,
      y: cy - (point.y / rMax) * radius,
    };
  };

  ctx.save();
  ctx.fillStyle = "#fbfdfd";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#dbe5e8";
  ctx.lineWidth = 1;
  for (let i = 1; i <= 4; i += 1) {
    ctx.beginPath();
    ctx.arc(cx, cy, (radius * i) / 4, 0, Math.PI * 2);
    ctx.stroke();
  }
  for (let i = 0; i < 12; i += 1) {
    const angle = (Math.PI * 2 * i) / 12;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(angle) * radius, cy - Math.sin(angle) * radius);
    ctx.stroke();
  }
  ctx.strokeStyle = "#8fa1a8";
  ctx.beginPath();
  ctx.moveTo(cx - radius - 12, cy);
  ctx.lineTo(cx + radius + 12, cy);
  ctx.moveTo(cx, cy + radius + 12);
  ctx.lineTo(cx, cy - radius - 12);
  ctx.stroke();

  const outer = (plot.outer || []).map(toPx).filter(Boolean);
  const inner = (plot.inner || []).map(toPx).filter(Boolean);
  if (outer.length > 2) {
    ctx.beginPath();
    ctx.moveTo(outer[0].x, outer[0].y);
    for (const point of outer.slice(1)) ctx.lineTo(point.x, point.y);
    if (inner.length > 2) {
      for (const point of [...inner].reverse()) ctx.lineTo(point.x, point.y);
    } else {
      ctx.lineTo(cx, cy);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(11, 122, 117, 0.18)";
    ctx.fill();
  }

  if (plot.kind === "polar_surface" && Array.isArray(plot.rows)) {
    const zMin = plot.zMin ?? -1;
    const zMax = plot.zMax ?? 1;
    for (const row of plot.rows) {
      for (const sample of row) {
        const p = toPx(sample);
        if (!p || sample.z === null || sample.z === undefined) continue;
        const zRatio = Math.max(0, Math.min(1, (sample.z - zMin) / Math.max(1e-9, zMax - zMin)));
        ctx.fillStyle = `rgba(${Math.round(26 + zRatio * 190)}, ${Math.round(110 + zRatio * 60)}, 150, 0.32)`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2.2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  drawPolarCurve(ctx, outer, "#0b7a75", 2.4);
  drawPolarCurve(ctx, inner, "#a65f00", 1.8);

  ctx.fillStyle = "#42545b";
  ctx.font = "12px Cascadia Mono, Consolas, monospace";
  ctx.fillText("0", cx + 6, cy - 6);
  ctx.fillText(`r≈${formatNumber(rMax)}`, cx + radius - 44, cy - 8);
  ctx.fillText(`θ: ${formatNumber(plot.thetaMin)}..${formatNumber(plot.thetaMax)}`, 16, height - 18);
  ctx.restore();
}

function drawPolarCurve(ctx, points, color, width) {
  if (!points || points.length < 2) return;
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (const point of points.slice(1)) ctx.lineTo(point.x, point.y);
  ctx.stroke();
  ctx.restore();
}

function drawCurvePlot(ctx, width, height, plot) {
  if (!plot?.points) return;
  const margin = { left: 54, right: 18, top: 22, bottom: 42 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const xMin = plot.xMin;
  const xMax = plot.xMax;
  const yMin = Math.min(plot.yMin, 0);
  const yMax = Math.max(plot.yMax, 0);
  const xToPx = (value) => margin.left + ((value - xMin) / (xMax - xMin)) * innerWidth;
  const yToPx = (value) => margin.top + (1 - (value - yMin) / (yMax - yMin)) * innerHeight;
  drawGrid(ctx, margin, innerWidth, innerHeight, xToPx, yToPx, xMin, xMax, yMin, yMax);
  drawShade(ctx, plot, xToPx, yToPx);
  drawCurve(ctx, plot.points, xToPx, yToPx);
  drawBounds(ctx, plot, xToPx, margin, innerHeight);
}

function drawGrid(ctx, margin, innerWidth, innerHeight, xToPx, yToPx, xMin, xMax, yMin, yMax) {
  ctx.save();
  ctx.strokeStyle = "#e4ebee";
  ctx.fillStyle = "#61717a";
  ctx.font = "12px Cascadia Mono, Consolas, monospace";
  for (let i = 0; i <= 8; i += 1) {
    const value = xMin + ((xMax - xMin) * i) / 8;
    const px = xToPx(value);
    ctx.beginPath();
    ctx.moveTo(px, margin.top);
    ctx.lineTo(px, margin.top + innerHeight);
    ctx.stroke();
    ctx.fillText(formatTick(value), px - 16, margin.top + innerHeight + 25);
  }
  for (let i = 0; i <= 6; i += 1) {
    const value = yMin + ((yMax - yMin) * i) / 6;
    const py = yToPx(value);
    ctx.beginPath();
    ctx.moveTo(margin.left, py);
    ctx.lineTo(margin.left + innerWidth, py);
    ctx.stroke();
    ctx.fillText(formatTick(value), 8, py + 4);
  }
  ctx.strokeStyle = "#80909a";
  if (xMin <= 0 && xMax >= 0) {
    const x0 = xToPx(0);
    ctx.beginPath();
    ctx.moveTo(x0, margin.top);
    ctx.lineTo(x0, margin.top + innerHeight);
    ctx.stroke();
  }
  if (yMin <= 0 && yMax >= 0) {
    const y0 = yToPx(0);
    ctx.beginPath();
    ctx.moveTo(margin.left, y0);
    ctx.lineTo(margin.left + innerWidth, y0);
    ctx.stroke();
  }
  ctx.restore();
}

function drawShade(ctx, plot, xToPx, yToPx) {
  if (!Number.isFinite(plot.shadeMin) || !Number.isFinite(plot.shadeMax) || plot.shadeMin === plot.shadeMax) return;
  const min = Math.min(plot.shadeMin, plot.shadeMax);
  const max = Math.max(plot.shadeMin, plot.shadeMax);
  const shaded = plot.points.filter((point) => point.y !== null && point.x >= min && point.x <= max);
  if (shaded.length < 2) return;
  const y0 = yToPx(0);
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(xToPx(shaded[0].x), y0);
  for (const point of shaded) ctx.lineTo(xToPx(point.x), yToPx(point.y));
  ctx.lineTo(xToPx(shaded[shaded.length - 1].x), y0);
  ctx.closePath();
  ctx.fillStyle = "rgba(212, 91, 71, 0.22)";
  ctx.fill();
  ctx.restore();
}

function drawCurve(ctx, points, xToPx, yToPx) {
  ctx.save();
  ctx.strokeStyle = "#0b7a75";
  ctx.lineWidth = 2.8;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  let drawing = false;
  for (const point of points) {
    if (point.y === null) {
      drawing = false;
      continue;
    }
    if (!drawing) {
      ctx.moveTo(xToPx(point.x), yToPx(point.y));
      drawing = true;
    } else {
      ctx.lineTo(xToPx(point.x), yToPx(point.y));
    }
  }
  ctx.stroke();
  ctx.restore();
}

function drawBounds(ctx, plot, xToPx, margin, innerHeight) {
  if (!Number.isFinite(plot.shadeMin) || !Number.isFinite(plot.shadeMax) || plot.shadeMin === plot.shadeMax) return;
  ctx.save();
  ctx.strokeStyle = "#6f5bb8";
  ctx.fillStyle = "#6f5bb8";
  ctx.setLineDash([5, 5]);
  const bounds = [
    { value: plot.shadeMin, label: plot.leftTail ? "-∞" : formatTick(plot.shadeMin) },
    { value: plot.shadeMax, label: plot.rightTail ? "∞" : formatTick(plot.shadeMax) },
  ];
  for (const bound of bounds) {
    const px = xToPx(bound.value);
    ctx.beginPath();
    ctx.moveTo(px, margin.top);
    ctx.lineTo(px, margin.top + innerHeight);
    ctx.stroke();
    ctx.fillText(bound.label, px + 5, margin.top + 15);
  }
  ctx.restore();
}

function drawSurfacePlot(ctx, width, height, plot) {
  const frame = { cx: width * 0.52, cy: height * 0.58, scale: Math.min(width, height) * 0.31 };
  ctx.save();
  const base = [
    projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, 0),
    projectSurfacePoint(plot, frame, plot.xMax, plot.yMin, 0),
    projectSurfacePoint(plot, frame, plot.xMax, plot.yMax, 0),
    projectSurfacePoint(plot, frame, plot.xMin, plot.yMax, 0),
  ];
  drawPolygon(ctx, base);
  ctx.fillStyle = "rgba(11, 122, 117, 0.07)";
  ctx.strokeStyle = "rgba(97, 113, 122, 0.34)";
  ctx.fill();
  ctx.stroke();
  drawSurfaceBaseGrid(ctx, plot, frame);
  drawSurfaceMesh(ctx, plot, frame);
  drawSurfaceAxes(ctx, plot, frame);
  ctx.restore();
}

function projectSurfacePoint(plot, frame, xValue, yValue, zValue) {
  const xSpan = Math.max(1e-12, plot.xMax - plot.xMin);
  const ySpan = Math.max(1e-12, plot.yMax - plot.yMin);
  const zScale = Math.max(Math.abs(plot.zMin), Math.abs(plot.zMax), 1e-9);
  const xn = ((xValue - plot.xMin) / xSpan - 0.5) * 2;
  const yn = ((yValue - plot.yMin) / ySpan - 0.5) * 2;
  const zn = Math.max(-1.4, Math.min(1.4, zValue / zScale));
  return {
    x: frame.cx + frame.scale * (xn - yn) * 0.62,
    y: frame.cy + frame.scale * ((xn + yn) * 0.32 - zn * 0.86),
    depth: xn + yn - zn * 0.16,
  };
}

function drawPolygon(ctx, points) {
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i += 1) ctx.lineTo(points[i].x, points[i].y);
  ctx.closePath();
}

function drawSurfaceBaseGrid(ctx, plot, frame) {
  ctx.save();
  ctx.strokeStyle = "rgba(97, 113, 122, 0.18)";
  for (let i = 0; i <= 6; i += 1) {
    const t = i / 6;
    const xv = plot.xMin + (plot.xMax - plot.xMin) * t;
    const yv = plot.yMin + (plot.yMax - plot.yMin) * t;
    const a = projectSurfacePoint(plot, frame, xv, plot.yMin, 0);
    const b = projectSurfacePoint(plot, frame, xv, plot.yMax, 0);
    const c = projectSurfacePoint(plot, frame, plot.xMin, yv, 0);
    const d = projectSurfacePoint(plot, frame, plot.xMax, yv, 0);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.moveTo(c.x, c.y);
    ctx.lineTo(d.x, d.y);
    ctx.stroke();
  }
  ctx.restore();
}

function drawSurfaceMesh(ctx, plot, frame) {
  const cells = [];
  for (let row = 0; row < plot.rows.length - 1; row += 1) {
    for (let col = 0; col < plot.rows[row].length - 1; col += 1) {
      const a = plot.rows[row][col];
      const b = plot.rows[row][col + 1];
      const c = plot.rows[row + 1][col + 1];
      const d = plot.rows[row + 1][col];
      if ([a, b, c, d].some((point) => point.z === null)) continue;
      const points = [a, b, c, d].map((point) => projectSurfacePoint(plot, frame, point.x, point.y, point.z));
      cells.push({ points, avgZ: (a.z + b.z + c.z + d.z) / 4, depth: points.reduce((s, p) => s + p.depth, 0) / 4 });
    }
  }
  cells.sort((a, b) => a.depth - b.depth);
  ctx.save();
  ctx.lineWidth = 0.7;
  for (const cell of cells) {
    drawPolygon(ctx, cell.points);
    ctx.fillStyle = surfaceColor(cell.avgZ, plot.zMin, plot.zMax, 0.72);
    ctx.strokeStyle = "rgba(21, 32, 38, 0.16)";
    ctx.fill();
    ctx.stroke();
  }
  ctx.restore();
}

function surfaceColor(value, zMin, zMax, alpha) {
  const t = Math.max(0, Math.min(1, (value - zMin) / Math.max(1e-12, zMax - zMin)));
  const low = [111, 91, 184];
  const mid = [11, 122, 117];
  const high = [212, 91, 71];
  const left = t < 0.5 ? low : mid;
  const right = t < 0.5 ? mid : high;
  const local = t < 0.5 ? t * 2 : (t - 0.5) * 2;
  const rgb = left.map((channel, index) => Math.round(channel + (right[index] - channel) * local));
  return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`;
}

function drawSurfaceAxes(ctx, plot, frame) {
  const origin = projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, 0);
  drawAxis(ctx, origin, projectSurfacePoint(plot, frame, plot.xMax, plot.yMin, 0), "#0b7a75", "x");
  drawAxis(ctx, origin, projectSurfacePoint(plot, frame, plot.xMin, plot.yMax, 0), "#6f5bb8", "y");
  drawAxis(ctx, origin, projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, Math.max(Math.abs(plot.zMax), 1)), "#d45b47", "z");
}

function drawAxis(ctx, start, end, color, label) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();
  ctx.font = "700 14px Cascadia Mono, Consolas, monospace";
  ctx.fillText(label, end.x + 10, end.y + 10);
  ctx.restore();
}

function drawMiniPlot(canvas, plot) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (plot?.kind === "surface") {
    drawSurfacePlot(ctx, canvas.width, canvas.height, plot);
  } else if (plot?.kind === "polar_area" || plot?.kind === "polar_surface") {
    drawPolarPlot(ctx, canvas.width, canvas.height, plot);
  } else {
    drawCurvePlot(ctx, canvas.width, canvas.height, plot);
  }
}

function formatTick(value) {
  if (Math.abs(value) >= 1000 || (Math.abs(value) > 0 && Math.abs(value) < 0.001)) return value.toExponential(1);
  return String(Number((Math.abs(value) < 1e-10 ? 0 : value).toFixed(2)));
}

function bindEvents() {
  for (const tab of elements.modeTabs) tab.addEventListener("click", () => setSection(tab.dataset.section));
  for (const button of elements.modeButtons) button.addEventListener("click", () => setMode(button.dataset.mode));
  elements.calculate.addEventListener("click", calculate);
  for (const input of [
    elements.expression,
    elements.lower,
    elements.upper,
    elements.xLower,
    elements.xUpper,
    elements.yLower,
    elements.yUpper,
    elements.innerExpression,
    elements.rLower,
    elements.rUpper,
    elements.thetaLower,
    elements.thetaUpper,
  ]) {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") calculate();
    });
  }
  elements.palette.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-insert]");
    if (button) insertAtCursor(elements.expression, button.dataset.insert);
  });
  elements.qaPalette.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-insert]");
    if (button) insertAtCursor(elements.qaExpression, button.dataset.insert);
  });
  elements.examples.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-example]");
    if (!button) return;
    const item = cannedProblems[button.dataset.example];
    applyProblem(item);
    calculate();
  });
  elements.lessonTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-lesson]");
    if (!button) return;
    currentLesson = button.dataset.lesson;
    renderLessons();
  });
  elements.lessonContent.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-lesson-problem]");
    if (!button) return;
    const item = cannedProblems[button.dataset.lessonProblem];
    try {
      await solveProblem(item, elements.lessonSolutionTitle, elements.lessonSolutionBody, true);
    } catch (error) {
      elements.lessonSolutionBody.innerHTML = `<div class="message error">${error.message}</div>`;
    }
  });
  elements.generatePractice.addEventListener("click", generatePractice);
  elements.practiceKind.addEventListener("change", () => {
    elements.practiceProblem.innerHTML = "<strong>还没有题目</strong><p>点击生成题目。</p>";
  });
  elements.askQuestion.addEventListener("click", askQuestion);
  elements.qaMode.addEventListener("change", updateQaBounds);
  window.addEventListener("resize", () => {
    if (lastPlot) drawPlot(lastPlot);
  });
}

function init() {
  renderPalettes();
  renderCommonExamples();
  renderLessons();
  updateQaBounds();
  bindEvents();
  calculate();
}

init();
