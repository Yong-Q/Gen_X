# 从配置到结果：Gen_X 使用教程

本教程面向第一次打开仓库、希望亲自运行并检查产物的读者。当前可执行内容是 **CPU 冒烟流程**：用人工编写的合成坐标检查 Bash 入口、配置验证、Slurm 调度、日志、几何 QA 和候选队列。这里的 `completed` 表示软件流程完成；模型推理、能量与力评估、训练及科学分布验证均未执行。

研究目标是学习条件构型分布 $q_\theta(X\mid c)$，再生成多个结构。当前冒烟流程为后续真实模型接入准备可追溯的运行接口；三条路线的配置目前都是 `model_status: not_integrated`。阅读[文献调研](literature_survey.md)可了解已有方法，阅读[技术路线](technical_roadmap.md)可了解后续科学验收。

## 1. 打开项目，选择路线

下面的命令均从仓库根目录执行。本机路径为：

```bash
cd /home/qiuyong/bza/H2O/Gen_X
/usr/bin/python3 --version
bash scripts/local_smoke.sh --help
bash scripts/submit_smoke.sh --help
```

冒烟流程只使用 Bash 和 Python 标准库，不需要安装生成模型依赖。启动器默认使用 `/usr/bin/python3`；如需选择其他解释器，可设置 `GENX_PYTHON` 为兼容解释器的绝对路径。程序要求 Python 3.6 或更新版本；实际已执行的登录端和计算端分别为 Python 3.12.15、3.12.13，未声称在 3.6 上实测。

| 你的起步方向 | 配置文件 | 当前示例与真实模型边界 |
|---|---|---|
| 非晶生成，优先起点 | [dm2_smoke.json](../configs/dm2_smoke.json) | 使用人工硅坐标；没有调用 DM2，也不是 SiO₂ 推理结果 |
| 单珠水／冰的概率采样 | [bgmat_smoke.json](../configs/bgmat_smoke.json) | 使用人工单珠坐标；没有调用 bgmat，不含显式氢原子 |
| 后续全原子水路线 | [mbpol_water_smoke.json](../configs/mbpol_water_smoke.json) | 使用人工 O/H 坐标；没有调用 DNN@MB-pol；该势是未来参考模型，生成器另行实现 |

先使用 DM2 配置熟悉接口，之后仅替换 `--config` 即可检查另外两条冒烟路线。配置中的 `source_url`、`prerequisites` 和 `upstream_entrypoint` 记录上游来源与接入前置条件；后者目前是说明文字，不是可执行的真实推理命令。

## 2. 先查看将执行的命令

`--dry-run` 检查配置与输出位置，并打印实际参数数组；不创建运行目录，也不提交作业。

```bash
bash scripts/local_smoke.sh --config configs/dm2_smoke.json --dry-run
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --partition debug --dry-run
```

输出是一行 JSON。检查 `status` 为 `dry_run`、`route_id` 为 `dm2_amorphous`，并查看 `command`：Slurm 请求为一节点、一任务、一 CPU、128 MB、两分钟上限，无 GPU 请求，也不指定节点。`run_dir` 只是本次预览的计划路径，下一次真实运行省略 `--run-id` 时会生成另一个新路径。

可选参数的含义如下：

| 参数 | 作用与约束 |
|---|---|
| `--config PATH` | 必填；选择 JSON 配置，路径相对当前工作目录 |
| `--run-id NAME` | 可选；省略时自动生成唯一名称；仅允许字母、数字、下划线、点及连字符，首字符必须为字母或数字 |
| `--output-root PATH` | 可选；默认 `runs/`；必须在本项目内，含空格的路径要用引号包住 |
| `--dry-run` | 仅验证并打印命令，不写运行产物 |
| `--partition NAME` | 仅用于提交入口；默认 `debug`，应以执行时的集群配置为准 |

## 3. 运行一次本地冒烟

以下命令只检查小型合成数据，可在登录环境执行：

```bash
bash scripts/local_smoke.sh --config configs/dm2_smoke.json
```

成功后，终端输出 JSON，包含 `status: completed`、新建的 `run_dir` 和 `summary`。对仓库当前三个合成示例，预期各有 3 条 QA 记录、1 条示意 QA 通过、2 条候选。这些数量来自固定测试数据，不能解释为生成成功率或物理正确率。

