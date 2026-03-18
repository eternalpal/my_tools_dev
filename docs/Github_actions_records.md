# 金融市场自定义消息每日自动监控 (main.py)记录说明

## 🌟 项目缘由
本项目源于对开源项目 [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) 的二次开发（二创）。

在原始项目的基础上，我针对个人需求进行了深度定制：
*   **跨市场覆盖**：从单一 A 股扩展至加密货币（BTC/ETH）、大宗商品（黄金/白银/原油）。
*   **算法修复**：重构了涨跌幅计算逻辑，解决了因休市和时区导致的 `NaN%` 报错。
*   **接口加固**：针对 GitHub 海外 IP 被封锁的问题，引入了新浪财经原生 API 作为备份，确保数据 100% 可达。

---

## ☁️ 关于 GitHub Actions 部署方式

### 什么是 GitHub Actions？
GitHub Actions 是 GitHub 提供的自动化流平台。你可以把它理解为一个**免费的、部署在云端的“私人助手”**。它允许你在不需要购买任何服务器的情况下，定时触发 Python 脚本运行。

### ✅ 优势特点
*   **零成本**：完全白嫖 GitHub 提供的每月 2000 分钟免费额度。
*   **免维护**：无需担心服务器宕机、续费或环境崩溃。
*   **原生外网环境**：服务器位于海外，可以畅快抓取 Coinbase、Yahoo Finance 等国内难以访问的数据源。

### ❌ 不足之处
*   **IP 限制**：部分国内金融网站（如东财）会识别并拦截数据中心 IP，需配合多源备份策略。
*   **时区差异**：系统使用 UTC 时间，配置时需手动进行北京时间换算（+8 小时）。

---

## 🛠️ 快速上手指南

1.  **Fork 本仓库**：点击右上角 `Fork`，将代码保存到你的 GitHub 账号下。
2.  **配置飞书 Webhook**：
    *   在飞书群中：`设置` -> `群机器人` -> `添加自定义机器人`。**（飞书桌面客户端才能设置，网页，手机都不行）**
    *   **安全设置**：勾选“自定义关键词”，填入 `行情`。
    *   复制生成的 **Webhook 地址**。
3.  **设置 GitHub Secrets**：
    *   进入你的仓库：`Settings` -> `Secrets and variables` -> `Actions`。
    *   新建 `New repository secret`：
        *   Name: `FEISHU_WEBHOOK`
        *   Secret: 粘贴刚才复制的飞书链接。
4.  **启用并运行**：
    *   点击 `Actions` 标签页，点击绿色按钮启用工作流。
    *   点击 `Financial Monitor` -> `Run workflow` 手动测试一次。

---

## ❓ 常见问题 FAQ (避坑指南)

### Q1：如何修改定时推送的时间？
编辑 `.github/workflows/daily_run.yml` 中的 `cron` 表达式。
**注意：GitHub 使用 UTC 时间，比北京时间晚 8 小时。**
*   北京时间 **09:00** 运行 $\rightarrow$ `cron: '0 1 * * *'`
*   北京时间 **15:10** 运行 $\rightarrow$ `cron: '10 7 * * 1-5'` (1-5 表示周一至周五)

### Q2：运行报错 `No such file or directory: 'requirements.txt'`？
**原因**：脚本在云端安装依赖时，找不到记录库清单的文件。
**解决**：
1.  确保仓库根目录下有一个名为 `requirements.txt` 的文件。
2.  文件内容需包含：`requests`, `akshare`, `yfinance`, `pandas`。
3.  或者直接在 `.yml` 文件中将命令改为：`pip install requests akshare yfinance pandas`。

### Q3：如何获取飞书 Webhook 链接？
1.  飞书群 -> `群设置` -> `群机器人` -> `添加机器人` -> `自定义机器人`。
**（飞书桌面客户端才能设置，网页，手机都不行）**
2.  **关键点**：安全设置必须包含关键词（本脚本默认使用“行情”），否则推送会返回 400 错误。

### Q4：本地 CMD 调试时，无法访问外网接口怎么办？
如果你在本地使用 **v2rayN** 代理，需要让 CMD 窗口识别代理环境。
1.  **确定端口**：v2rayN 的 HTTP 代理端口默认为 `10809`。
2.  **CMD 设置方式**：在运行 Python 之前，先输入以下命令：
    ```cmd
    set http_proxy=http://127.0.0.1:10809
    set https_proxy=http://127.0.0.1:10809
    ```
3.  **Python 代码方式**：在 `main.py` 最顶部加入以下代码：
    ```python
    import os
    os.environ['https_proxy'] = 'http://127.0.0.1:10809'
    ```
    *注：GitHub Actions 部署时不需要这些配置，仅限本地开发使用。*

---

## 📈 版本更新记录
*   **v1.0**：参考 `daily_stock_analysis` 完成 Actions 框架搭建。
*   **v2.0**：修复了休市期间 yfinance 返回 `NaN` 导致涨跌幅报错的问题。
*   **v3.0**：引入新浪财经 API 解决 A 股数据封锁问题，并优化了飞书消息的北京时间显示格式。

---
*免责声明：本工具仅供学习参考，不构成任何投资建议。*