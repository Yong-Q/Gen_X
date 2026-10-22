# Gen_X

面向原子构型概率分布学习与生成的研究项目仓库，支持逐步开展水、非晶和聚合物课题。

仓库容纳具体研究项目、可复用的运行工具、模型与数据接口、验证和反馈流程。文献调研与教程是其中的文档模块；单个模型复现不会成为整个项目的定义。

## 项目结构

| 位置 | 职责 |
|---|---|
| [projects/](projects/) | 独立课题与模型示例的入口、假设和结果说明 |
| `scripts/`、`configs/` | 可复用的运行入口、配置、模型与来源约定 |
| `tests/` | 软件行为与关键接口测试 |
| `runs/` | 小型可追溯运行记录；每次运行使用新目录 |
| `docs/`、`site/`、`reports/` | 文献、方法、工程教程及HTML/PDF快照 |
| `external/`、`.venv*/` | 本地上游代码与隔离环境，不纳入Git |

## 课题入口

- [非晶构型概率分布迁移：研究方案](projects/amorphous_generation/README.md)
- [单珠水冰：预训练 bgmat 生成闭环](projects/water_ice_bgmat/README.md)
- 非晶、全原子水与聚合物的后续路线见[技术路线](docs/technical_roadmap.md)。

## 阅读入口

- [HTML工程教程](site/index.html)：离线可打开，含导航、检索、复制命令和证据链接。
- [研究方案](docs/research_program.md)与[生成理论推导](docs/generative_theory.md)：科学动机、可检验假设、数学基础及详细流程。
- [文献调研](docs/literature_survey.md)：别人实际做到了什么，数据、尺度和代码边界。
- [技术路线](docs/technical_roadmap.md)：模型选型、里程碑、验收和两层反馈回环。
- [势模型及环境](docs/potentials_and_environment.md)：复用权重、版本与运行前置条件。
- [执行结果](docs/smoke_results.md)：实际命令、作业及验证记录。
- [PDF目录](reports/)：调研与技术路线快照。
- [设计范围](docs/design.md)和[实施计划](docs/implementation_plan.md)。
- [文档案例](docs/documentation_patterns.md)与[技能来源](docs/documentation_skills.md)：GitHub参考、项目级skill及固定版本。

## 使用与开发

先在`projects/`选择课题，再按其说明准备数据、模型和运行环境。调度接口入门见[教程](docs/tutorial.md)，真正的预训练推理见各项目文档；合成测试与真实构型不可混用。

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_html.py
```

## 资源管理

上游代码、模型权重和训练数据不提交进Git。每条实际路线锁定上游commit与模型hash，依赖安装限项目隔离环境。训练/模拟经Slurm运行；小型配置、生成示例、日志、JSON结果和PDF可追踪。

## 更新PDF

```bash
bash tools/build_pdfs.sh reports/<新的快照目录名>
```

此命令从文档源生成PDF，并拒绝覆盖已有PDF。每轮调研或运行更新保留新的快照。
PDF内的仓库证据链接指向GitHub；HTML中的证据链接可随完整仓库离线访问。

## 重建HTML教程

```bash
python3 tools/build_html.py
# 如需浏览器HTTP预览，从仓库根目录提供服务
python3 -m http.server 8000
```

打开 `http://localhost:8000/site/`。也可以直接打开 `site/index.html`；页面不依赖外部CDN。HTTP服务应以仓库根目录为根，以便访问运行证据和PDF。
