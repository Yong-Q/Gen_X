# 文档技能来源与维护

为本项目拉取并应用了以下 GitHub skill，均保存在项目内：

| Skill | 用途 | 上游 |
|---|---|---|
| doc-coauthoring | 将上下文整理为可独立阅读的文档，做结构改写及陌生读者检查 | [官方目录](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) |
| frontend-design | HTML教程的布局、排版、导航、移动端与可访问性 | [官方目录](https://github.com/anthropics/skills/tree/main/skills/frontend-design) |
| markdown-mermaid-writing | 科学解释、工程参考和教程的组织，可编辑结构图与源文件保留 | [K-Dense固定版本目录](https://github.com/K-Dense-AI/scientific-agent-skills/tree/593377bb048752abb0152deab9fbb1083a6087df/skills/markdown-mermaid-writing) |

安装位置为项目内 `.agents/skills/`，没有修改全局技能目录。Anthropic来源固定到提交 `dbd4588f9e1033efb41dad4bef2f7947c8993d44`；[原有哈希清单](../.agents/skills-lock.json)保留SHA-256。K-Dense来源固定到 `593377bb048752abb0152deab9fbb1083a6087df`；[新增哈希清单](../.agents/skills-mermaid-lock.json)逐文件记录。上游提供的许可证与署名原样保留；该skill的移植指南和模板含Apache-2.0署名，不能仅按仓库总许可概括。

本轮应用其研究文档模板、证据与范围声明、结构图可编辑源及交付检查原则，沿用本仓库的中文标题样式。三张流程图使用本机Graphviz生成SVG和矢量PDF，保留DOT源；没有为导图安装新的浏览器或运行外部图像API。Markdown写作无需凭证；若日后使用Mermaid CLI，应另行锁定Node、CLI与浏览器版本并实测目标平台。项目级安装不等于技能已在所有后续会话中自动发现；可直接阅读本地SKILL.md使用。

优秀项目的固定版本案例和具体采用方式见[文档案例调研](documentation_patterns.md)。

Markdown是内容源；HTML用于工程教程和交互导航，PDF用于归档和分享。修改内容后重建输出，并检查链接、命令、实际状态与运行证据一致。文献结果、计划里程碑和已执行smoke始终分别标注。
