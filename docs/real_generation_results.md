# bgmat：真正跑通的预训练构型生成

运行日期：2026-10-22。这个独立示例完成了**固定源码和权重 → 实际采样 → 坐标导出 → 基本验证**，与此前使用人工坐标的synthetic smoke分开记录。

## 1. 生成了什么

| 项目 | 实际结果 |
|---|---|
| 生成器 | 作者预训练bgmat，可逆耦合流和局部图网络 |
| 已加载参数 | 7,972,860个；不是随机初始化权重 |
| 物理模型与相态 | mW单珠水、立方冰；每个粒子代表一水分子，无显式H |
| 条件 | 200 K，数密度0.033567184 Å⁻³，边长约18.600 Å |
| 生成量 | 8个不同构型，每个216粒子 |
| 后处理 | 只做周期坐标包装；没有能量最小化、MD、筛选或重采样 |
| 运行资源 | 2 CPU、8 GB内存申请；没有申请或使用GPU |
| Slurm | 作业96496，COMPLETED，退出码0:0；总耗时87秒 |
| 模型推理 | 首个样本21.37秒，含JIT；其后约2.11–2.14秒/样本 |

作业位于`gpu`分区的节点，但`ReqTRES/AllocTRES`均仅有CPU、内存和节点，JAX设备为`TFRT_CPU_0`。原因是普通CPU分区满载，GPU节点仍有空闲CPU。分区名字不能用于判断是否申请了GPU。

这说明**真实预训练生成流程可以执行**。它不等于已复现论文中的统计精度、尺寸外推或自由能结果，也不等于生成了常温液态水。

## 2. 数据和证据

- [samples.extxyz](../runs/bgmat_real_20261022/samples.extxyz)：8帧周期构型，可用ASE或结构可视化软件读取。`O`是显示标签；计算质量密度时应按一个mW粒子对应一个水分子，而不是氧原子质量。
- [samples.npz](../runs/bgmat_real_20261022/samples.npz)：坐标、盒子、能量、两类log score及重要性权重。
- [samples.csv](../runs/bgmat_real_20261022/samples.csv)：逐构型能量、最短距离和权重。
- [manifest.json](../runs/bgmat_real_20261022/manifest.json)：来源、运行条件、版本、参数数目、时间和输出哈希。
- [独立读取验证](../runs/bgmat_real_20261022/independent_validation.json)：数组形状、有限数值、PBC范围、权重归一化及extxyz帧数检查。
- [采样日志](../runs/bgmat_job_20261022/slurm-96496.out)、[stderr](../runs/bgmat_job_20261022/slurm-96496.err)、[Slurm记账](../runs/bgmat_job_20261022/accounting.txt)与[完整提交参数](../runs/bgmat_job_20261022/submission-96496.json)。

8个样本的最短粒子间距为2.343–2.418 Å，坐标、能量和log score均为有限值。归一化权重和为1，有效样本数ESS约3.53（44.09%）。这只是8个样本的诊断量，不能证明总体权重分布或热力学估计已收敛。

上游在物理坐标的高斯参考分布中省略了归一化常数，因此这里的模型和目标log score都采用作者的**非归一化、物理加辅助坐标联合空间约定**。归一化重要性权重中常数相消；不要把这些数组当作物理坐标边缘分布的绝对log概率。

原始生成样本平均能量为−11.7722 kcal/mol/粒子；仓库提供的1000个MD参考样本均值为−11.7487。两个数字仅供排错和量级核对，不将小样本均值接近视为分布验证。

## 3. 如何复跑

从Gen_X根目录操作。先准备Python 3.10，再运行：

```bash
bash tools/setup_bgmat.sh
```

若默认Python不是3.10，设置`GENX_PYTHON310`为已有Python 3.10解释器路径。脚本只在项目内准备`external/bgmat`及`.venv-bgmat`，按已保存的依赖锁文件安装，并验证源码和权重哈希。上游原始版本为JAX/JAXlib 0.4.32；本次固定这一作者版本，不声称已验证新版兼容性。

准备一个新的日志目录和结果路径，然后提交CPU推理：

```bash
run_tag="bgmat_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "runs/${run_tag}_logs"
sbatch --parsable --partition=gpu \
  --job-name=genx_bgmat_real --nodes=1 --ntasks=1 \
  --cpus-per-task=2 --mem=8G --time=00:20:00 \
  --no-requeue --open-mode=append --export=NONE \
  --chdir="$PWD" \
  --output="$PWD/runs/${run_tag}_logs/slurm-%j.out" \
  --error="$PWD/runs/${run_tag}_logs/slurm-%j.err" \
  scripts/run_bgmat_cpu.sh --output "runs/$run_tag" --samples 8
```

此命令不包含GPU GRES请求；运行器还显式设置`JAX_PLATFORMS=cpu`。如果集群不允许在GPU分区运行CPU作业，改成允许的CPU分区。必须从仓库根目录提交，输出路径不能已存在。更改种子可使用`--seed`；当前适配器只接受已验证的216粒子配置。

运行结束后同时检查`sacct`的终态和结果manifest。加载权重、开始运行或出现首个样本日志，都不单独代表整个流程完成。

```bash
sacct -j <实际作业号> --format=JobID,State,ExitCode,Elapsed -P
python3 -m json.tool "runs/$run_tag/manifest.json"
```

## 4. 版本与实现边界

源码来自[官方bgmat仓库](https://github.com/maxschebek/bgmat)，固定提交`6e3db2b3453cb57eb16fdd2148c95ec35264faf4`。权重为作者的`params-mw_cubic_216.pkl`，SHA-256见manifest和源码常量。源码文件哈希另存[bgmat_source_lock.json](../configs/bgmat_source_lock.json)，依赖见[锁文件](../configs/bgmat_requirements.lock.txt)。

架构使用作者教程的96维embedding、16个局部邻居、10层耦合流。适配器调用上游`create_base`、`create_flow`和`_get_loss`；通过`hk.transform(...).apply`将真实预训练参数传入完整flow。参考分布是在晶格附近加噪的分布，生成后的坐标来自训练好的变换，不直接把这些初始噪声坐标作为结果。

主要工程适配：Slurm在spool目录执行脚本，项目路径改从`SLURM_SUBMIT_DIR`取得；计算节点不依赖Git，用预先固定的源码哈希校验；上游editable安装未暴露namespace包，显式加入已校验源码路径。这些处理不更改模型权重或物理势。

## 5. 调试记录和后续任务

96462在模型启动前因Slurm脚本路径失败；96471因计算节点无Git失败；96484取消以修正导入路径；96487因CPU分区排队取消，改由96496以CPU-only方式运行。失败和取消记录均保留，只有96496报告实际生成成功。

软件测试现共20项通过，涵盖原smoke接口、生成输出、输入边界、源码校验及Slurm spooled脚本路径。与运行结果相结合，它们证明工程闭环，不替代科研验收。

后续可在这个独立项目中增加样本、多个种子、RDF与高阶结构比较、权重收敛及尺寸迁移；另设非晶或全原子水项目。主动学习仍需要独立参考数据和触发准则，本示例没有自动训练生成器或势。
