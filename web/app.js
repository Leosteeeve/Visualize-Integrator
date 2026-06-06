const elements = {
  expression: document.querySelector("#expression"),
  expressionLabel: document.querySelector("#expressionLabel"),
  lower: document.querySelector("#lower"),
  upper: document.querySelector("#upper"),
  xLower: document.querySelector("#xLower"),
  xUpper: document.querySelector("#xUpper"),
  yLower: document.querySelector("#yLower"),
  yUpper: document.querySelector("#yUpper"),
  boundsGrid: document.querySelector("#boundsGrid"),
  doubleBoundsGrid: document.querySelector("#doubleBoundsGrid"),
  calculate: document.querySelector("#calculate"),
  statusLine: document.querySelector("#statusLine"),
  modeButtons: [...document.querySelectorAll(".segment")],
  palette: document.querySelector("#palette"),
  examples: document.querySelector("#examples"),
  plot: document.querySelector("#plot"),
  plotTitle: document.querySelector("#plotTitle"),
  numericChip: document.querySelector("#numericChip"),
  engineBadge: document.querySelector("#engineBadge"),
  statusResult: document.querySelector("#statusResult"),
  exactResult: document.querySelector("#exactResult"),
  numericResult: document.querySelector("#numericResult"),
  fourthResultLabel: document.querySelector("#fourthResultLabel"),
  antiderivativeResult: document.querySelector("#antiderivativeResult"),
  errorResult: document.querySelector("#errorResult"),
  messages: document.querySelector("#messages"),
  guideTabs: [...document.querySelectorAll(".guide-tab")],
  guideContent: document.querySelector("#guideContent"),
  solutionTitle: document.querySelector("#solutionTitle"),
  solutionBody: document.querySelector("#solutionBody"),
  generatePractice: document.querySelector("#generatePractice"),
  practiceDifficulty: document.querySelector("#practiceDifficulty"),
};

let currentMode = "definite";
let lastPlot = null;
let currentGuide = "foundation";

const math = String.raw;

