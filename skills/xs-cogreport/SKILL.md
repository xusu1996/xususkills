---
name: xs-cogreport
description: "徐宿的认知问题诊断器。Use when the user wants to diagnose a cognitive dilemma by stages, screen whether a problem belongs to cognition, collect the user's problem story, ask for keyword usage and relationships, and output only the diagnosis level supported by user-provided language. Trigger phrases include: /xs-cogreport, 认知问题, 认知困境, 怎么思考, 认知体系构建, 知识体系构建, 我想不明白, 这个概念让我卡住了, 我分不清, 帮我诊断认知问题."
---
# xs-cogreport：认知问题诊断器

本 skill 是徐宿开发的认知问题诊断工具，只根据用户已提供的语言材料做分层诊断。

本 skill 不补全用户理解，不纠正概念，不替用户生成解释框架。

本 skill 不写入文件，不创建资产库，不修改知识库文章。

---
## 状态约定

`停止 skill` 表示：输出当前阶段指定内容；停止读取后续 Phase；结束本次 assistant 回复；等待用户下一条输入。

需要跨轮接续的模板必须使用固定问题首句，Phase A 只根据上一轮固定问题首句恢复入口。

每个 Phase 只能有一个主规则文件决定 `路由结果`。

---
## 工作流

### Phase A：恢复入口

读取 `references/state-rules.md`，按 `路由结果` 进入 Phase 0、Phase 1、Phase 3。

### Phase 0：职责筛选

读取 `references/start-rules.md`，按 `路由结果` 进入 Phase 1 或执行 `停止 skill`。

### Phase 1：收集困境叙述

读取 `references/problem-rules.md`，按 `路由结果` 进入 Phase 2 或执行 `停止 skill`。

### Phase 2：第一轮诊断

读取 `references/first-diagnosis-rules.md` 和 `references/report-template.md`，输出第一轮诊断后执行 `停止 skill`。

### Phase 3：收集解释材料

读取 `references/explanation-rules.md`，按 `路由结果` 进入 Phase 4 或 Phase 6。

### Phase 4：第二轮诊断

读取 `references/second-diagnosis-rules.md`，生成第二轮诊断材料后进入 Phase 6。

### Phase 6：最终诊断

读取 `references/final-diagnosis-rules.md` 和 `references/report-template.md`，输出最终诊断后执行 `停止 skill`。

---
## 说话方式

- 默认中文。
- 平铺直叙。
