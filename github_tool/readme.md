# 📦 GitHub tool (GitHub 批量分析与 README 智能查图工具)

一个强大且轻量的自动化脚本工具，用于**批量提取** GitHub 项目的核心元数据（Star、Fork、简介等），并**智能深度扫描**项目的 README 文件，精准统计其中包含的展示大图和 GIF 动图数量。

非常适合开发者、研究人员或产品经理用于批量筛选有详尽 UI 截图或演示的开源项目。

## ✨ 核心特性

- 📊 **基础数据全覆盖**：自动抓取项目的 `Star数`、`Fork数`、`创建时间`、`项目简介 (Description)` 以及 `官网/演示链接 (Homepage)`。
- 🧠 **智能图片过滤引擎**：
  - **静态图大图检测**：自动过滤掉 README 中的构建徽章 (Badges)、小图标和打赏按钮。通过校验服务器返回文件大小，**仅统计大于 30KB 的高质量展示图**。
  - **GIF 特权通道**：准确识别 GIF 动图（无论文件大小），单独分类统计。
- 🔗 **完美兼容 GitHub 图床**：彻底解决了 GitHub 原生拖拽上传图片（`user-attachments`）无 `.png`/`.jpg` 后缀导致常规脚本无法识别的痛点，支持基于 HTTP Header 的精准格式探测。
- 兼容多种 Markdown 写法：支持识别 `![]()`、`<img src="..."/>` 以及适配深色模式的 `<source srcset="..."/>` 标签。
- 💾 **一键导出**：运行结束后自动生成结构化的 `result.csv` 文件，方便导入 Excel 进行二次筛选。

## 🚀 快速开始

### 方式一：直接运行 Python 源码（推荐 Mac/Linux/Win 开发者）

1. **环境准备**：确保已安装 Python 3.6+。
2. **安装依赖**：
   ```bash
   pip install requests
   ```
3. **准备数据源**：在同级目录下创建 `url-list.txt` 文件，每行填入一个 GitHub 项目地址。例如：
   ```text
   https://github.com/torvalds/linux
   https://github.com/jordanbaird/Ice
   ```
4. **运行脚本**：
   ```bash
   python github_tool_v5.py
   ```

### 方式二：打包为 Windows 可执行文件 (.exe)

如果您需要在没有 Python 环境的 Windows 电脑上运行：
1. 安装打包工具：`pip install pyinstaller`
2. 执行打包命令：`pyinstaller --onefile github_tool_v5.py`
3. 将生成的 `github_tool_v5.exe` 与 `url-list.txt` 放在同一文件夹下，**双击即可运行**。

## ⚙️ 配置文件说明

程序运行依赖同目录下的 `url-list.txt`，请确保该文件存在且非空。

在程序启动时，会提示您输入 **GitHub Token**（按回车可跳过）：
- **不输入 Token**：受限于 GitHub 官方 API 限制，每小时最多只能请求约 60 次。
- **输入 Token（强烈推荐）**：请求上限提升至每小时 5000 次。
  > **如何获取 Token？**
  > 登录 GitHub -> `Settings` -> `Developer settings` -> `Personal access tokens (Classic)` -> Generate new token -> 勾选 `public_repo` -> 生成并复制。

## 📊 导出数据字段说明

程序运行完毕后生成的 `result.csv` 包含以下列：

| 字段名 | 说明 |
| :--- | :--- |
| **项目名称** | 格式为 `Owner/Repo` |
| **项目简介** | GitHub 仓库的 Description |
| **Homepage链接** | 仓库右侧 About 区域的官网或演示网址 |
| **发布时间** | 仓库创建日期 (YYYY-MM-DD) |
| **Star数** / **Fork数** | 仓库当前的热度数据 |
| **中大图数量(不含GIF)** | README 中体积 **> 30KB** 的 png/jpg 等静态图片数量 |
| **GIF数量** | README 中的 GIF 动画数量（无视大小限制） |
| **是否符合(>3图)** | 若 `大图数 + GIF数 >= 3` 则为 "是"，否则为 "否" |
| **状态** | 分析状态（成功 / 网络错误 / Token无效等） |

## 🛠️ 技术细节 (它是如何工作的？)

普通的正则提取往往会漏掉大量的图片，本项目采用了多层级的验证机制：
1. **HTML/Markdown 混合解析**：暴力提取所有潜在的多媒体链接。
2. **CDN 链接还原**：自动将 `github.com/.../blob/...` 的网页预览链接转换为 `raw.githubusercontent.com` 的直链。
3. **轻量级网络探测**：使用 `requests.get(stream=True)` 仅拉取目标链接的 HTTP Header，不下载图片实体，在保证极快速度的同时，准确获取 `Content-Type` 和 `Content-Length`，实现精准查图。