const problemBank = [
  {
    id: "area-x2",
    title: "幂函数面积",
    difficulty: "easy",
    topic: "定积分",
    mode: "definite",
    expression: "x^2",
    lower: "0",
    upper: "1",
    statement: math`\int_0^1 x^2\,dx`,
    method: "幂函数公式 + 微积分基本定理",
    steps: (payload) => [
      math`把定积分看成曲线 \(y=x^2\) 在 \([0,1]\) 上方的面积。`,
      math`先求原函数：\(\int x^2\,dx=\frac{x^3}{3}+C\)。`,
      math`代入上下限：\(\left.\frac{x^3}{3}\right|_0^1=\frac{1}{3}-0\)。`,
      math`所以 \(\int_0^1 x^2\,dx=\frac{1}{3}\)。`,
      exactLine(payload),
    ],
  },
  {
    id: "sin-area",
    title: "正弦半波面积",
    difficulty: "easy",
    topic: "定积分",
    mode: "definite",
    expression: "sin(x)",
    lower: "0",
    upper: "pi",
    statement: math`\int_0^\pi \sin x\,dx`,
    method: "基本三角函数积分",
    steps: (payload) => [
      math`\(\sin x\) 在 \([0,\pi]\) 上非负，因此图像阴影就是实际面积。`,
      math`原函数为 \(\int \sin x\,dx=-\cos x+C\)。`,
      math`代入：\(\left[-\cos x\right]_0^\pi=-\cos\pi+\cos0=2\)。`,
      exactLine(payload),
    ],
  },
  {
    id: "u-sub",
    title: "换元法雏形",
    difficulty: "medium",
    topic: "技巧",
    mode: "definite",
    expression: "2*x*cos(x^2)",
    lower: "0",
    upper: "1",
    statement: math`\int_0^1 2x\cos(x^2)\,dx`,
    method: "换元法",
    steps: (payload) => [
      math`观察到内层函数 \(x^2\) 的导数是 \(2x\)，这正好出现在积分式里。`,
      math`令 \(u=x^2\)，则 \(du=2x\,dx\)。当 \(x=0\) 时 \(u=0\)，当 \(x=1\) 时 \(u=1\)。`,
      math`原积分化为 \(\int_0^1 \cos u\,du=\sin u\big|_0^1=\sin1\)。`,
      exactLine(payload),
    ],
  },
  {
    id: "parts",
    title: "分部积分",
    difficulty: "medium",
    topic: "技巧",
    mode: "definite",
    expression: "x*exp(x)",
    lower: "0",
    upper: "1",
    statement: math`\int_0^1 xe^x\,dx`,
    method: "分部积分",
    steps: (payload) => [
      math`使用公式 \(\int u\,dv=uv-\int v\,du\)。`,
      math`取 \(u=x\)，\(dv=e^x\,dx\)，于是 \(du=dx\)，\(v=e^x\)。`,
      math`\(\int xe^x\,dx=xe^x-\int e^x\,dx=xe^x-e^x+C\)。`,
      math`代入 \([0,1]\)：\((e-e)-(0-1)=1\)。`,
      exactLine(payload),
    ],
  },
  {
    id: "p-converges",
    title: "p 型反常积分收敛",
    difficulty: "medium",
    topic: "反常积分",
    mode: "improper",
    expression: "1/x^2",
    lower: "1",
    upper: "oo",
    statement: math`\int_1^\infty \frac{1}{x^2}\,dx`,
    method: "无穷区间极限",
    steps: (payload) => [
      math`把无穷上限改写为极限：\(\int_1^\infty x^{-2}\,dx=\lim_{b\to\infty}\int_1^b x^{-2}\,dx\)。`,
      math`原函数为 \(-x^{-1}\)，所以 \(\int_1^b x^{-2}\,dx=-\frac1b+1\)。`,
      math`令 \(b\to\infty\)，得到 \(1\)，因此积分收敛。`,
      exactLine(payload),
    ],
  },
  {
    id: "p-diverges",
    title: "调和尾部发散",
    difficulty: "medium",
    topic: "反常积分",
    mode: "improper",
    expression: "1/x",
    lower: "1",
    upper: "oo",
    statement: math`\int_1^\infty \frac{1}{x}\,dx`,
    method: "无穷区间极限",
    steps: (payload) => [
      math`写成极限：\(\lim_{b\to\infty}\int_1^b \frac1x\,dx\)。`,
      math`原函数是 \(\ln x\)，所以结果为 \(\lim_{b\to\infty}\ln b\)。`,
      math`这个极限趋于无穷，因此反常积分发散。`,
      exactLine(payload),
    ],
  },
  {
    id: "endpoint-singular",
    title: "可积端点奇异",
    difficulty: "medium",
    topic: "反常积分",
    mode: "improper",
    expression: "1/sqrt(x)",
    lower: "0",
    upper: "1",
    statement: math`\int_0^1 \frac{1}{\sqrt{x}}\,dx`,
    method: "端点极限",
    steps: (payload) => [
      math`函数在 \(x=0\) 处无界，所以要写成 \(\lim_{a\to0^+}\int_a^1 x^{-1/2}\,dx\)。`,
      math`原函数为 \(2\sqrt{x}\)。`,
      math`\(\lim_{a\to0^+}(2-2\sqrt a)=2\)，所以虽然端点无界，面积仍然有限。`,
      exactLine(payload),
    ],
  },
  {
    id: "double-xy",
    title: "矩形区域二重积分",
    difficulty: "easy",
    topic: "二重积分",
    mode: "double",
    expression: "x*y",
    xLower: "0",
    xUpper: "1",
    yLower: "0",
    yUpper: "1",
    statement: math`\int_0^1\int_0^1 xy\,dy\,dx`,
    method: "累次积分",
    steps: (payload) => [
      math`二重积分可以看成曲面 \(z=xy\) 在单位正方形上方的有向体积。`,
      math`先对 \(y\) 积分：\(\int_0^1 xy\,dy=x\left[\frac{y^2}{2}\right]_0^1=\frac{x}{2}\)。`,
      math`再对 \(x\) 积分：\(\int_0^1 \frac{x}{2}\,dx=\frac14\)。`,
      exactLine(payload),
    ],
  },
  {
    id: "paraboloid",
    title: "抛物面体积",
    difficulty: "medium",
    topic: "二重积分",
    mode: "double",
    expression: "x^2+y^2",
    xLower: "-1",
    xUpper: "1",
    yLower: "-1",
    yUpper: "1",
    statement: math`\int_{-1}^1\int_{-1}^1 (x^2+y^2)\,dy\,dx`,
    method: "拆项与对称",
    steps: (payload) => [
      math`在正方形区域上，\(\int\int(x^2+y^2)=\int\int x^2+\int\int y^2\)。`,
      math`\int_{-1}^1\int_{-1}^1 x^2\,dy\,dx=2\int_{-1}^1 x^2\,dx=\frac43\)。`,
      math`同理 \(y^2\) 的部分也是 \(\frac43\)，总和为 \(\frac83\)。`,
      exactLine(payload),
    ],
  },
  {
    id: "wave-surface",
    title: "可分离波面",
    difficulty: "hard",
    topic: "二重积分",
    mode: "double",
    expression: "sin(x)*cos(y)",
    xLower: "0",
    xUpper: "pi",
    yLower: "0",
    yUpper: "pi/2",
    statement: math`\int_0^\pi\int_0^{\pi/2}\sin x\cos y\,dy\,dx`,
    method: "可分离函数",
    steps: (payload) => [
      math`因为 integrand 是 \(\sin x\cos y\)，区域又是矩形，所以可以拆成两个一元积分的乘积。`,
      math`\int_0^\pi \sin x\,dx=2\)，\(\int_0^{\pi/2}\cos y\,dy=1\)。`,
      math`因此二重积分等于 \(2\cdot1=2\)。`,
      exactLine(payload),
    ],
  },
  {
    id: "gaussian-window",
    title: "有限窗口高斯丘",
    difficulty: "hard",
    topic: "二重积分",
    mode: "double",
    expression: "exp(-(x^2+y^2))",
    xLower: "-2",
    xUpper: "2",
    yLower: "-2",
    yUpper: "2",
    statement: math`\int_{-2}^2\int_{-2}^2 e^{-(x^2+y^2)}\,dy\,dx`,
    method: "数值积分 + 曲面观察",
    steps: (payload) => [
      math`这个矩形窗口上的高斯曲面没有简单初等闭式，适合用数值积分和三维图形一起理解。`,
      math`函数在原点最高，离原点越远越接近 \(0\)，所以体积主要集中在中心区域。`,
      math`上方 \(xyz\) 图中的彩色曲面就是 \(z=e^{-(x^2+y^2)}\)，底面正方形是积分区域。`,
      exactLine(payload),
    ],
  },
];

