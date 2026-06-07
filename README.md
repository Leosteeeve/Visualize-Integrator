# Calculus Studio

本地优先的可视化积分学习、练习、问答与自动计算系统。项目目标是把“算得准”和“看得懂”放在第一位：后端用 SymPy/SciPy/C++ 做计算与校验，前端用结构化输入、教材级步骤、MathJax 公式和 Canvas/Three.js 可视化帮助学习。

## 当前能力

- 页面分为四个主区域：学习路线、练习模式、问答模式、可视化工具。
- 支持中英双语切换，语言选择会保存在浏览器本地。
- 支持积分类型：
  - 不定积分
  - 定积分
  - 反常积分
  - 矩形区域二重积分
  - 极坐标曲线面积
  - 极坐标二重积分
  - 旋转体/立体几何积分
- 计算路径：
  - SymPy 负责符号积分、精确结果、LaTeX 输出和结果校验。
  - C++ Simpson 引擎优先负责一维/二维数值积分。
  - C++ 不可用或不适合时自动回退到 SciPy。
- 可视化路径：
  - Canvas 绘制一元曲线、区间阴影、反常积分尾部、极坐标网格和极坐标面积。
  - Three.js 绘制可拖拽旋转、缩放和自动旋转的二重积分曲面、极坐标曲面和旋转体 3D 图像。
  - Three.js 已放入 `web/vendor` 和 `docs/vendor`，不依赖 CDN。

## 学习、练习和问答

学习路线从零解释积分直觉、公式符号、使用条件和典型例题。每个章节可以把例题加载到上方可视化工具中。

练习模式由后端题库生成器驱动，不再依赖前端固定模板池。生成流程是“题型家族 + 参数随机化 + 后端校验 + 签名去重”，当前覆盖不定积分、定积分、反常积分、二重积分、极坐标积分和旋转体积分。

问答模式支持结构化输入，也支持少量自然数学文本。复杂题建议使用结构化字段，这样解析更稳定。问答模式会尽量返回方法、公式卡、推导步骤、精确答案、数值校验和可视化数据；超出规则步骤引擎能力时，会明确降级而不是猜测推导。

## 旋转体积分

新增 `solid_revolution` 模式，第一版支持 4 种结构化预设：

- `washer_x`：垫片/圆盘法，绕 x 轴
- `washer_y`：垫片/圆盘法，绕 y 轴
- `shell_y`：柱壳法，绕 y 轴
- `shell_x`：柱壳法，绕 x 轴

常用公式：

```text
V = pi * integral_a^b (R(u)^2 - r(u)^2) du
V = 2*pi * integral_a^b radius(u) * height(u) du
```

后端会返回旋转体元数据、书面步骤、精确体积、数值校验和 3D 采样点。前端可以实时旋转和缩放图像，并提供重置视角和自动旋转开关。

## 本地运行

安装依赖：

```bat
D:\Anaconda\python.exe -m pip install -r requirements.txt
```

启动服务：

```bat
run.bat
```

然后打开：

```text
http://127.0.0.1:8000
```

后端第一次需要数值积分时会尝试自动编译 `cpp\integrator.cpp`。也可以手动编译：

```bat
build_cpp.bat
```

## GitHub Pages 静态页

GitHub Pages 只能托管静态文件，不能运行 Python 后端。这个项目的 `docs` 文件夹可以作为 GitHub Pages 的静态入口，用来浏览学习内容和界面；要在线计算，需要再连接一个后端服务。

设置方法：

1. 打开 GitHub 仓库的 `Settings`。
2. 进入 `Pages`。
3. `Source` 选择 `Deploy from a branch`。
4. `Branch` 选择 `main`，文件夹选择 `/docs`。
5. 保存后等待 GitHub 发布页面。

## 云端后端

推荐第一版用 Render 部署 Python 后端。仓库里已经包含 `render.yaml`，可以直接作为 Render Blueprint 使用。

部署成功后检查：

```text
https://YOUR-SERVICE.onrender.com/api/health
```

应该返回：

```json
{"ok": true, "service": "calculus-studio"}
```

把 GitHub Pages 连接到后端有两种方式。

临时方式：在 Pages 地址后加 `api` 参数：

```text
https://YOUR-GITHUB-USER.github.io/YOUR-REPO/?api=https://YOUR-SERVICE.onrender.com
```

永久方式：编辑 `docs/index.html` 中的配置：

```html
<script>
  window.CALCULUS_API_BASE = "https://YOUR-SERVICE.onrender.com";
</script>
```

更多部署说明见 [DEPLOY.md](DEPLOY.md)。

## 输入格式

表达式示例：

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

反常积分可以使用：

```text
oo
-oo
```

极坐标请用：

```text
theta
r
```

问答模式示例：

```text
∫_0^1 x^2 dx
∫_1^oo 1/x^2 dx
∫∫ x*y dA
r=2*sin(theta), theta=0..pi
```

## API

底层计算：

```text
POST /api/integrate
```

步骤解释：

```text
POST /api/solve
```

练习生成：

```text
POST /api/practice/generate
```

旋转体示例：

```json
{
  "mode": "solid_revolution",
  "solidPreset": "washer_x",
  "expression": "x",
  "innerExpression": "0",
  "lower": "0",
  "upper": "1"
}
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
D:\Anaconda\python.exe -m py_compile backend\server.py backend\problem_generator.py backend\algebra_steps.py
D:\Anaconda\python.exe tests\smoke_solve.py
D:\Anaconda\python.exe tests\smoke_generator.py
D:\Anaconda\python.exe tests\smoke_http.py
```

前端 3D 烟测会调用本机 Microsoft Edge headless，验证旋转体模式能真实创建 Three.js 画布：

```bat
D:\Anaconda\python.exe tests\smoke_frontend_3d.py
```

题库压力测试：

```bat
set CALCULUS_GENERATOR_STRESS=1
D:\Anaconda\python.exe tests\smoke_generator.py
```

## 后续方向

- 问答模式接入更完整的本地规则步骤引擎。
- 一般区域二重积分：`y=g1(x)..g2(x)` 或 `x=h1(y)..h2(y)`。
- 极坐标弧长、交点自动分析和更复杂的极坐标区域拆分。
- 更丰富的旋转体类型，例如非标准旋转轴和由两条曲线围成的自动区域。
- 开源题库导入适配层，优先研究 WeBWorK、Numbas、STACK 的题目格式。
