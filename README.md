# gh-ob

`gh-ob` 是一个面向 Codex 的本地技能，用来把 GitHub 仓库整理成适合长期积累的 Obsidian 笔记，同时尽量把源码同步到本地，方便后续搜索、复核和二次分析。

它围绕一个或多个 GitHub 仓库链接，完成这些事情：

- 优先把源码同步到本地目录
- 阅读 `README.md` 和关键项目文件
- 按 AI 优先的分类体系归档
- 总结安装与使用方式
- 生成结构化 Markdown 笔记并写入 Obsidian

## 适用场景

适合这些需求：

- 建立个人 GitHub 项目知识库
- 批量整理 AI、Agent、RAG、LLM 相关仓库
- 对新仓库做快速可复用的安装与使用总结
- 把零散仓库文档沉淀进 Obsidian

## 当前能力

当前版本不只是“说明型技能”，还自带源码同步脚本：

- 优先更新已有本地 git 仓库
- 优先尝试 `gh repo clone`
- 回退到原生 `git clone`
- 最后回退到 GitHub API `zipball` 下载
- 可以区分本地副本到底是 `git-repo` 还是 `source-snapshot`
- 可以输出结构化 JSON，方便后续流程消费

## 仓库结构

```text
gh-ob-repo/
  README.md
  .gitignore
  gh-ob/
    SKILL.md
    agents/
      openai.yaml
    references/
      classification.md
      note-template.md
    scripts/
      fetch_github_repo.py
      tests/
        test_fetch_github_repo.py
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
git clone https://github.com/AwakenBox/gh-ob.git
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

## 默认路径

默认配置如下：

- Obsidian 根目录：`D:\Obsidian\Github`
- 知识库目录：`D:\Obsidian\Github\GitHub-Knowledge`
- 本地源码目录：`D:\Obsidian\Github\Source-Repos`
- 笔记文件名格式：`owner__repo.md`

如果你想改默认路径，主要修改这些文件：

- `gh-ob/SKILL.md`
- `gh-ob/references/classification.md`
- `gh-ob/references/note-template.md`
- `gh-ob/scripts/fetch_github_repo.py`

## 同步脚本

核心脚本是：

- [gh-ob/scripts/fetch_github_repo.py](gh-ob/scripts/fetch_github_repo.py)

典型用法：

```bash
python gh-ob/scripts/fetch_github_repo.py https://github.com/owner/repo --target-root "D:\Obsidian\Github\Source-Repos" --repair-broken --json
```

这个脚本会返回结构化结果，关键字段包括：

- `status`
- `sync_method`
- `local_copy_type`
- `revision`
- `archive_path`
- `attempts`

其中：

- `local_copy_type = git-repo` 表示本地是完整 git 仓库
- `local_copy_type = source-snapshot` 表示本地只是源码快照，不带 `.git` 历史

## 测试方式

这个仓库现在带有最基础的回归测试：

```bash
python -m unittest discover -s gh-ob/scripts/tests -p "test_*.py" -v
```

也可以先做语法检查：

```bash
python -m py_compile gh-ob/scripts/fetch_github_repo.py
```

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
- 本地副本类型
- “适合我吗”判断

详细模板见：

- [gh-ob/references/note-template.md](gh-ob/references/note-template.md)

## 发布说明

这个仓库发布的是技能目录本身，不是整套 Codex 配置。

如果后续继续演进，推荐保持这条约定：

- 所有自动化逻辑放进 `gh-ob/scripts/`
- 所有人类说明和工作流规则放进 `gh-ob/SKILL.md`
- 所有输出结构和分类规则放进 `gh-ob/references/`