const guideChapters = {
  foundation: {
    title: "积分的核心直觉",
    cards: [
      {
        title: "1. 定积分不是“神秘公式”，而是累积量",
        tags: ["AP AB/BC", "面积", "微积分基本定理"],
        body: [
          "定积分最直接的图像是面积：把区间切成许多小段，每一小段用函数高度乘以宽度近似，最后把这些小矩形加起来。",
          "如果函数在 x 轴下方，定积分会计入负面积，所以它更准确地说是有向面积。物理中也常把它解释为累积量，例如速度积分得到位移。",
        ],
        formula: math`\[\int_a^b f(x)\,dx=\lim_{n\to\infty}\sum_{i=1}^n f(x_i^\*)\Delta x,\qquad \int_a^b f(x)\,dx=F(b)-F(a)\]`,
        examples: ["area-x2", "sin-area"],
      },
      {
        title: "2. 看图时要分清面积、净面积和变化量",
        tags: ["图像理解", "符号判断"],
        body: [
          "图像阴影帮助我们判断答案应该是正、负还是接近零。比如奇函数在对称区间上的定积分常常抵消为零。",
          "当前工具会把积分区间染色，适合用来检查你算出的符号和大小是否合理。",
        ],
        formula: math`\[\int_{-a}^{a}\text{odd}(x)\,dx=0,\qquad \int_{-a}^{a}\text{even}(x)\,dx=2\int_0^a\text{even}(x)\,dx\]`,
        examples: [],
      },
    ],
  },
  techniques: {
    title: "常见积分技巧",
    cards: [
      {
        title: "1. 换元法：识别“内层函数 + 导数”",
        tags: ["u-substitution", "链式法则反向"],
        body: [
          "换元法本质上是链式法则的反向使用。看到 f(g(x))g'(x) 的结构，就可以尝试令 u=g(x)。",
          "对定积分换元时，最好同步改上下限，这样不用最后再换回 x。",
        ],
        formula: math`\[\int_a^b f(g(x))g'(x)\,dx=\int_{g(a)}^{g(b)}f(u)\,du\]`,
        examples: ["u-sub"],
      },
      {
        title: "2. 分部积分：乘积求导的反向",
        tags: ["integration by parts", "BC 常见"],
        body: [
          "当 integrand 是两个不同类型函数的乘积，例如多项式乘指数、对数、三角函数，分部积分很常见。",
          "选择 u 时通常让它求导后更简单；指数和三角函数常作为 dv。",
        ],
        formula: math`\[\int u\,dv=uv-\int v\,du\]`,
        examples: ["parts"],
      },
      {
        title: "3. 对称性与拆项：先看结构再算",
        tags: ["对称", "简化"],
        body: [
          "很多题不难算，但如果直接展开会很慢。先看奇偶性、可分离结构、区间对称性，经常能把题目变短。",
          "二重积分中，如果函数可写成 p(x)q(y)，且区域是矩形，积分可以拆成两个一元积分的乘积。",
        ],
        formula: math`\[\int_a^b\int_c^d p(x)q(y)\,dy\,dx=\left(\int_a^b p(x)\,dx\right)\left(\int_c^d q(y)\,dy\right)\]`,
        examples: ["wave-surface"],
      },
    ],
  },
  improper: {
    title: "反常积分",
    cards: [
      {
        title: "1. 无穷区间：先改写为极限",
        tags: ["AP BC", "收敛", "发散"],
        body: [
          "反常积分不能直接把无穷当数字代入。正确做法是先用有限端点 b 替代无穷，再让 b 趋近无穷。",
          "如果这个极限是有限数，积分收敛；如果极限无穷或不存在，积分发散。",
        ],
        formula: math`\[\int_a^\infty f(x)\,dx=\lim_{b\to\infty}\int_a^b f(x)\,dx\]`,
        examples: ["p-converges", "p-diverges"],
      },
      {
        title: "2. 端点奇异：无界不等于发散",
        tags: ["端点奇点", "极限"],
        body: [
          "函数在端点附近无界时，面积仍可能有限。例如 1/sqrt(x) 在 0 附近无限高，但高得不够快，所以面积有限。",
          "可视化时你会看到曲线靠近端点急剧上升；计算时要用单侧极限确认。",
        ],
        formula: math`\[\int_a^b f(x)\,dx=\lim_{t\to a^+}\int_t^b f(x)\,dx\quad\text{if }f\text{ is unbounded at }a\]`,
        examples: ["endpoint-singular"],
      },
    ],
  },
  double: {
    title: "二重积分与体积",
    cards: [
      {
        title: "1. 二重积分是曲面下的有向体积",
        tags: ["多变量", "体积", "xyz"],
        body: [
          "一元定积分把区间上的高度累积成面积；二重积分把平面区域上的高度 z=f(x,y) 累积成体积。",
          "当前工具先支持矩形区域。上方三维图中，x-y 平面是底面区域，z 轴表示函数高度。",
        ],
        formula: math`\[\iint_R f(x,y)\,dA\approx \sum f(x_i,y_j)\Delta A\]`,
        examples: ["double-xy", "paraboloid"],
      },
      {
        title: "2. 矩形区域可以写成累次积分",
        tags: ["Fubini", "矩形区域"],
        body: [
          "在矩形区域 R=[a,b]×[c,d] 上，可以先固定 x 对 y 积分，再对 x 积分；也可以交换顺序。",
          "如果曲面有正有负，二重积分给的是有向体积；如果函数非负，它就是通常意义的体积。",
        ],
        formula: math`\[\iint_R f(x,y)\,dA=\int_a^b\int_c^d f(x,y)\,dy\,dx\]`,
        examples: ["wave-surface", "gaussian-window"],
      },
    ],
  },
  practice: {
    title: "随机练习",
    cards: [
      {
        title: "用题目训练“先判断方法”的能力",
        tags: ["题库", "难度分层", "自动步骤"],
        body: [
          "选择难度后点击随机生成。每道题都会同步到上方可视化工具，并在右侧给出标准书面步骤。",
          "基础题重在概念与公式；进阶题训练换元、分部、反常极限；挑战题包含二重积分、可分离结构和数值曲面观察。",
        ],
        formula: math`\[\text{题目}\rightarrow\text{选方法}\rightarrow\text{计算}\rightarrow\text{用图像检查大小与符号}\]`,
        examples: [],
      },
    ],
  },
};

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  if (Math.abs(numeric) >= 1e6 || (Math.abs(numeric) > 0 && Math.abs(numeric) < 1e-5)) {
    return numeric.toExponential(8);
  }
  return numeric.toPrecision(11).replace(/\.?0+$/, "");
}

