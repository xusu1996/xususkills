---
name: dialogue-screenshot-cards
description: Create truthful screenshot-style social cards from real human-AI conversations. Use when the user wants to turn Codex, ChatGPT, Claude, Gemini, or other AI dialogue excerpts into clean Xiaohongshu vertical images, chat bubbles, conversation screenshots, or social media cards while preserving original wording, removing private details, paginating long exchanges, and avoiding invented content.
---

# 对话截图卡片生成器

把真实人机对话片段整理成适合发布的小红书竖图截图卡片。

默认目标是“真实对话现场”，不是知识海报或改写后的内容包装。保持原话、顺序和语气，只做隐私清理、分页、排版和视觉统一。

## 默认输出

- 尺寸：1080 x 1440
- 格式：默认生成 SVG；使用 `--png` 时同时导出 PNG
- 默认输出目录：`Codex应用工作台/4-对话截图卡片/exports/日期-主题`
- 默认风格：白色微信气泡版（`style=wechat` + `theme=light`）
- 可选风格：真实 Codex 日记室版（`style=codex-real`）
- 数量：由真实内容长度决定，不自动扩写成更多页
- 标题：第一张固定显示“徐宿的思维进化日记”，副标题显示“关于 xxx”
- 多页：第二张开始不显示标题和副标题，直接显示对话内容
- 分页：识别标题、正文和空行，避免孤立标题，减少不必要的大块留白
- 字体：手机端可读性优先，正文使用接近微信聊天截图的较大字号
- Markdown：将 `### 标题`、加粗、行内代码等标记渲染成普通文本
- 图片：大图模式独立展示；同一条消息同时包含图片和长文字时，默认图片在上、文字在下
- 字体：PNG 优先使用 PingFang SC；标题使用字体本身的 Semibold/Medium 字重，不使用伪加粗

## 工作流程

1. 确认用户提供的是对话文本、聊天记录、文件，或当前窗口中可定位的对话范围。
2. 读取 `references/content-rules.md` 和 `references/style-guide.md`。
3. 保留真实发言顺序和原文，按用户/AI 两类角色整理消息。
4. 遮盖隐私；不要改写观点和语气。
5. 图片使用大图模式，保持比例并自动缩放；同一消息内默认图片先于长文字展示。
6. 按自然消息边界和段落可读性分页；`codex-real` 风格的续页左上角显示“继续”。
7. 使用 `scripts/render_cards.py` 生成卡片，并给出文件位置。

## 对话范围输入

用户可能不粘贴完整对话，而是指定当前窗口中的范围，例如：

- “把我们从 xxx 到 xxx 的完整对话做成竖图卡片”
- “把刚才关于 skill 是什么的那段做成卡片”
- “把这一轮关于文件夹结构的讨论生成图片”

处理规则：

1. 只从当前窗口上下文中定位范围。
2. 保留范围内的真实消息顺序和原文。
3. 如果起点或终点不清楚，先问一个具体确认问题。
4. 不要凭记忆补全上下文中不存在的内容。
5. 在目标对话所在窗口调用本 skill 时，可以直接使用当前窗口上下文定位范围。
6. 在一个窗口要求处理另一个窗口的对话时，要求用户在目标窗口调用本 skill，或粘贴原文，或提供保存好的文本/JSON/Markdown 文件。

窗口边界规则：在哪里调用，就只能可靠使用哪里的当前上下文。不要声称可以直接读取另一个窗口的聊天记录。

## 真实性规则

- 不添加用户没有说过的话。
- 不添加 AI 没有说过的话。
- 不把多段不同上下文拼成连续对话，除非标注“节选”。
- 不为了传播效果改写原话。
- 不自动补充标题党、结论、金句或引导关注。
- 可以调整换行、分页和视觉层级；同一消息内图片先于长文字展示属于视觉层级调整。
- 可以删除无关寒暄、重复内容和操作噪音，但删除后要保持语义不变。
- 可以用 `...` 标记省略。
- 可以遮盖本地路径、账号、姓名、联系方式、密钥、订单号等隐私。

如果用户明确要求“帮我改写”“帮我做成传播卡片”“帮我补标题”，可以进入创作模式；进入创作模式前先说明这会降低原始截图感。

## 内容选择

优先保留真实问题、AI 的关键解释、从模糊到清晰的转折、共同思考过程。优先移除本地绝对路径、系统噪音、过长命令输出、重复确认和隐私内容。

## 渲染脚本

使用脚本生成卡片：

```bash
python3 skills/dialogue-screenshot-cards/scripts/render_cards.py input.json --out output-dir
```

如果不传 `--out`，脚本会自动创建：

```text
Codex应用工作台/4-对话截图卡片/exports/YYYY-MM-DD-主题
```

如果当前 Python 环境安装了 Pillow，可以同时导出 PNG：

```bash
python3 skills/dialogue-screenshot-cards/scripts/render_cards.py input.json --png
```

默认生成白色微信气泡版。切换方式：

```bash
# 白色微信气泡版，默认
python3 skills/dialogue-screenshot-cards/scripts/render_cards.py input.json --png

# 黑色微信气泡版
python3 skills/dialogue-screenshot-cards/scripts/render_cards.py input.json --theme dark --png

# 真实 Codex 日记室版
python3 skills/dialogue-screenshot-cards/scripts/render_cards.py input.json --style codex-real --png
```

也可以在 JSON 中写：

```json
{
  "style": "codex-real",
  "theme": "light"
}
```

`style=wechat` 支持 `theme=light/dark`；`style=codex-real` 固定为白色日记室窗口感。

输入 JSON 示例：

```json
{
  "title": "Skill 是什么？",
  "subtitle": "关于 skill 的创造",
  "style": "wechat",
  "theme": "light",
  "messages": [
    {
      "role": "user",
      "text": "我现在对一个概念很感兴趣，skill 是什么？"
    },
    {
      "role": "assistant",
      "text": "Skill 可以理解成一份专业说明书加工作流程。"
    },
    {
      "role": "user",
      "text": "你看这张图。",
      "images": [
        "/absolute/path/to/image.jpg"
      ]
    }
  ]
}
```

图片也可以带说明：

```json
{
  "role": "user",
  "text": "这是我想对比的参考图。",
  "images": [
    {
      "path": "/absolute/path/to/image.jpg",
      "caption": "参考图"
    }
  ]
}
```

脚本会按内容长度自动生成：

- `card-01.svg`
- `card-01.png`（使用 `--png` 时）
- `card-02.svg`
- `preview.html`

## 输出给用户

完成后简洁说明：

- 生成了几张卡片
- 文件在哪里
- 使用了暗色还是亮色主题
- 是否做过隐私遮盖或省略

不要长篇解释实现细节，除非用户要求。
