# GIF-FFmpeg-Optimizer-Generator

**一个纯前端实现的 GIF 优化命令生成器。无需上传文件，本地解析 GIF 属性，自动生成最高画质的 FFmpeg 压缩命令。**

![License](https://img.shields.io/github/license/yourusername/repo-name)
![Static Badge](https://img.shields.io/badge/Pure-Frontend-blue)
![Static Badge](https://img.shields.io/badge/Privacy-Safe-green)

---

## 🌟 项目背景

处理 GIF 图片时，我们经常面临两个难题：
1. **体积过大**：直接生成的 GIF 往往几十 MB，难以在网页或社交媒体传播。
2. **工具门槛高**：专业的命令行工具如 `Gifsicle` 或 `FFmpeg` 参数极其复杂，普通用户难以上手；而 `Ezgif` 等在线工具又存在上传慢、隐私风险和处理速度受限的问题。

本工具旨在提供一个**中间地带**：用户在网页上进行直观的参数调整，工具通过**二进制解析**本地 GIF 属性，最终生成一条经过深度优化的 FFmpeg 命令。用户只需在本地执行命令，即可获得与 Ezgif 相当甚至更优的压缩效果。

---

## ✨ 核心功能

- 🚀 **本地零上传解析**：采用纯 JavaScript 二进制流读取技术，瞬间获取 GIF 的原分辨率、总帧数、真实 FPS。
- ✂️ **智能抽帧逻辑**：
    - **强制 FPS**：统一降至网页标准的 10 FPS。
    - **Ezgif 模式**：提供“抽掉一半帧数”或“保留 1/3 帧数”选项，自动根据原图频率计算目标值。
- 📏 **比例缩放**：支持自定义宽度，高度自动等比缩放。
- 🎨 **极致画质算法**：生成的命令包含 `split`, `palettegen`, `paletteuse` 滤镜链，解决 GIF 常见的色散和噪点问题。
- 💻 **开发者友好**：单 HTML 文件架构，完美兼容 Astro、Vercel 等静态部署平台。

---

## 🛠️ 使用方式

### 1. 生成命令
1. 打开网页工具。
2. 点击文件选择框，选中你想要压缩的 GIF。
3. 在工具面板查看原图信息（帧数、帧率等）。
4. 调整 **控制帧率** 或 **修改宽度**。
5. 点击 **📋 复制命令**。

### 2. 本地执行
1. 确保你的电脑已安装 `FFmpeg`。
2. 将 `ffmpeg.exe` 与图片放在同一个文件夹。
3. 在文件夹路径栏输入 `cmd` 回车，打开终端。
4. 粘贴命令并回车，等待处理完成。

---

## 🚀 收尾待完善优化工作

如果你打算长期使用或分享此工具，建议进行以下优化：

### 1. 完善教程图片
在 `README` 或 HTML 源代码中，将以下占位符替换为实际的操作截图，提升新手用户体验：
- `YOUR_IMAGE_URL_STEP1`: 展示 `ffmpeg.exe` 与图片同框的截图。
- `YOUR_IMAGE_URL_STEP2`: 展示如何在地址栏输入 `cmd` 的截图。
- `YOUR_IMAGE_URL_STEP3`: 展示黑色命令行运行成功的截图。

### 2. 自定义下载链接
在 HTML 底部教程区，将下载链接指向你推荐的 FFmpeg 版本（如：[Gyan.dev](https://www.gyan.dev/ffmpeg/builds/)）。

### 3. 部署到个人网站 (Astro/Vercel)
如果你使用 Astro，建议将此 HTML 逻辑封装为组件：
- 将 CSS 放入 `<style>` 标签。
- 将 JS 逻辑放入 `<script is:inline>` 标签以确保在客户端正常解析二进制流。
- 配置 `vercel.json` 开启跨源隔离（如果未来打算集成 FFmpeg.wasm）。

---

## 📝 许可证

本项目采用 [MIT License](LICENSE) 开源。

---

### 🤝 贡献与反馈

如果你有更好的 FFmpeg 滤镜参数建议，或者发现了解析特定 GIF 时的 Bug，欢迎提交 Issue 或 Pull Request！

---

### ⚡ 提示
*本工具生成的命令示例：*
```bash
ffmpeg -i "input.gif" -vf "fps=10,scale=500:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -y "output_opt.gif"
```