function exactLine(payload) {
  const exact = payload?.exact?.available ? `\\(${payload.exact.latex}\\)` : null;
  const numeric = payload?.numeric?.ok !== false ? formatNumber(payload?.numeric?.value) : null;
  if (exact && numeric && exact !== `\\(${numeric}\\)`) {
    return math`计算器核验：精确结果为 ${exact}，数值近似为 \(${numeric}\)。`;
  }
  if (exact) {
    return math`计算器核验：精确结果为 ${exact}。`;
  }
  if (numeric) {
    return math`计算器核验：数值近似为 \(${numeric}\)。`;
  }
  return "计算器核验：该题没有有限数值结果。";
}

function problemById(id) {
  return problemBank.find((problem) => problem.id === id);
}

function renderGuide(category = currentGuide) {
  currentGuide = category;
  for (const button of elements.guideTabs) {
    button.classList.toggle("active", button.dataset.guide === category);
  }

  const chapter = guideChapters[category];
  if (!chapter) {
    return;
  }

  elements.guideContent.innerHTML = chapter.cards
    .map((card) => {
      const tags = card.tags.map((tag) => `<span class="tag">${tag}</span>`).join("");
      const paragraphs = card.body.map((text) => `<p>${text}</p>`).join("");
      const examples = card.examples?.length ? renderExampleList(card.examples) : "";
      return `
        <section class="lesson-card">
          <h3>${card.title}</h3>
          <div class="lesson-meta">${tags}</div>
          ${paragraphs}
          <div class="formula-box">${card.formula}</div>
          ${examples}
        </section>
      `;
    })
    .join("");

  if (category === "practice") {
    const difficulty = elements.practiceDifficulty.value;
    const matching = problemBank.filter((problem) => problem.difficulty === difficulty);
    const preview = matching
      .map((problem) => `
        <div class="practice-card">
          <strong>${problem.title}</strong>
          <span class="tag">${problem.topic}</span>
          <div class="formula-box">\\[${problem.statement}\\]</div>
          <div class="example-actions">
            <button class="mini-action" type="button" data-solve-problem="${problem.id}">显示步骤</button>
            <button class="mini-action" type="button" data-visualize-problem="${problem.id}">载入可视化</button>
          </div>
        </div>
      `)
      .join("");
    elements.guideContent.insertAdjacentHTML(
      "beforeend",
      `<section class="lesson-card"><h3>${difficultyLabel(difficulty)}题池</h3><div class="example-list">${preview}</div></section>`
    );
  }

  typesetMath();
}

