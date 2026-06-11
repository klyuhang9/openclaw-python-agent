---
description: 【发抖音】触发词：「发抖音」「抖音发帖」「发布抖音视频」「抖音发布」「发图文」。看到这些词立即 load_skill("douyin_post") 并用 browser_* 工具栈完成全流程（导航→选发布类型→上传媒体→填标题描述→点发布），禁止口头给文案让用户手动复制。
---

# 抖音发帖 (Douyin Post)

## 概述

通过 browser 工具控制抖音创作者平台网页版，自动化完成发帖全流程。

## 前置条件

1. **浏览器已登录抖音**：浏览器使用持久化 profile（`~/.cli-agent/browser-profile/`），首次需手动扫码登录抖音创作者平台，之后登录态自动保留
2. **图片/视频文件存在于本地**：提供绝对路径

## 首次登录流程（仅一次）

如果 snapshot 显示需要登录：

1. `browser_navigate("https://creator.douyin.com")`
2. 提示用户用抖音 App 扫描页面上的二维码登录
3. 登录成功后 cookies 写入 `~/.cli-agent/browser-profile/`，后续会话不需重复登录

## 完整流程

### 步骤 1：打开抖音创作者平台

```
browser_navigate("https://creator.douyin.com/creator-micro/content/upload")
```

> 注意：`creator.douyin.cn` 可能 DNS 解析失败，使用 `creator.douyin.com`

### 步骤 2：快照页面，选择发布类型

```
browser_snapshot()
```

找到对应按钮并点击：
- **发布视频**：上传视频文件（主流）
- **发布图文**：上传多张图片（类似小红书图文）
- **发布全景视频**：VR 全景内容
- **发布文章**：长文形式

```
browser_click("eN")   # N 是快照中对应按钮的 ref
```

### 步骤 3：上传媒体文件

快照找到 `input[type=file]` 对应的 ref：

```
browser_upload("eN", "/path/to/file.jpg")
```

等待上传完成，再次快照确认上传成功。

### 步骤 4：填写标题和描述

快照找到编辑区：
- **标题框**：placeholder 通常为「添加作品标题」（20 字限制）
- **描述框**：placeholder 通常为「添加作品描述」（1000 字限制）

```
browser_click("eN")
browser_type("eN", "标题内容")

browser_click("eM")
browser_type("eM", "描述内容\n\n#话题标签1 #话题标签2")
```

### 步骤 5：发布设置（可选）

快照找到以下选项按需调整：
- **谁可以看**：公开 / 好友可见 / 仅自己可见
- **保存权限**：允许 / 不允许
- **发布时间**：立即发布 / 定时发布

### 步骤 6：点击发布

```
browser_click("eN")   # 右下角「发布」按钮
```

### 步骤 7：确认发布成功

```
browser_snapshot()
# 或
browser_screenshot()
```

页面显示「发布成功」并跳转到作品管理页面即完成。

---

## 关键技巧

### 元素定位
- 每次操作后重新 `browser_snapshot()` 获取最新 ref
- ref 在每次 snapshot 后重新编号，不要缓存上次的 ref
- 用文本内容定位按钮（如「发布图文」「发布」）

### 内容建议
- 标题：简洁有吸引力，20 字以内
- 描述：分段清晰，加话题标签（#五一假期 #打工人日常）
- 推荐话题：发布页面会推荐热门话题，可点击快速添加

### 上传限制
- **图片**：最大 50MB，支持 jpg/jpeg/png/webp，最多 35 张
- **视频**：最大 16GB，时长 60 分钟以内，支持 mp4/webm
- 推荐图片比例：3:4、4:3（不建议超过 1:2）
- 推荐视频比例：16:9、9:16、3:4、4:3、9:19.5

### 错误处理
- **元素找不到**：重新 snapshot，检查页面是否加载完成
- **上传失败**：检查文件路径是否正确，文件是否存在
- **发布失败**：检查标题/描述是否必填，图片/视频是否上传成功
- **DNS 解析失败**：`creator.douyin.cn` 可能无法解析，改用 `creator.douyin.com`

---

## 示例

用户：帮我发一条五一主题的抖音图文，图片在 /tmp/holiday.jpg

```
1. browser_navigate 打开抖音创作者平台
2. browser_snapshot 查看页面结构
3. browser_click 点击「发布图文」
4. browser_snapshot 等待上传区域出现
5. browser_upload "eN" "/tmp/holiday.jpg"
6. browser_snapshot 确认图片上传成功
7. browser_click + browser_type 填写标题（20字以内）
8. browser_click + browser_type 填写描述+话题
9. browser_click 点击「发布」
10. browser_screenshot 确认发布成功
```

## 发布后

- 发布成功后自动跳转到「作品管理」页面
- 可查看播放量、点赞、评论、收藏等数据
- 作品状态：已发布 / 审核中 / 未通过
