# my_tools_dev
保存开发的一些小工具

## GIF-html-tool

参考使用的项目是：https://github.com/kohler/gifsicle

使用 WebAssembly (纯前端运行)的方法，用html页面，实现调整Gif图片的文件大小，总帧数，以及调整长宽。

GIF-html-tool-claude.html - claude sonnet4.6

GIF-html-tool-Gemini.html - Gemini 3.0

下面html文件后即可使用。

若双击打开后，点击按钮报错或者没反应（按 F12 看到红色 CORS policy 错误），这是因为浏览器（主要是严格的安全策略）禁止了本地 file:/// 协议加载 WebAssembly 模块。

解决办法极其简单：

不要双击打开，而是用本地服务器打开它。
如果有 VS Code：装一个叫 Live Server 的插件，右键这个 HTML 文件选择 Open with Live Server 即可完美运行。
如果装了 Node.js：在当前文件夹打开终端，输入 npx serve 即可。
如果装了 Python：在当前文件夹打开终端，输入 python -m http.server 即可。

## Github tool

一个强大且轻量的自动化脚本工具，用于**批量提取** GitHub 项目的核心元数据（Star、Fork、简介等），并**智能深度扫描**项目的 README 文件，精准统计其中包含的展示大图和 GIF 动图数量。

非常适合开发者、研究人员或产品经理用于批量筛选有详尽 UI 截图或演示的开源项目。