function renderExampleList(ids) {
  return `
    <div class="example-list">
      ${ids
        .map((id) => {
          const problem = problemById(id);
          if (!problem) {
            return "";
          }
          return `
            <div class="example-card">
              <strong>${problem.title}</strong>
              <div class="formula-box">\\[${problem.statement}\\]</div>
              <div class="example-actions">
                <button class="mini-action" type="button" data-solve-problem="${problem.id}">显示步骤</button>
                <button class="mini-action" type="button" data-visualize-problem="${problem.id}">载入可视化</button>
              </div>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function difficultyLabel(value) {
  if (value === "easy") {
    return "基础";
  }
  if (value === "hard") {
    return "挑战";
  }
  return "进阶";
}

function payloadForProblem(problem) {
  return {
    mode: problem.mode,
    expression: problem.expression,
    lower: problem.lower ?? "0",
    upper: problem.upper ?? "1",
    xLower: problem.xLower ?? "0",
    xUpper: problem.xUpper ?? "1",
    yLower: problem.yLower ?? "0",
    yUpper: problem.yUpper ?? "1",
    epsilon: 1e-8,
  };
}

function applyProblemToControls(problem) {
  elements.expression.value = problem.expression;
  if (problem.lower !== undefined) {
    elements.lower.value = problem.lower;
  }
  if (problem.upper !== undefined) {
    elements.upper.value = problem.upper;
  }
  if (problem.xLower !== undefined) {
    elements.xLower.value = problem.xLower;
  }
  if (problem.xUpper !== undefined) {
    elements.xUpper.value = problem.xUpper;
  }
  if (problem.yLower !== undefined) {
    elements.yLower.value = problem.yLower;
  }
  if (problem.yUpper !== undefined) {
    elements.yUpper.value = problem.yUpper;
  }
  setMode(problem.mode, false);
}

async function solveGuideProblem(problem, options = {}) {
  applyProblemToControls(problem);
  elements.solutionTitle.textContent = problem.title;
  elements.solutionBody.innerHTML = `<p>正在计算并整理步骤...</p>`;
  typesetMath();

  try {
    const response = await fetch("/api/integrate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payloadForProblem(problem)),
    });
    const payload = await response.json();
    if (!payload.ok) {
      throw new Error(payload.error || "计算失败");
    }
    renderResult(payload);
    renderSolution(problem, payload);
    if (options.scrollToTool) {
      document.querySelector(".workspace").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (error) {
    elements.solutionBody.innerHTML = `<div class="message error">${error.message}</div>`;
  } finally {
    typesetMath();
  }
}

function renderSolution(problem, payload) {
  const result = payload?.exact?.available
    ? `\\(${payload.exact.latex}\\)`
    : payload?.numeric?.ok !== false
      ? `\\(${formatNumber(payload.numeric?.value)}\\)`
      : "发散或无有限值";
  const steps = problem.steps(payload).map((step) => `<li>${step}</li>`).join("");

  elements.solutionTitle.textContent = problem.title;
  elements.solutionBody.innerHTML = `
    <div class="formula-box">\\[${problem.statement}\\]</div>
    <p><strong>方法：</strong>${problem.method}</p>
    <ol>${steps}</ol>
    <div class="solution-result">答案：${result}</div>
  `;
}

function generatePracticeProblem() {
  const difficulty = elements.practiceDifficulty.value;
  const candidates = problemBank.filter((problem) => problem.difficulty === difficulty);
  const problem = candidates[Math.floor(Math.random() * candidates.length)];
  if (!problem) {
    return;
  }
  renderGuide("practice");
  solveGuideProblem(problem, { scrollToTool: true });
}

function typesetMath() {
  if (window.MathJax?.typesetPromise) {
    window.MathJax.typesetPromise().catch(() => {});
  }
}

function setMode(mode, shouldCalculate = true) {
  currentMode = mode;
  for (const button of elements.modeButtons) {
    button.classList.toggle("active", button.dataset.mode === mode);
  }
  elements.boundsGrid.style.display = mode === "indefinite" || mode === "double" ? "none" : "grid";
  elements.doubleBoundsGrid.style.display = mode === "double" ? "grid" : "none";
  elements.expressionLabel.textContent = mode === "double" ? "f(x, y)" : "f(x)";
  if (shouldCalculate) {
    calculate();
  }
}

function insertAtCursor(input, value) {
  input.focus();
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? input.value.length;
  const before = input.value.slice(0, start);
  const after = input.value.slice(end);
  input.value = before + value + after;

  const cursorOffset = value.endsWith("()") ? value.length - 1 : value.length;
  const cursor = start + cursorOffset;
  input.setSelectionRange(cursor, cursor);
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
    epsilon: 1e-8,
  };
}

async function calculate() {
  elements.calculate.disabled = true;
  elements.statusLine.textContent = "计算中";
  setMessages([]);

  try {
    const response = await fetch("/api/integrate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload()),
    });
    const payload = await response.json();
    if (!payload.ok) {
      throw new Error(payload.error || "计算失败");
    }
    renderResult(payload);
    elements.statusLine.textContent = "完成";
  } catch (error) {
    elements.statusLine.textContent = "输入需要调整";
    elements.exactResult.textContent = "-";
    elements.numericResult.textContent = "-";
    elements.antiderivativeResult.textContent = "-";
    elements.errorResult.textContent = "-";
    elements.statusResult.textContent = "-";
    elements.numericChip.textContent = "-";
    elements.engineBadge.textContent = "待机";
    setMessages([error.message], true);
  } finally {
    elements.calculate.disabled = false;
  }
}

