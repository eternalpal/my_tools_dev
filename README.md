# my_tools_dev
保存开发的一些小工具

## 01 GIF-html-tool

参考使用的项目是：https://github.com/kohler/gifsicle

使用 WebAssembly (纯前端运行)的方法，用html页面，实现调整Gif图片的文件大小，总帧数，以及调整长宽。

GIF-html-tool-claude.html - claude sonnet4.6

[GIF-html-tool-claude.html](GIF-html-tool/GIF-html-tool-claude.html)

GIF-html-tool-Gemini.html - Gemini 3.0

[GIF-html-tool-Gemini.html](GIF-html-tool/GIF-html-tool-Gemini.html)

下面html文件后即可使用。

若双击打开后，点击按钮报错或者没反应（按 F12 看到红色 CORS policy 错误），这是因为浏览器（主要是严格的安全策略）禁止了本地 file:/// 协议加载 WebAssembly 模块。

解决办法极其简单：

不要双击打开，而是用本地服务器打开它。
如果有 VS Code：装一个叫 Live Server 的插件，右键这个 HTML 文件选择 Open with Live Server 即可完美运行。
如果装了 Node.js：在当前文件夹打开终端，输入 npx serve 即可。
如果装了 Python：在当前文件夹打开终端，输入 python -m http.server 即可。

## 02 Github tool

[Github tool](github_tool/)

一个强大且轻量的自动化脚本工具，用于**批量提取** GitHub 项目的核心元数据（Star、Fork、简介等），并**智能深度扫描**项目的 README 文件，精准统计其中包含的展示大图和 GIF 动图数量。

非常适合开发者、研究人员或产品经理用于批量筛选有详尽 UI 截图或演示的开源项目。

使用方法：
1、python源码运行
2、下载release中 github_tool_v1.0.exe 与 url-list.txt 放在同一文件夹下，双击即可运行。

## 03 金融市场自定义消息每日自动监控 (main.py)

这是一个基于 **Python** 和 **GitHub Actions** 实现的金融数据自动化监控工具。无需服务器，零成本运行，每天自动抓取全球市场数据并推送到 **飞书**。

开发过程详细记录在这里：**[GitHub Actions开发过程和踩坑记录](docs/Github_actions_records.md)**

### 🌟 核心功能
*   **加密货币**：实时监控 BTC、ETH 现价及 24h 涨跌幅。
*   **大宗商品**：涵盖 黄金、白银、原油 的国际期货行情与走势。
*   **A 股指数**：集成 中证500、创业板指、科创50 的实时点位与涨跌幅。
*   **打新提醒**：自动检索今日是否有可转债申购，避免错过“肉签”。
*   **智能推送**：每日准时将精美报表推送到飞书机器人，支持涨跌动态图标（📈/📉）。

### 🛠️ 快速部署 (只需 3 分钟)
1.  **Fork 本仓库**：点击右上角 `Fork` 按钮，复制到你的账号下。
2.  **配置 Webhook**：
    *   在飞书群添加“自定义机器人”，获取 `Webhook URL`。
    *   在 GitHub 仓库中进入 `Settings` -> `Secrets and variables` -> `Actions`。
    *   新建 **Secret**：Name 填 `FEISHU_WEBHOOK`，Value 填入你的 Webhook 链接。
3.  **启用脚本**：
    *   点击仓库上方的 `Actions` 标签，点击 `I understand... enable them`。
    *   手动测试：选择左侧工作流，点击 `Run workflow`。

### 📅 运行计划
默认配置在 **北京时间每个工作日 09:00 和 15:10** 自动运行。
*   如需修改时间，请编辑 `.github/workflows/daily_run.yml` 中的 `cron` 表达式（注意 UTC 时区差 8 小时）。

### 📂 文件结构
*   `main.py`: 核心逻辑。采用多源备份机制（yfinance, Sina, THS），确保数据采集的高可用。
*   `daily_run.yml`: 自动化配置。定义了云端运行环境及触发时机。
*   `requirements.txt`: 依赖清单（`requests`, `yfinance`, `akshare`, `pandas`）。

### 🔄 版本迭代
*   **v1.0**: 实现基础 BTC/ETH 价格监控与推送。
*   **v2.0**: 引入 `AkShare` 与 `yfinance`，支持 A 股及大宗商品。
*   **v3.0 (Current)**: 
    *   重构涨跌幅算法，使用交易所“昨收价”字段确保精度。
    *   引入新浪财经原生 API，解决海外 IP 访问 A 股数据的限制。
    *   优化时区处理，支持毫秒级北京时间校验。

### ⚖️ 免责声明
本工具仅供学习交流使用，所提供数据来源于公开网络，不构成任何投资建议。投资有风险，入市需谨慎。

## 04 GIF-FFmpeg-Optimizer-Generator

一个纯前端实现的 GIF 优化（FFmpeg）命令生成器。无需上传文件，本地解析 GIF 属性，自动生成最高画质的 FFmpeg 压缩命令。

[详细介绍](GIF-FFmpeg-Optimizer-Generator/)

## 05 小学作文格子纸排版工具 (Composition Grid Generator)

响应学校语文老师的教学倡议而开发一个作文排版工具，实现在格子纸中快速排版作文。

[工具截图](Composition_Grid_Generator/shots01.jpg)
[工具截图](Composition_Grid_Generator/shots02.jpg)

[详细介绍](Composition_Grid_Generator/)

