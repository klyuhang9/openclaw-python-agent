---
description: 【发小红书】触发词：「发小红书」「小红书发帖」「发布笔记」「小红书发布」「发一篇笔记」。看到这些词立即 load_skill("xiaohongshu_post") 并用 browser_* 工具栈完成全流程（导航→上传图片→填标题正文→点发布），禁止口头给文案让用户手动复制。
---

# 小红书发帖 (Xiaohongshu Post)

## 概述

通过 browser 工具控制小红书创作中心网页版，端到端发布笔记。

## 前置条件

- **浏览器登录态**：`~/.cli-agent/browser-profile/` 已经登录小红书。首次跑某站点需要用户手动扫码登录一次，之后会话自动复用 cookies。
- **图片文件**：本地绝对路径，jpg / png / webp / jpeg。

## 完整流程（已端到端验证）

### 1. 导航到发布页

```
browser_navigate("https://creator.xiaohongshu.com/publish/publish?source=official")
```

### 2. 切换到「上传图文」标签

小红书默认进入「上传视频」。用 `browser_click_text` 切到图文：

```
browser_click_text("上传图文", exact=True)
```

> `browser_click` 用 ref 会因为小红书的 React 渲染了多个同名 span 导致定位歧义；用 `browser_click_text` 更稳，工具会自动选可见且在视口内的那个。

### 3. 上传图片

文件 `<input type=file>` 在小红书页面是**隐藏的**（display:none），snapshot 看不到。直接用：

```
browser_upload_file("/Users/.../image.png", accept_hint="image")
```

`accept_hint="image"` 是为了区分图片 input 和视频 input。

上传后等 **5-8 秒**（图片处理 + 编辑表单加载），再操作下一步。

### 4. 填标题

```
browser_snapshot()                           # 找标题 ref
browser_type("eN", "你的标题（≤20字）")
```

或者更稳的方式（适用于模型确认 placeholder 存在的情况）：
- 标题框 placeholder 是「填写标题会有更多赞哦」
- 正文是 `contenteditable=true` 的 div，placeholder「输入正文描述」

### 5. 填正文

正文是 contenteditable，先 click 进入再 type。`browser_type` 已支持。

> **副作用**：输入 `#tag` 后会弹自动补全下拉框，遮住底部按钮。**填完正文务必 `browser_press_key("Escape")` 关掉**。注意不要点页面空白处去关（会点到左侧导航跳走）。

### 6. 点「发布」按钮（重点）

「发布」按钮在自定义 web component `<xhs-publish-btn>` 里，shadow DOM 是**关闭的**，`browser_snapshot` / `browser_click_text("发布")` 都看不到内部结构。

但元素本身可见，属性能读：

```js
<xhs-publish-btn submit-text="发布" save-text="暂存离开"
                 submit-disabled="false" save-disabled="false">
```

布局：680px 宽 × 90px 高，左半「暂存离开」、右半「发布」。**用 `browser_click_selector` 在元素内偏移点击**：

```
browser_click_selector("xhs-publish-btn", position_x=412, position_y=45)
```

`position_x=412` 是右半正中（约「发布」按钮中心），`position_y=45` 是垂直中心。

### 7. 确认发布成功

```
browser_screenshot()         # 看到「发布成功」+ 绿勾
# 或检查 URL
```

成功后 URL 跳转到 `/publish/success`。

## 调试技巧

- 每步操作后**重新 snapshot 或 screenshot**，确认页面状态。
- snapshot 抓不到某元素 → 优先 `browser_click_text`（穿透 shadow DOM 和 iframe）。
- `browser_click_text` 也抓不到 → 说明是 closed shadow DOM 的 web component，看元素的标签名和属性，用 `browser_click_selector` + position 偏移点击。
- **禁止用 AppleScript / 屏幕坐标 / `execute_python` 操作浏览器** —— 一律走 `browser_*` 工具。

## 上传限制

- 图片：最大 32MB，最多 18 张，比例 3:4 至 2:1 最佳
- 视频：最大 20GB，mp4 / mov

## 错误处理

- **登录态失效**：navigate 后 URL 跳到 `/login` → 引导用户扫码后重试
- **「上传图文」点击 outside viewport**：`browser_click_text` 内部已对 force fallback 处理；如果还失败，等更久（页面 SPA 渲染慢）
- **发布按钮 disabled**：检查标题是否填了、图片是否真上传完成（看左上角缩略图存在与否）
- **小红书提示「内容违规」**：标题 / 正文有敏感词，让用户改文案重试
