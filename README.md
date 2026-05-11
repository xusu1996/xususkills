# xususkills

这是徐宿的个人 Codex 技能库，用来存放、发布和复用自己设计的 Codex skills。

这里的 skill 不是普通提示词，而是一组可以被 Codex 加载的专业工作流程。每个 skill 都有独立的 `SKILL.md`，并可以包含界面元数据、参考资料、脚本和资源文件。

## 当前包含的 Skills

- `dialogue-screenshot-cards`：把真实的人机对话片段整理成适合发布的小红书竖图截图卡片，重点是保留原话、清理隐私、分页排版，不编造内容。
- `thinking-evolution-journal`：分析中文日记、复盘和自由表达内容，输出关于情绪、因果链、成长阶段和长期模式的“思维进化日记”报告。

## 如何安装

在 Codex 中安装 skill 时，可以使用下面的 GitHub 地址。

安装“对话截图卡片”：

    https://github.com/xusu1996/xususkills/tree/main/skills/dialogue-screenshot-cards

安装“思维进化日记”：

    https://github.com/xusu1996/xususkills/tree/main/skills/thinking-evolution-journal

安装完成后，需要重启 Codex，新的 skill 才会出现在可用技能中。

## 如何调用

可以显式点名调用：

    Use $dialogue-screenshot-cards to turn this conversation into vertical screenshot cards.

    Use $thinking-evolution-journal to analyze this diary.

也可以用中文直接说明：

    使用 thinking-evolution-journal 这个 skill，帮我分析这篇日记。

## 文件结构

    skills/
    ├── dialogue-screenshot-cards/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   ├── references/
    │   └── scripts/
    └── thinking-evolution-journal/
        ├── SKILL.md
        ├── agents/openai.yaml
        └── references/

## 说明

每个 skill 都是一个独立文件夹，放在 `skills/` 目录下。

- `SKILL.md` 是必需文件，定义 skill 的名称、触发描述和具体工作流程。
- `agents/openai.yaml` 是推荐文件，用来提供界面显示名称、短描述和默认调用提示词。
- `references/` 用来放需要按需读取的参考资料。
- `scripts/` 用来放可重复执行的脚本工具。