function renderResult(payload) {
  elements.plotTitle.textContent = payload.mode === "double" ? `z = ${payload.expression}` : `f(x) = ${payload.expression}`;

  if (payload.mode === "double") {
    const exact = payload.exact?.available ? payload.exact.text : "-";
    const numeric = payload.numeric?.ok !== false ? formatNumber(payload.numeric?.value) : "-";
    const error = payload.numeric?.ok !== false ? formatNumber(payload.numeric?.estimated_error) : "-";
    elements.statusResult.textContent = "二重积分";
    elements.exactResult.textContent = exact;
    elements.numericResult.textContent = numeric;
    elements.errorResult.textContent = error;
    elements.numericChip.textContent = numeric;
    elements.engineBadge.textContent = payload.numeric?.engine === "cpp" ? "C++ 2D" : "SciPy 2D";
    elements.fourthResultLabel.textContent = "区域";
    elements.antiderivativeResult.textContent = payload.double?.region_text || "矩形区域";
  } else if (payload.mode === "definite" || payload.mode === "improper") {
    const exact = payload.exact?.available ? payload.exact.text : "-";
    const numeric = payload.numeric?.ok !== false ? formatNumber(payload.numeric?.value) : "-";
    const error = payload.numeric?.ok !== false ? formatNumber(payload.numeric?.estimated_error) : "-";
    elements.exactResult.textContent = exact;
    elements.numericResult.textContent = numeric;
    elements.errorResult.textContent = error;
    elements.numericChip.textContent = payload.mode === "improper" ? translateImproperStatus(payload.improper?.status) : numeric;
    elements.fourthResultLabel.textContent = "原函数";

    if (payload.mode === "improper") {
      elements.statusResult.textContent = translateImproperStatus(payload.improper?.status);
      elements.engineBadge.textContent = payload.improper?.status === "divergent" ? "判定" : "SciPy";
    } else {
      elements.statusResult.textContent = "有限区间";
      elements.engineBadge.textContent = payload.numeric?.engine === "cpp" ? "C++" : "SciPy";
    }
  } else {
    elements.fourthResultLabel.textContent = "原函数";
    elements.statusResult.textContent = "不定积分";
    elements.exactResult.textContent = "-";
    elements.numericResult.textContent = "-";
    elements.errorResult.textContent = "-";
    elements.numericChip.textContent = "F(x)";
    elements.engineBadge.textContent = "SymPy";
  }

  if (payload.mode === "double") {
    // The rectangular region is already rendered in the fourth result slot.
  } else if (payload.antiderivative?.available) {
    elements.antiderivativeResult.textContent = `${payload.antiderivative.text} + C`;
  } else {
    elements.antiderivativeResult.textContent = "未得到闭式";
  }

  const messages = [...(payload.warnings || [])];
  if (payload.mode === "improper" && payload.improper?.reason) {
    messages.unshift(payload.improper.reason);
  }
  if (payload.mode === "improper" && payload.improper?.singularities?.length) {
    const labels = payload.improper.singularities
      .map((item) => `${item.text} (${translateSingularityLocation(item.location)})`)
      .join(", ");
    messages.push(`检测到奇点: ${labels}`);
  }
  setMessages(messages);
  lastPlot = payload.plot;
  drawPlot(lastPlot);
}

function translateImproperStatus(status) {
  if (status === "convergent") {
    return "收敛";
  }
  if (status === "divergent") {
    return "发散";
  }
  if (status === "unknown") {
    return "待判定";
  }
  return "-";
}

function translateSingularityLocation(location) {
  if (location === "left_endpoint") {
    return "左端点";
  }
  if (location === "right_endpoint") {
    return "右端点";
  }
  return "区间内部";
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

  if (!plot || !Array.isArray(plot.points)) {
    return;
  }

  const margin = { left: 54, right: 18, top: 22, bottom: 42 };
  const innerWidth = Math.max(10, width - margin.left - margin.right);
  const innerHeight = Math.max(10, height - margin.top - margin.bottom);
  const xMin = plot.xMin;
  const xMax = plot.xMax;
  let yMin = Math.min(plot.yMin, 0);
  let yMax = Math.max(plot.yMax, 0);
  if (yMin === yMax) {
    yMin -= 1;
    yMax += 1;
  }

  const xToPx = (x) => margin.left + ((x - xMin) / (xMax - xMin)) * innerWidth;
  const yToPx = (y) => margin.top + (1 - (y - yMin) / (yMax - yMin)) * innerHeight;

  drawGrid(ctx, margin, innerWidth, innerHeight, xToPx, yToPx, xMin, xMax, yMin, yMax);
  drawShade(ctx, plot, xToPx, yToPx);
  drawCurve(ctx, plot.points, xToPx, yToPx);
  drawBounds(ctx, plot, xToPx, margin, innerHeight);
}