需要自选名称时，为每次尝试选择一个未使用的名称。例如，第一次可以运行：

```bash
bash scripts/local_smoke.sh \
  --config configs/bgmat_smoke.json \
  --output-root "runs/tutorial runs" \
  --run-id bgmat_first_check
```

再次使用同一输出位置会被拒绝，即使原目录为空或上次运行失败。保留已有结果与失败证据，重试时更换名称。配置与样例会复制到新运行目录，随后以快照作为实际输入。

## 4. 通过 Slurm 运行并确认结束

下面的提交命令会创建一个真实 CPU 作业。仅当需要检查集群执行时运行：

```bash
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --partition debug
```

提交成功仅表示调度器接收了作业。输出中的 `status` 是 `submitted`，同时给出 `job_id` 和 `run_dir`。把实际作业号填入变量后查看：

```bash
# 此处是已完成记录的作业号；检查新作业时替换它。
job_id=96390
squeue -j "$job_id" -o '%.18i %.9P %.20j %.8T %.10M %.6D %R'
sacct -j "$job_id" --format=JobID,State,ExitCode,AllocCPUS,ReqMem,Elapsed -P
```

作业结束后可能从 `squeue` 消失；应结合 `sacct`、运行目录内的 `manifest.json` 和日志判断。预期为作业／batch 状态 `COMPLETED`、退出码 `0:0`，且 manifest 为 `completed`、`exit_code: 0`。只有提交记录而没有终态 manifest 时，流程尚不能判定完成；调度器取消或超时也可能导致没有终态 manifest。

本项目已保存两次实际 CPU 作业。初版 **96379** 记账用时 5 秒；复核修正后的 **96390** 为 4 秒。二者均使用 `debug` 分区，由调度器分配 `node04`，1 CPU、128 MB，状态 `COMPLETED`、退出码 `0:0`。96390 验证当前脚本的配置快照校验、日志追加与禁止自动重排设置。它们是 2026-10-22 的历史证据，不是实时队列状态。完整命令与证据见[执行记录](smoke_results.md)。

## 5. 读懂运行目录

下面可直接读取已保存的成功运行。检查你自己的结果时，将 `run_dir` 换为终端返回的路径。

```bash
run_dir="runs/slurm_dm2_review_20261022"
/usr/bin/python3 -m json.tool "$run_dir/manifest.json"
cat "$run_dir/qa.jsonl"
cat "$run_dir/candidates.jsonl"
```

| 文件 | 回答的问题 |
|---|---|
| `config.input.json`、`fixture.input.json` | 当时实际使用了哪份配置与合成输入？ |
| `config.resolved.json` | worker 读取的快照配置是什么？ |
| `launch.json`、`command.json` | 哪条路线、何时启动、输入与脚本哈希、解释器和实际 argv 是什么？ |
| `launcher.stdout.log`、`launcher.stderr.log` | 启动器捕获了哪些输出与错误？ |
| `worker.started.json` | worker 是否开始执行？该文件也用于拒绝重复执行 |
| `manifest.json` | 最终状态、退出码、运行主机、Python 版本、摘要及产物哈希是什么？ |
| `qa.jsonl` | 每个合成样例的几何标记、来源、示意优先级是什么？ |
| `candidates.jsonl` | 哪些样例被标记为需要人工复查？ |
| `submission.json`、`slurm-作业号.out/.err` | Slurm 作业号与调度日志是什么？仅集群运行产生 |

已完成运行中的关键边界字段应保持：

```json
{
  "status": "completed",
  "exit_code": 0,
  "synthetic": true,
  "model_inference": "not_run",
  "scientific_validation": "not_run"
}
```

上面是字段摘录，不是完整 manifest。可直接打开[真实 manifest](../runs/slurm_dm2_review_20261022/manifest.json)、[调度记账](../runs/slurm_dm2_review_20261022/sacct.txt)和[候选队列](../runs/slurm_dm2_review_20261022/candidates.jsonl)核对。当前实现还核对 `resolved_config_sha256`，确认执行配置未在提交后被改动。日志、哈希和输入快照用于解释结果，不应当作缓存清理。

