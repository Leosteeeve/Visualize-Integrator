# Calculus Studio

本地优先的可视化积分学习与自动计算系统。当前目标是把“算得准”和“看得懂”放在第一位：后端用 SymPy/SciPy/C++ 做计算，前端用模板输入、书面步骤和 Canvas 可视化帮助学习。

## 当前阶段

- 顶部主导航分为 **学习路线、练习模式、问答模式、可视化工具**。
- 支持不定积分、定积分、反常积分、矩形区域二重积分、极坐标面积、极坐标二重积分。
- SymPy 负责符号积分、精确结果和 LaTeX；C++ Simpson 引擎优先负责数值积分；失败时回退到 SciPy。
- 一元积分可视化曲线、区间、正负面积；反常积分标记无穷尾部和奇点；二重积分绘制 `x/y/z` 三轴曲面预览。
- 极坐标可视化绘制极轴、角度网格、同心圆、曲线、夹层区域和二重积分底面区域。
- 学习路线提供从零开始的讲义、公式解释、章节例题和可视化按钮。
- 练习模式由后端海量随机题生成器驱动，不依赖前端固定模板池。

## 极坐标能力

新增两个计算模式：

- `polar_area`：计算极坐标曲线面积

```text
A = 1/2 ∫(r_out(theta)^2 - r_in(theta)^2) dtheta
```

- `polar_double`：计算极坐标二重积分

```text
∫∫ f(r, theta) dA = ∫∫ f(r, theta) * r dr dtheta
```

输入变量：

- `theta`、`t`、`θ` 都表示角度。
- `r` 表示极径。
- 极坐标二重积分会自动乘雅可比因子 `r`。

问答模式支持少量自然文本，例如：

```text
r=2*sin(theta), theta=0..pi
```

复杂极坐标题推荐使用页面里的结构化字段。

## 练习生成器

练习题采用 **题型家族 + 参数随机化 + 后端校验 + 签名去重**：

- 后端模块：`backend/problem_generator.py`
- API：`POST /api/practice/generate`
- 题型规模：200 个题型家族，设计候选空间约 400000 题。
- 每个 `积分种类 + 难度` 至少有 10 个题型家族。
- 生成后会立即调用 `/api/solve` 校验，成功后才返回给前端。
- 前端用 `localStorage` 保存最近 300 道题的签名，点击“再来一题”会把签名列表发给后端避免重复。

支持的练习种类：

- 不定积分：基本原函数、逐项积分、换元法、分部积分、特殊函数型题。
- 定积分：微积分基本定理、换元法、对称性、三角恒等式、数值型挑战题。
- 反常积分：p 型积分、端点奇异、指数尾部、对数型、收敛/发散判断。
- 二重积分：矩形区域、可分离函数、对称性、耦合曲面、数值型曲面体积。
- 极坐标积分：圆、扇形、心形线、玫瑰线、夹层面积、极坐标二重积分、雅可比训练。

难度分层：

- **简单**：直接公式、基础函数、步骤短。
- **AP**：换元、面积、基础反常判断、基础极坐标曲线。
- **高等技巧**：分部积分、恒等变形、对称性、可分离二重积分、极坐标雅可比。
- **MIT/挑战**：多步骤技巧、特殊函数、数值校验、复杂边界和收敛性判断。

## 运行

```bat
run.bat
```

然后打开：

```text
http://127.0.0.1:8000
```

后端第一次计算时会尝试自动编译 `cpp\integrator.cpp`。也可以手动编译：

```bat
build_cpp.bat
```

## 输入格式

表达式支持：

```text
x^2
sin(x)
exp(-x^2)
sqrt(1-x^2)
log(x)
x*y
2*sin(theta)
exp(-r^2)
```

上下限可以使用 `pi`、`e` 和普通代数式。反常积分可以使用：

```text
oo
-oo
```

问答模式同时支持结构化输入和少量自然数学文本，例如：

```text
∫_0^1 x^2 dx
∫_1^oo 1/x^2 dx
∫∫ x*y dA
r=2*sin(theta), theta=0..pi
```

## API

底层计算接口：

```text
POST /api/integrate
```

步骤解释接口：

```text
POST /api/solve
```

练习生成接口：

```text
POST /api/practice/generate
```

极坐标面积示例：

```json
{
  "mode": "polar_area",
  "expression": "2*sin(theta)",
  "innerExpression": "0",
  "thetaLower": "0",
  "thetaUpper": "pi"
}
```

极坐标二重积分示例：

```json
{
  "mode": "polar_double",
  "expression": "1",
  "rLower": "0",
  "rUpper": "1",
  "thetaLower": "0",
  "thetaUpper": "2*pi"
}
```

## 测试

常用烟测：

```bat
D:\Anaconda\python.exe tests\smoke_solve.py
D:\Anaconda\python.exe tests\smoke_generator.py
D:\Anaconda\python.exe tests\smoke_http.py
```

大样本生成器测试：

```bat
set CALCULUS_GENERATOR_STRESS=1
D:\Anaconda\python.exe tests\smoke_generator.py
```

## 下一步

- 一般区域二重积分：`y=g1(x)..g2(x)` 或 `x=h1(y)..h2(y)`。
- 极坐标弧长与更复杂的交点自动分析。
- 3D 渲染升级：Three.js 曲面、区域和旋转体。
- 输入系统升级：MathLive 公式输入框。
- 开源题库导入适配层：优先研究 WeBWorK、Numbas、STACK 的题目格式，而不把它们作为当前运行依赖。
