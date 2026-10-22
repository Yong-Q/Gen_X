# 单珠水冰的预训练生成示例

本项目接入作者公开的bgmat normalizing-flow权重，目标是在Slurm CPU节点实际采样216粒子的mW立方冰构型，完成加载、生成、导出及基本检查。

- 温度：200 K；数密度：0.033567184 Å⁻³。
- 模型：一粒子代表一水分子的mW模型；不是带显式氢的液态水。
- 生成器：作者在216粒子体系训练的预训练可逆流；不重新训练。
- [上游论文与代码](https://github.com/maxschebek/bgmat)。
- [实施与验收约定](../../docs/real_generation_plan.md)。
- 运行入口：`scripts/run_bgmat_cpu.sh`；实际采样适配器：`scripts/bgmat_inference.py`。
- 已完成真实CPU推理：8个216粒子构型，作业96496成功，输出为`runs/bgmat_real_20261022/`。
- [复跑教程和结果解释](../../docs/real_generation_results.md)。
- [可视化构型](../../runs/bgmat_real_20261022/samples.extxyz)和[成功manifest](../../runs/bgmat_real_20261022/manifest.json)。

本页是独立模型示例，仓库其他研究课题不受此体系、温度或网络架构限制。