## 6. 从 QA 候选走向两条反馈回环

**当前已实现：合成输入 → 几何 QA → 人工复查队列。** QA 用正交盒的周期最小镜像计算粒子对最短距离，并标记坐标是否位于主盒外。统一的 0.7 Å 阈值只是测试参数，不是经过验证的元素或分子验收条件。`illustrative_priority` 等于 QA 标记数量；`next_action` 为 `manual_review_only`。队列不会触发 DFT、模拟、标注或重训。

实际复查时，先按 `sample_id` 回到 `fixture.input.json` 查看坐标与来源，再判断是明显几何异常还是表示约定问题。周期等价的盒外坐标不必然不合理，当前标记只是演示如何暴露需要检查的输入。

**后续计划：生成器反馈。** 接入真实模型后，检查状态覆盖、网络拓扑及高阶分布缺口；补充独立可信参考样本，再更新生成器。持续重复训练自身生成数据不构成新的参考证据。

**后续计划：势模型反馈。** 第一阶段冻结已有参考势。仅当独立参考能量／力或适用域检查显示势有缺口时，才选择代表构型进行独立量化标注，再考虑更新势。高能生成结构本身不能证明势不准确。两条反馈回环分别验收，详见[技术路线中的反馈设计](technical_roadmap.md)。

## 7. 常见问题与下一步

| 现象 | 下一步检查 |
|---|---|
| `run directory already exists` | 保留原目录；省略 `--run-id` 自动命名，或选择新名称 |
| `unknown route`、缺少字段、fixture 不存在 | 对照三个现有配置核对字段；fixture 路径相对配置文件目录解析 |
| `only mode=synthetic_smoke is implemented` | 真实推理／训练尚未接入；修改 mode 不会启用外部模型 |
| `sbatch` 失败或 `submission_failed` | 查看启动器 stderr 和 manifest，核对分区与调度环境；修复后使用新 run ID |
| 已提交但没有 `manifest.json` | 先查作业排队／运行／失败状态及 Slurm 日志，不将 `submitted` 当作完成 |
| `worker script changed after submission` | 保留失败记录；在代码稳定后重新提交新运行，不重放旧 worker |
| 生成了候选文件 | 只代表文件流程通过；继续检查来源和 QA 标记，不能视为不确定度或科学验证 |

修改入口后可运行现有行为测试，不会提交调度作业：

```bash
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -v
bash -n scripts/local_smoke.sh scripts/submit_smoke.sh scripts/slurm_smoke.sh
```

下一阶段按[技术路线](technical_roadmap.md)的 S1 开始：锁定 DM2 上游提交、权重哈希、依赖和许可，建立单位／元素／盒子约定，再实际加载权重并保存生成结果。这些步骤**尚未完成**。随后才进入多种子系综、留出条件与尺度迁移验证；当前不要把合成样例用于论文结构统计。

## 8. 更新 HTML 与 PDF 文档

在 Markdown 源文件中修改内容后，重新生成离线站点：

```bash
/usr/bin/python3 tools/build_html.py
```

构建需要本机可用的 Pandoc，Python 构建器仅使用标准库。入口是 [site/index.html](../site/index.html)，可直接在浏览器打开；页面样式、导航搜索、复制按钮和 MathML 公式均使用本地资源，不依赖 CDN。外部论文与 GitHub 链接需要联网，源文档、运行记录和已有 PDF 可从完整仓库离线访问。分享时应保留仓库目录关系，只复制 `site/` 会缺少这些原始文件。

站点每次构建会更新派生 HTML，并校验本地链接和页内锚点；不会修改 Markdown、运行证据或 PDF。`site/build-validation.json` 记录构建检查结果。构建器还会发现 `reports/` 中同时包含两份报告的最新 PDF 快照，并在页面底部生成下载链接。

如需新 PDF 快照，使用一个未用过的输出目录名：

```bash
bash tools/build_pdfs.sh reports/tutorial_snapshot_01
```

PDF 脚本拒绝覆盖已有 PDF。生成新快照后再次运行 HTML 构建命令即可更新下载索引。
