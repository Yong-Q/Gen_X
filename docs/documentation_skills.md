# 文档技能来源与维护

为本项目拉取并应用了 Anthropic 官方 GitHub 仓库的两个 skill：

| Skill | 用途 | 上游 |
|---|---|---|
| doc-coauthoring | 将上下文整理为可独立阅读的文档，做结构改写及陌生读者检查 | [官方目录](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) |
| frontend-design | HTML教程的布局、排版、导航、移动端与可访问性 | [官方目录](https://github.com/anthropics/skills/tree/main/skills/frontend-design) |

安装位置为项目内 `.agents/skills/`，没有修改全局技能目录。来源固定到提交 `dbd4588f9e1033efb41dad4bef2f7947c8993d44`；[文件哈希清单](../.agents/skills-lock.json)保留每个文件的SHA-256。上游提供的许可证文件原样保留。

Markdown是内容源；HTML用于工程教程和交互导航，PDF用于归档和分享。修改内容后重建输出，并检查链接、命令、实际状态与运行证据一致。文献结果、计划里程碑和已执行smoke始终分别标注。
