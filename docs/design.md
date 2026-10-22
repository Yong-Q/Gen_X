# Gen_X：构型概率分布学习与生成

日期：2026-10-22。本文件保留最初Bash调度smoke阶段的设计范围。用户随后要求实际跑通生成模型，新阶段见[真实生成计划](real_generation_plan.md)和[运行结果](real_generation_results.md)；仍不使用GPU计算。

## 目标

维护水、非晶和聚合物的生成模型调研、可行技术路线及 PDF；建立可追溯的 Bash/Slurm 入口，实际验证无 GPU 的 smoke。后续再接入现成生成器的推理和训练。本轮不得把合成测试数据、dry-run 或调度检查称为已复现论文生成结果。

## 模型分工

- 势模型：构型到能量、力；优先冻结现成模型，验证不足时再微调。
- 生成模型：学习条件构型分布并采样，可选周期性等变 diffusion、flow matching、normalizing flow。
- 实验反演：用观测约束结构系综，明确非唯一性及势先验依赖。
- 非晶：条件包括组分、密度、冷却/老化历史，不自动等于平衡 Boltzmann 分布。

## 本轮可运行边界

1. 三条路线注册：DM2 非晶扩散；bgmat 单珠水冰 Boltzmann generator；水专用势＋未来全原子生成器。
2. 配置为版本化 JSON，含来源、执行状态、上游入口、模型/数据前置条件。
3. Bash 本地 smoke 验证配置和路由，产生唯一 run ID、manifest 和日志。
4. Bash Slurm 入口支持 dry-run，默认 CPU smoke（单 CPU、短 walltime）；不申请 GPU，不运行训练。
5. 实际提交短 CPU smoke（资源可用时，修复后必要时重新验证），用 sacct/squeue 和落盘结果确认完成。
6. 反馈回环仅运行数据流示范：明确标记的 synthetic fixtures → QA → candidates.jsonl。队列不自动触发 DFT、势重训或生成器训练。
7. 科学运行、依赖安装、真实权重/数据下载与 GPU 推理单列为后续里程碑。

## 安全和可复现

所有写入限本仓库；每次运行创建新结果目录，拒绝覆盖。命令以数组构造，配置内容不经 eval。外部 repo/权重不提交；记录 URL、版本和下载后的 hash。Slurm 使用共享目录，当前 smoke 不使用 node-local scratch。训练或模拟必须经 Slurm。最终只提交本任务文件，用户已授权推送 https://github.com/Yong-Q/Gen_X.git。

## 验证标准

测试覆盖非法路线/缺失字段、重复运行目录、带空格路径、命令失败传播、有效结构不被错误当作已物理验证。验收区分：配置通过、Bash smoke 通过、Slurm CPU smoke 通过、模型推理通过、科学分布验证通过。后两项本轮不预先声称通过。