function drawGrid(ctx, margin, innerWidth, innerHeight, xToPx, yToPx, xMin, xMax, yMin, yMax) {
  ctx.save();
  ctx.strokeStyle = "#e4ebee";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#61717a";
  ctx.font = "12px Cascadia Mono, Consolas, monospace";

  const xTicks = 8;
  const yTicks = 6;
  for (let i = 0; i <= xTicks; i += 1) {
    const value = xMin + ((xMax - xMin) * i) / xTicks;
    const px = xToPx(value);
    ctx.beginPath();
    ctx.moveTo(px, margin.top);
    ctx.lineTo(px, margin.top + innerHeight);
    ctx.stroke();
    ctx.fillText(formatTick(value), px - 16, margin.top + innerHeight + 25);
  }
  for (let i = 0; i <= yTicks; i += 1) {
    const value = yMin + ((yMax - yMin) * i) / yTicks;
    const py = yToPx(value);
    ctx.beginPath();
    ctx.moveTo(margin.left, py);
    ctx.lineTo(margin.left + innerWidth, py);
    ctx.stroke();
    ctx.fillText(formatTick(value), 8, py + 4);
  }

  ctx.strokeStyle = "#80909a";
  ctx.lineWidth = 1.4;
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
  if (!Number.isFinite(plot.shadeMin) || !Number.isFinite(plot.shadeMax) || plot.shadeMin === plot.shadeMax) {
    return;
  }
  const min = Math.min(plot.shadeMin, plot.shadeMax);
  const max = Math.max(plot.shadeMin, plot.shadeMax);
  const shaded = plot.points.filter((point) => point.y !== null && point.x >= min && point.x <= max);
  if (shaded.length < 2) {
    return;
  }

  ctx.save();
  const y0 = yToPx(0);
  ctx.beginPath();
  ctx.moveTo(xToPx(shaded[0].x), y0);
  for (const point of shaded) {
    ctx.lineTo(xToPx(point.x), yToPx(point.y));
  }
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
    const px = xToPx(point.x);
    const py = yToPx(point.y);
    if (!drawing) {
      ctx.moveTo(px, py);
      drawing = true;
    } else {
      ctx.lineTo(px, py);
    }
  }
  ctx.stroke();
  ctx.restore();
}

function drawBounds(ctx, plot, xToPx, margin, innerHeight) {
  if (!Number.isFinite(plot.shadeMin) || !Number.isFinite(plot.shadeMax) || plot.shadeMin === plot.shadeMax) {
    return;
  }
  ctx.save();
  ctx.strokeStyle = "#6f5bb8";
  ctx.fillStyle = "#6f5bb8";
  ctx.lineWidth = 1.4;
  ctx.setLineDash([5, 5]);
  const bounds = [
    { value: plot.shadeMin, label: plot.leftTail ? "-∞" : formatTick(plot.shadeMin) },
    { value: plot.shadeMax, label: plot.rightTail ? "∞" : formatTick(plot.shadeMax) },
  ];
  for (const bound of bounds) {
    const value = bound.value;
    const px = xToPx(value);
    ctx.beginPath();
    ctx.moveTo(px, margin.top);
    ctx.lineTo(px, margin.top + innerHeight);
    ctx.stroke();
    ctx.fillText(bound.label, px + 5, margin.top + 15);
  }
  ctx.restore();
}

function drawSurfacePlot(ctx, width, height, plot) {
  const frame = {
    cx: width * 0.52,
    cy: height * 0.58,
    scale: Math.min(width, height) * 0.31,
  };

  ctx.save();
  const base = [
    projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, 0),
    projectSurfacePoint(plot, frame, plot.xMax, plot.yMin, 0),
    projectSurfacePoint(plot, frame, plot.xMax, plot.yMax, 0),
    projectSurfacePoint(plot, frame, plot.xMin, plot.yMax, 0),
  ];

  ctx.fillStyle = "rgba(11, 122, 117, 0.07)";
  ctx.strokeStyle = "rgba(97, 113, 122, 0.34)";
  ctx.lineWidth = 1;
  drawPolygon(ctx, base);
  ctx.fill();
  ctx.stroke();

  drawSurfaceBaseGrid(ctx, plot, frame);
  drawSurfaceMesh(ctx, plot, frame);
  drawSurfaceAxes(ctx, plot, frame);
  drawSurfaceTicks(ctx, plot, frame);
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
    zn,
  };
}

function drawPolygon(ctx, points) {
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i += 1) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.closePath();
}

function drawSurfaceBaseGrid(ctx, plot, frame) {
  ctx.save();
  ctx.strokeStyle = "rgba(97, 113, 122, 0.18)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 6; i += 1) {
    const t = i / 6;
    const xv = plot.xMin + (plot.xMax - plot.xMin) * t;
    const yv = plot.yMin + (plot.yMax - plot.yMin) * t;
    const xLineA = projectSurfacePoint(plot, frame, xv, plot.yMin, 0);
    const xLineB = projectSurfacePoint(plot, frame, xv, plot.yMax, 0);
    const yLineA = projectSurfacePoint(plot, frame, plot.xMin, yv, 0);
    const yLineB = projectSurfacePoint(plot, frame, plot.xMax, yv, 0);
    ctx.beginPath();
    ctx.moveTo(xLineA.x, xLineA.y);
    ctx.lineTo(xLineB.x, xLineB.y);
    ctx.moveTo(yLineA.x, yLineA.y);
    ctx.lineTo(yLineB.x, yLineB.y);
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
      if ([a, b, c, d].some((point) => point.z === null)) {
        continue;
      }
      const points = [a, b, c, d].map((point) => projectSurfacePoint(plot, frame, point.x, point.y, point.z));
      const avgZ = (a.z + b.z + c.z + d.z) / 4;
      const depth = points.reduce((sum, point) => sum + point.depth, 0) / points.length;
      cells.push({ points, avgZ, depth });
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
  const span = Math.max(1e-12, zMax - zMin);
  const t = Math.max(0, Math.min(1, (value - zMin) / span));
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
  const xEnd = projectSurfacePoint(plot, frame, plot.xMax, plot.yMin, 0);
  const yEnd = projectSurfacePoint(plot, frame, plot.xMin, plot.yMax, 0);
  const zScale = Math.max(Math.abs(plot.zMin), Math.abs(plot.zMax), 1);
  const zEnd = projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, zScale);

  ctx.save();
  drawAxis(ctx, origin, xEnd, "#0b7a75", "x");
  drawAxis(ctx, origin, yEnd, "#6f5bb8", "y");
  drawAxis(ctx, origin, zEnd, "#d45b47", "z");
  ctx.restore();
}

