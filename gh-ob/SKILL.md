---
name: gh-ob
description: 克隆或下载 GitHub 仓库，将源码优先同步到 `D:\Obsidian\Github\Source-Repos`，阅读 README 和关键项目文件，按 AI 优先的分类体系归档，总结安装与使用方式，并将结构化 Markdown 笔记保存到 `D:\Obsidian\Github`。当 Codex 收到一个或多个 GitHub 仓库链接，且目标是归档项目知识、建立个人仓库资料库、比较工具或将仓库文档沉淀为可复用的 Obsidian 笔记时使用此技能。
---

# GitHub 仓库归档到 Obsidian

## 概述

将一个或多个 GitHub 仓库链接转化为可复用的 Obsidian 笔记，并保存到 `D:\Obsidian\Github`。
优先依据仓库中的真实证据进行判断，不凭空猜测，最终笔记要便于以后快速回顾和复用。

## 默认路径

- Obsidian 仓库根目录：`D:\Obsidian\Github`
- 知识库根目录：`D:\Obsidian\Github\GitHub-Knowledge`
- 默认本地源码目录：`D:\Obsidian\Github\Source-Repos`
- 笔记文件命名格式：`owner__repo.md`

如果知识库根目录或目标分类目录还不存在，只创建当前笔记所需的目录以及 `00-Dashboard`。
如果源码目录不存在，就创建 `D:\Obsidian\Github\Source-Repos` 以及当前仓库所需的子目录。

## 工作流程

### 1. 规范化仓库链接

- 尽量将 GitHub 深层链接还原为仓库根链接。
- 在进行任何文件操作或写笔记之前，从链接中提取 `owner` 和 `repo`。
- 如果本地已经有对应仓库，优先复用已有副本。

### 2. 安全获取源码

- 默认优先将源码同步到 `D:\Obsidian\Github\Source-Repos\owner__repo`。
- 始终优先运行 `scripts/fetch_github_repo.py <repo-url> --target-root "D:\Obsidian\Github\Source-Repos" --repair-broken --json`，不要手写临时的 clone / curl / 解压流程，除非脚本本身坏了。
- 脚本的同步顺序是：
  1. 已有 git 仓库：执行 `fetch --all --tags --prune`，可快进时再 `pull --ff-only`
  2. 有 `gh` 且已登录：优先 `gh repo clone`，并传递浅克隆参数
  3. 有 `git`：回退到原生 `git clone --depth=1 --filter=blob:none`
  4. 前面都失败：回退到 GitHub API `zipball` 下载并解压为源码快照
- 如果目标目录里只有残缺的 `.git` 元数据、存在锁文件，或明显是一次中断的 clone，优先使用 `--repair-broken` 让脚本把坏目录改名备份后再重试。
- 只有在脚本明确失败且用户要求保留手工路径时，才使用脚本外的下载方式。
- 不要自动执行来历不明的安装脚本。

### 3. 检查项目内容

- 先阅读 README。
- 再检查最能说明安装与使用方式的文件：
  - Node.js：`package.json`、`pnpm-lock.yaml`、`package-lock.json`、`yarn.lock`
  - Python：`pyproject.toml`、`requirements.txt`、`requirements-*.txt`、`setup.py`
  - Rust：`Cargo.toml`
  - Go：`go.mod`
  - Java/Kotlin：`pom.xml`、`build.gradle`、`build.gradle.kts`、`settings.gradle`
  - 容器相关：`Dockerfile`、`compose.yml`、`docker-compose.yml`
  - 自动化流程：`.github/workflows/`
- 识别真实项目类型、技术栈、安装路径、运行命令和关键目录。
- 优先采用 README 中明确写出的命令，其次参考清单文件推断，只有在没有足够证据时才进行保守推测。

### 4. 判断是否需要安装

- 默认在不完整安装项目的前提下完成总结。
- 只有当标准包管理器命令短小、安全，且确实能显著提升总结质量时，才执行安装。
- 在进行耗时构建前，优先读取元数据或执行无副作用的探测命令。
- 如果安装需要密钥、付费服务、管理员权限或存在破坏性操作，应停止执行并明确说明原因。

### 5. 为仓库分类

- 在选择目标目录前，先阅读 `references/classification.md`。
- 应用 AI 优先分类规则：
  - 如果仓库的核心价值是 AI、LLM、Agent、RAG、模型训练、推理或评测，即使它同时也是 CLI、库或 Web 应用，也优先归入 `01-AI`。
  - 在有足够证据的前提下，尽量选择最具体的 AI 子分类。
- 只有在无法有把握地分类时，才使用 `99-Unclassified`。

### 6. 写入 Obsidian 笔记

- 使用 `references/note-template.md` 作为输出结构。
- 将笔记保存到 `D:\Obsidian\Github\GitHub-Knowledge\<分类路径>\owner__repo.md`。
- 除非用户明确要求其他语言，否则使用中文撰写总结。
- 命令、文件名和路径统一使用等宽格式。
- 笔记中要包含 GitHub 链接、本地仓库路径、分类、安装步骤、使用命令、重要文件和简短的实用评价。
- “本地仓库路径” 默认写成 `D:\Obsidian\Github\Source-Repos\owner__repo`。
- 脚本返回 JSON 时，优先读取其中的 `status`、`sync_method`、`local_copy_type`、`archive_path`、`revision` 和 `attempts`。
- 如果 `local_copy_type` 是 `git-repo`，可以写成“本地已同步 git 仓库”；如果是 `source-snapshot`，必须明确写成“源码快照/zip 解压副本”，不要让人误以为本地带有 `.git` 历史。
- 如果此次未能成功同步源码，要明确写出原因、失败方法和当前目录状态，不要假装已经下载完成。

### 7. 维护轻量索引

- 如果 `D:\Obsidian\Github\GitHub-Knowledge\00-Dashboard\分类索引.md` 已存在，就向其中添加新笔记链接。
- 如果用户提供多个仓库，默认每个仓库生成一篇笔记；只有在用户明确要求时，才生成合并对比笔记。

## 笔记必须包含的内容

每篇仓库笔记都必须包含以下部分：

- 仓库名称和 URL
- 一句话项目总结
- 主分类和子分类
- 为什么值得关注
- 技术栈
- 安装步骤
- 启动或使用命令
- 重要目录和文件
- 风险、限制或前置条件
- 简短的“适合我吗”判断，便于以后回顾

## 质量要求

- 不要声称某个命令可用，除非它来自 README、清单文件，或已经被你亲自验证过。
- 优先写高信息密度的简洁总结，不要机械复制 README 内容。
- 要明确指出缺失的前置条件、过时文档或可疑的安装步骤。
- 如果仓库内容不完整或文档质量较差，要明确保留不确定性。
- 如果源码同步失败，要在最终说明和 Obsidian 笔记里同时注明失败原因、已尝试的方法，以及当前是否存在半截仓库目录。
- 如果同步脚本成功返回 `source-snapshot`，要把它视为“可读源码已同步”而不是“git clone 成功”。

## 示例请求

- 用这个 GitHub 链接帮我归档到 Obsidian
- 克隆这个仓库，总结怎么安装和启动
- 看看这个 AI agent 项目值不值得学，并存成笔记
- 把这个 GitHub 项目分类后写进我的知识库
