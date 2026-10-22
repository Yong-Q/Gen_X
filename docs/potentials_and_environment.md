# 机器学习势、运行环境与复用边界

调研日期：2026-10-22。以下机器学习水势的信息来自网页、官方仓库和本机只读检查；本节所列MLP权重尚未下载和加载。已跑通的bgmat生成器及其经典mW势另见[独立示例](real_generation_results.md)。

## 势是否需要重训

第一阶段冻结一个已有参考势，训练或复用生成器。这样才能区分生成器的分布误差与势本身的物理误差。仅当独立能量、力或目标条件下的物性验证失败，才考虑补充量化参考数据、微调势。生成器产生了高能结构，并不自动意味着势错了，也可能是生成器给出了不合理构型。

水有现成的复用依据。PNAS 2025 的 *Computational investigation of water glasses using machine-learning potentials* 使用 DP_SCAN 和 DP_MBpol 研究低密度、高密度非晶冰，并未专门用非晶冰重新训练这两个模型。这支持先验证已有势，但不保证任意淬火路径和温压均准确。[论文](https://doi.org/10.1073/pnas.2509609122)

## 可用水势

| 项目 | 已核实内容 | 使用边界 |
|---|---|---|
| DNN@MB-pol | 2023 水相图模型，2025 液—液临界点工作复用；DeePMD TensorFlow `.pb`；可接 LAMMPS | 优先作为水路线的参考模型；新温压、淬火历史和核量子效应需分别验证 |
| DP-SCAN | PRL 2021 水相图模型体系，PRL 2022 研究液—液相变 | 适合模型对照；参考泛函误差会改变温标和相界，不能直接将模型温压当实验真值 |
| MACE-POLAR-1 | 通用分子模型，含长程静电与极化 | 原始论文水验证主要在270–330 K、1 atm，报告密度及结构偏差；本轮不将其设为已验证的过冷水基准 |

DNN@MB-pol 的官方资源：

- [作者模型说明](https://paesanigroup.ucsd.edu/many-body-potentials/dnn-mb-pol.html)。
- [作者推荐的 graph-compress.pb](https://raw.githubusercontent.com/paesanilab/Quantum-phase-diagram-of-water/main/Model/GraphFiles/graph-compress.pb)，官方仓库条目约36.9 MB。“compress”指运行时表格优化，不能理解成文件一定更小。
- [完整数据与模型归档](https://zenodo.org/records/7863744)，约14.9 GB；推理不需要先下载整个归档。
- [2025液—液相变论文](https://doi.org/10.1038/s41567-024-02761-0)。

DP-SCAN 的官方资源：

- [PRL 2022正式数据归档](https://doi.org/10.34770/hycg-af09)。本轮其页面访问受限，未核实内部精确权重路径。
- [作者后续仓库中的同源 graph.pb](https://raw.githubusercontent.com/PabloPiaggi/mishima-melting-lines-2023/main/DeepPotentialModel/graph.pb)；[模型说明](https://github.com/PabloPiaggi/mishima-melting-lines-2023/tree/main/DeepPotentialModel)对应 PRL 126, 236001。本轮未将该文件与2022归档做二进制同一性验证。
- [MACE-POLAR原始论文](https://arxiv.org/abs/2602.19411)。

“DNN@MB-pol”“DP_MBpol”“MB-pol(2023)”和其他基于MB-pol训练的模型不能只凭简称混用。最终每次运行必须保存：来源URL、上游commit、权重SHA-256、类型映射、单位、截断、推理后端及版本。上面DNN@MB-pol归档标记为`other-open`，未确认标准MIT/GPL许可证；可获得不等于可任意再分发，因此本仓库不打包上游权重。

## 本机已观察到的能力

| 检查项 | 观察结果 | 尚未验证 |
|---|---|---|
| 调度 | `sbatch`、`squeue`、`sinfo`、`scontrol`可用；用户确认使用Slurm | GPU任务本轮不提交 |
| CPU smoke资源 | `debug`分区可查询；按单CPU、短walltime提交 | 每次执行时重新查资源，不承诺排队时间 |
| GPU | 集群列出RTX4090等GPU节点；用户说明GPU已满 | 不因节点显示mixed就认定GPU空闲 |
| Python基础环境 | Python3.10、PyTorch2.12、ASE3.22、NumPy、SciPy、RDKit可发现 | 不等于适配全部上游checkpoint |
| DeepMD | 工作区旁已有CPU及CUDA版DeepMD3.2环境和`dp`/`lmp`入口 | 尚未加载上述水模型 |
| 生成模型依赖 | 当前基础环境缺e3nn、PyG、JAX等 | 应为每条真实路线建立隔离环境并锁定版本 |
| PDF工具 | Pandoc、XeLaTeX、中文字体可用 | PDF输出另做文本/页面检查 |

系统中PBS命令与Slurm共存，但本项目的作业脚本只用Slurm。CPU smoke使用Python标准库和共享目录，不涉及模型推理、训练、GPU或节点本地scratch。

## 运行状态分层

1. **文献核实**：作者报告了该方法和结果。
2. **入口smoke**：配置、命令、日志和反馈队列能连通。
3. **模型推理**：实际加载指定权重并生成构型。
4. **分布验证**：结构、能量、相关统计和有效样本量满足基准。
5. **科学结论**：在独立证据及不确定性分析下支持物理判断。

这些层次不能互相替代。最初阶段只完成第2层；随后bgmat的mW冰示例已完成第3层及基本输出检查，见[运行结果](real_generation_results.md)。这里列出的DNN@MB-pol、DP-SCAN与MACE-POLAR势权重仍未在本项目加载验证。
