# gh-ob

`gh-ob` 是一个用于 Codex 的本地技能，用来把 GitHub 仓库整理成适合长期积累的 Obsidian 笔记。

它会围绕一个或多个 GitHub 仓库链接，完成这些事情：

- 克隆或下载仓库
- 阅读 `README` 和关键项目文件
- 按 AI 优先的分类体系归档
- 总结安装与使用方式
- 把结构化 Markdown 笔记写入 Obsidian

## 适用场景

适合这些需求：

- 建立个人 GitHub 项目知识库
- 批量整理 AI 项目、Agent 项目、RAG 项目
- 对新仓库做快速可复用的安装与使用总结
- 把零散仓库文档沉淀进 Obsidian

## 仓库结构

```text
gh-ob-repo/
  README.md
  gh-ob/
    SKILL.md
    agents/
      openai.yaml
    references/
      classification.md
      note-template.md
```

`gh-ob/` 目录本身就是技能目录。

## 安装方式

### 方式一：直接复制到用户技能目录

把 `gh-ob/` 目录复制到：

```text
~/.codex/skills/
```

在 Windows 上通常对应：

```text
C:\Users\<你的用户名>\.codex\skills\
```

复制完成后，技能路径应类似于：

```text
C:\Users\<你的用户名>\.codex\skills\gh-ob
```

### 方式二：从本仓库克隆后再复制

```bash
git clone <你的仓库地址>
```

然后把仓库中的 `gh-ob/` 目录复制到你的 Codex 技能目录里。

## 使用方式

在 Codex 对话里显式调用：

```text
使用 $gh-ob 处理这个 GitHub 链接：https://github.com/owner/repo
```

也可以这样说：

```text
使用 $gh-ob 归档这个仓库：https://github.com/owner/repo
```

批量处理时可以一次给多个链接：

```text
使用 $gh-ob 批量整理这些仓库，并分别生成笔记：
https://github.com/owner/repo1
https://github.com/owner/repo2
https://github.com/owner/repo3
```

## 默认行为

默认配置如下：

- Obsidian 根目录：`D:\Obsidian\Github`
- 知识库目录：`D:\Obsidian\Github\GitHub-Knowledge`
- 本地仓库缓存目录：`C:\Users\wobes\GitHub-Cache`
- 笔记文件名格式：`owner__repo.md`

如果你想改默认路径，可以编辑：

- `gh-ob/SKILL.md`
- `gh-ob/references/classification.md`
- `gh-ob/references/note-template.md`

## 分类规则

这个技能采用 AI 优先分类：

- 只要仓库核心价值是 AI、LLM、Agent、RAG、训练、推理或评测，就优先归到 `01-AI`
- 再根据仓库特征细分到 `Agents`、`RAG-Knowledge`、`LLM-Apps`、`Model-Training`、`Inference-Serving` 等子类

详细规则见：

- [gh-ob/references/classification.md](gh-ob/references/classification.md)

## 输出模板

生成的 Obsidian 笔记会包含这些信息：

- 仓库名称和 URL
- 一句话项目总结
- 主分类和子分类
- 技术栈
- 安装步骤
- 启动或使用命令
- 关键目录与文件
- 风险和前置条件
- “适合我吗”判断

详细模板见：

- [gh-ob/references/note-template.md](gh-ob/references/note-template.md)

## 当前版本说明

当前版本是“流程型技能”：

- 已具备完整的技能说明、分类规则和输出模板
- 适合直接在 Codex 中调用
- 还没有附带自动执行脚本

如果后续需要，可以继续扩展 `scripts/`，把克隆、分类、写入 Obsidian 的过程做成半自动或全自动。