function drawAxis(ctx, start, end, color, label) {
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();

  const angle = Math.atan2(end.y - start.y, end.x - start.x);
  const size = 8;
  ctx.beginPath();
  ctx.moveTo(end.x, end.y);
  ctx.lineTo(end.x - Math.cos(angle - 0.45) * size, end.y - Math.sin(angle - 0.45) * size);
  ctx.lineTo(end.x - Math.cos(angle + 0.45) * size, end.y - Math.sin(angle + 0.45) * size);
  ctx.closePath();
  ctx.fill();

  ctx.font = "700 14px Cascadia Mono, Consolas, monospace";
  ctx.fillText(label, end.x + Math.cos(angle) * 12, end.y + Math.sin(angle) * 12);
}

function drawSurfaceTicks(ctx, plot, frame) {
  ctx.save();
  ctx.fillStyle = "#61717a";
  ctx.font = "12px Cascadia Mono, Consolas, monospace";
  const x0 = projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, 0);
  const x1 = projectSurfacePoint(plot, frame, plot.xMax, plot.yMin, 0);
  const y1 = projectSurfacePoint(plot, frame, plot.xMin, plot.yMax, 0);
  const z0 = projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, 0);
  const z1 = projectSurfacePoint(plot, frame, plot.xMin, plot.yMin, plot.zMax);
  ctx.fillText(formatTick(plot.xMin), x0.x - 28, x0.y + 16);
  ctx.fillText(formatTick(plot.xMax), x1.x + 8, x1.y + 8);
  ctx.fillText(formatTick(plot.yMax), y1.x - 26, y1.y + 4);
  ctx.fillText("0", z0.x - 22, z0.y - 6);
  ctx.fillText(formatTick(plot.zMax), z1.x + 8, z1.y);
  ctx.restore();
}

function formatTick(value) {
  if (Math.abs(value) >= 1000 || (Math.abs(value) > 0 && Math.abs(value) < 0.001)) {
    return value.toExponential(1);
  }
  const rounded = Math.abs(value) < 1e-10 ? 0 : value;
  return String(Number(rounded.toFixed(2)));
}

elements.calculate.addEventListener("click", calculate);
elements.expression.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    calculate();
  }
});
for (const input of [elements.lower, elements.upper, elements.xLower, elements.xUpper, elements.yLower, elements.yUpper]) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      calculate();
    }
  });
}

for (const button of elements.modeButtons) {
  button.addEventListener("click", () => setMode(button.dataset.mode));
}

elements.palette.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-insert]");
  if (!button) {
    return;
  }
  insertAtCursor(elements.expression, button.dataset.insert);
});

elements.examples.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-expression]");
  if (!button) {
    return;
  }
  elements.expression.value = button.dataset.expression;
  if (button.dataset.lower !== undefined) {
    elements.lower.value = button.dataset.lower;
  }
  if (button.dataset.upper !== undefined) {
    elements.upper.value = button.dataset.upper;
  }
  if (button.dataset.xLower !== undefined) {
    elements.xLower.value = button.dataset.xLower;
  }
  if (button.dataset.xUpper !== undefined) {
    elements.xUpper.value = button.dataset.xUpper;
  }
  if (button.dataset.yLower !== undefined) {
    elements.yLower.value = button.dataset.yLower;
  }
  if (button.dataset.yUpper !== undefined) {
    elements.yUpper.value = button.dataset.yUpper;
  }
  setMode(button.dataset.mode || "definite", false);
  calculate();
});

for (const button of elements.guideTabs) {
  button.addEventListener("click", () => renderGuide(button.dataset.guide));
}

elements.guideContent.addEventListener("click", (event) => {
  const solveButton = event.target.closest("button[data-solve-problem]");
  const visualizeButton = event.target.closest("button[data-visualize-problem]");
  const id = solveButton?.dataset.solveProblem || visualizeButton?.dataset.visualizeProblem;
  if (!id) {
    return;
  }
  const problem = problemById(id);
  if (!problem) {
    return;
  }
  solveGuideProblem(problem, { scrollToTool: Boolean(visualizeButton) });
});

elements.generatePractice.addEventListener("click", generatePracticeProblem);
elements.practiceDifficulty.addEventListener("change", () => {
  if (currentGuide === "practice") {
    renderGuide("practice");
  }
});

window.addEventListener("resize", () => {
  if (lastPlot) {
    drawPlot(lastPlot);
  }
});

renderGuide("foundation");
calculate();
