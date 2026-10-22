# Gen_X

学习或推断原子构型的概率分布，再采样水、非晶及聚合物结构。

本仓库同时维护文献调研、技术路线、PDF和可追溯的执行记录。当前阶段按用户要求仅验证 **Bash → Slurm CPU smoke → 日志/manifest → 合成示例反馈队列**；不占用GPU，不将smoke当作论文复现。

## 阅读入口

- [HTML工程教程](site/index.html)：离线可打开，含导航、检索、复制命令和证据链接。
- [文献调研](docs/literature_survey.md)：别人实际做到了什么，数据、尺度和代码边界。
- [技术路线](docs/technical_roadmap.md)：模型选型、里程碑、验收和两层反馈回环。
- [势模型及环境](docs/potentials_and_environment.md)：复用权重、版本与运行前置条件。
- [执行结果](docs/smoke_results.md)：实际命令、作业及验证记录。
- [PDF目录](reports/)：调研与技术路线快照。
- [设计范围](docs/design.md)和[实施计划](docs/implementation_plan.md)。
- [文档技能来源](docs/documentation_skills.md)：从官方GitHub拉取的两个项目级skill及固定版本。

## 概率模型与势模型

生成模型学习 `q_theta(configuration | conditions)`；机器学习势计算 `U_phi(configuration)`及其梯度。势可提供参考MD数据、能量引导和物理检查，其内部特征不自动具备逆向解码能力。非晶分布还依赖制备历史，不能仅凭独立采样就声称是无偏平衡分布。

## Smoke入口

```bash
# 本地：只运行标准库配置/路由/合成数据检查
bash scripts/local_smoke.sh --config configs/dm2_smoke.json

# 检查Slurm命令，不提交
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --dry-run

# 提交一个短CPU smoke，无GPU请求
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --partition debug
```

另有`configs/bgmat_smoke.json`和`configs/mbpol_water_smoke.json`。每次使用新run目录；失败应返回非零状态。合成测试构型只用于验证数据流，不能用于论文结构统计。真实模型依赖及推理是后续独立阶段。

## 资源管理

上游代码、模型权重和训练数据不提交进Git。真实运行将锁定上游commit与模型hash，依赖安装限项目隔离环境。训练/模拟经Slurm运行。小型配置、日志、JSON结果和PDF可追踪。

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
