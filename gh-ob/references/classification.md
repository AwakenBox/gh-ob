# GitHub 知识库分类规则

使用本参考文档来决定仓库笔记应当放在 `D:\Obsidian\Github\GitHub-Knowledge` 的哪个目录下。

## 根目录结构

```text
GitHub-Knowledge/
  00-Dashboard/
  01-AI/
    Agents/
    RAG-Knowledge/
    LLM-Apps/
    Model-Training/
    Inference-Serving/
    Eval-Observability/
    AI-Tools/
    AI-Papers-Research/
  02-Applications/
  03-Libraries-SDKs/
  04-CLI-Tools/
  05-Infra-DevOps/
  06-Data-Engineering/
  07-Mobile-Desktop/
  08-Games-Graphics/
  09-Templates-Boilerplates/
  10-Docs-Research/
  99-Unclassified/
```

## 路由规则

1. 按项目用途分类，而不是按编程语言分类。
2. 如果仓库的主要价值与 AI 相关，始终优先归入 `01-AI/...`。
3. 在有足够仓库证据时，选择最具体的目录。
4. 只有在仓库信息不足时，才使用 `99-Unclassified`。

## AI 子分类

### `01-AI/Agents`

用于 Agent 框架、多 Agent 运行时、可调用工具的 Copilot、工作流 Agent 和编排系统。

### `01-AI/RAG-Knowledge`

用于检索流程、向量数据库、Embedding 工作流、分块处理流程和基于知识库的助手。

### `01-AI/LLM-Apps`

用于面向用户的 LLM 产品，例如聊天应用、Copilot、Prompt 应用或 AI 产品演示项目。

### `01-AI/Model-Training`

用于微调、训练流水线、数据集构建、合成数据生成，以及围绕模型改进的实验项目。

### `01-AI/Inference-Serving`

用于推理引擎、模型网关、服务化部署栈、GPU 部署工具或模型托管基础设施。

### `01-AI/Eval-Observability`

用于评测框架、Tracing、Prompt 测试、实验跟踪、打分和监控。

### `01-AI/AI-Tools`

用于辅助模型工作流但本身不是终端应用或框架的 AI 周边工具。

### `01-AI/AI-Papers-Research`

用于论文实现、研究型仓库、基准测试和与公开研究思路相关的实验性原型。

## 非 AI 分类

- `02-Applications`：完整的终端应用
- `03-Libraries-SDKs`：可复用的库和 SDK
- `04-CLI-Tools`：命令行工具和 Shell 工具
- `05-Infra-DevOps`：部署、Docker、Kubernetes、CI/CD、IaC
- `06-Data-Engineering`：数据流水线、ETL、数据库、分析基础设施
- `07-Mobile-Desktop`：移动端或桌面端应用及框架
- `08-Games-Graphics`：游戏、渲染、图形和多媒体工具
- `09-Templates-Boilerplates`：脚手架、模板、样板工程
- `10-Docs-Research`：纯文档仓库、教程、学习资料

## 命名规则

- 笔记文件名：`owner__repo.md`
- 本地仓库目录名：`owner__repo`
- 优先使用稳定路径，这样后续更新时可以覆盖已有笔记，而不会产生重复文件。
