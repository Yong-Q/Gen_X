# 数学基础附录：从高保真信息到非晶结构系综

本文为研究方案的理论依据，而非已完成结果。拟研究的问题是：能否利用少量高保真能量、力、应力及结构信息，校正由大量经典势数据预训练的生成模型，使其产生具有合理结构概率和力学性质分布的非晶系综？非晶 SiO$_2$ 是候选体系，材料选择仍需论证。现有 bgmat 的 $8\times216$ 个 mW 冰粒子工程运行仅提供流程背景，不能证明对非晶 SiO$_2$ 的迁移有效性，也不能作为新的材料科学结果。

## 1. 先定义目标：玻璃的分布包含制备历史

固定原子数 $N$、元素标签 $a=(a_1,\ldots,a_N)$ 及晶胞矩阵 $h$，体积为 $V=\det h>0$。用 $R=(r_1,\ldots,r_N)$ 表示位置，$P$ 表示动量，$U^{\mathrm C}$ 与 $U^{\mathrm H}$ 分别表示经典与高保真势能。这里的“高保真”是相对于所选参考电子结构方法而言，不等同于无误差的真实势能。为集中说明概率结构，先在选定坐标及参考体积测度 $dx$ 下讨论连续密度；周期边界、平移约束与原子置换在第 6 节处理。

玻璃通常由有限速率冷却、退火及等待得到，因此目标不宜直接写成某个温度的正则分布。设完整状态为 $y_k=(R_k,P_k,h_k,\zeta_k)$，其中 $\zeta_k$ 包含所需的恒温器、恒压器或其他记忆变量。给定协议 $\mathcal P=\{T_k,p_k,\Delta t_k,\ldots\}_{k=0}^{L-1}$，在状态变量足够完整时，离散动力学可以表示为时变 Markov 核 $K_k^U(dy_{k+1}\mid y_k;\mathcal P)$。确定性积分器也可用 Dirac 转移核表示。其路径概率测度为

$$
\mathbb P_{U,\mathcal P}(dy_{0:L})
=\mu_0^U(dy_0)\prod_{k=0}^{L-1}K_k^U(dy_{k+1}\mid y_k;\mathcal P).
$$

将最终状态投影到结构 $x=\Pi(y_L)$，例如保留瞬时坐标，或先按指定规则淬火到固有结构，再保留坐标与晶胞，得到

$$
p_{U,\mathcal P}(dx)
=\int\mathbb P_{U,\mathcal P}(dy_{0:L})\,
\delta_{\Pi(y_L)}(dx).
$$

这一定义说明，冷却率、初态、等待时间和最小化规则均属于目标的一部分。只保留位置一般不能保持 Markov 性，因为相同位置配以不同动量会产生不同的下一步位置；消去恒温器等变量也可能引入记忆。只有在明确的过阻尼模型等特殊条件下，位置本身才可构成闭合 Markov 过程。非晶 SiO$_2$ 性质随冷却率改变的原始模拟工作，为必须记录协议提供了具体材料背景。[Vollmayr、Kob 与 Binder（1996）](https://doi.org/10.1103/PhysRevB.54.15808)

与此不同，固定 $N,V,T$ 的平衡构型正则密度定义为

$$
\pi_U(x)=Z_U^{-1}e^{-\beta U(x)},\qquad
Z_U=\int e^{-\beta U(x)}dx,\quad \beta=(k_{\mathrm B}T)^{-1}.
$$

该式来自对平衡相空间正则分布积分掉动量，要求使用一致的坐标测度。它不含冷却率，因而不能自动等同于 $p_{U,\mathcal P}$。若目标是某个玻璃盆地内的受限热平衡，还须明确盆地集合及边界；若目标是淬火后的局部极小点集合，概率可能不再具有相对于普通体积测度的光滑密度。后文涉及密度和 KL 的公式均以相应绝对连续性为前提，不能直接用于离散极小点分布而不改变测度。

## 2. 势能模型与生成模型回答不同问题

机器学习势（machine-learned potential，MLP）学习标量函数 $U_\psi(R,h,a)$。以拉伸为正的能量共轭应力约定为例，定义

$$
F_{\psi,i}=-\nabla_{r_i}U_\psi,\qquad
\sigma_\psi=\frac1V
\left.\frac{\partial U_\psi((I+\varepsilon)R,(I+\varepsilon)h,a)}
{\partial\varepsilon}\right|_{\varepsilon=0}.
$$

参考软件若采用相反的压应力或维里符号，训练前必须统一。一个示意监督目标是

$$
\mathcal L_{\mathrm{MLP}}(\psi)
=\mathbb E_{\mathcal D_{\mathrm H}}
\left[
w_E\left(\frac{U_\psi-E^{\mathrm H}}{N}\right)^2
+\frac{w_F}{3N}\sum_i\|F_{\psi,i}-F_i^{\mathrm H}\|^2
+\frac{w_\sigma}{9}\|\sigma_\psi-\sigma^{\mathrm H}\|_F^2
\right].
$$

各权重需吸收单位与尺度差别，不能在未说明归一化时比较其数值。能量、力和应力分别约束势能面数值、坐标导数及应变导数，后两者不直接提供结构的出现频率。以能量及导数训练原子势的代表性原始工作可见 [Zhang 等（2018）](https://arxiv.org/abs/1707.09571)。

生成模型则学习条件结构分布 $q_\theta(x\mid c)$，其中 $c$ 可包含组成、尺寸、密度和制备协议。若有来自目标协议的独立参考结构，其最大似然目标为 $-\mathbb E_{p_{\mathrm H,\mathcal P}}\log q_\theta$，等于 $D_{\mathrm{KL}}(p_{\mathrm H,\mathcal P}\|q_\theta)$ 加上与 $\theta$ 无关的项。MLP 回答“这个结构的能量及响应是什么”，生成模型回答“应该以多大概率产生这个结构”。给出某些经典结构的高保真单点标签，不会将这些结构自动变为高保真动力学生成的样本。由小规模标签推断结构概率，必须增加统计力学假设、动力学信息或独立参考系综检验。

## 3. 归一化流：从体积变化到自由能

令潜变量 $z\sim\rho(z)$，以可逆可微映射 $x=f_\theta(z)$ 生成结构。对微小体积元，概率守恒要求 $q_\theta(x)dx=\rho(z)dz$，而 $dx=|\det J_{f_\theta}(z)|dz$。因此

$$
\log q_\theta(f_\theta(z))
=\log\rho(z)-\log|\det J_{f_\theta}(z)|.
$$

该式的作用不是只给出采样器，而是同时给出可计算的归一化密度。当目标确为平衡 $\pi_U$ 时，将其代入反向 KL 得到

$$
\begin{aligned}
D_{\mathrm{KL}}(q_\theta\|\pi_U)
&=\int q_\theta\log q_\theta\,dx
 +\beta\mathbb E_{q_\theta}U+\log Z_U\\
&=\beta\big[\mathbb E_{q_\theta}U-TS[q_\theta]-F_U\big],\\
S[q]&=-k_{\mathrm B}\int q\log q\,dx,\qquad
F_U=-k_{\mathrm B}T\log Z_U.
\end{aligned}
$$

所以最小化该 KL 等价于最小化变分自由能，而非仅最小化平均能量。用流的表达式展开后，训练中出现 $\beta U(f_\theta(z))-\log|\det J_f(z)|$，其中第二项防止通过任意压缩概率体积来降低能量。绝对微分熵依赖坐标单位，以上比较必须使用同一参考测度；KL 本身在一致变换下不变。Boltzmann generator 正是利用可逆映射与统计力学目标结合的原始范例。[Noé 等（2019）](https://doi.org/10.1126/science.aaw1147)

熵项为何不可省略，可用两个能量盆地说明：若盆地 $A,B$ 内能量近似为 $E_A,E_B$、有效体积为 $\Omega_A,\Omega_B$，正则权重比近似为 $\Omega_Ae^{-\beta E_A}/(\Omega_Be^{-\beta E_B})$。较低的最低能量不能决定盆地总概率。对玻璃还须叠加路径可达性，故将平衡自由能目标原样用于玻璃，会更换研究对象，而非仅改变训练技巧。

### 3.1 重要性权重能够校正什么

若已知目标的未归一化密度 $\widetilde p(x)$，且 $q(x)>0$ 覆盖目标支持集，可写

$$
\mathbb E_p A
=\frac{\mathbb E_q[w(x)A(x)]}{\mathbb E_q w(x)},\qquad
w(x)=\frac{\widetilde p(x)}{q(x)}.
$$

对 $M$ 个独立提议样本，估计量为 $\widehat A=\sum_j\bar w_jA(x_j)$，其中 $\bar w_j=w_j/\sum_\ell w_\ell$。这是随机分子与随机分母之比，有限样本通常有偏；在适当可积性与支持覆盖条件下才可讨论大样本一致性。常用诊断量

$$
\widehat{\mathrm{ESS}}=
\frac{(\sum_jw_j)^2}{\sum_jw_j^2}
=\frac1{\sum_j\bar w_j^2}
$$

度量的是已观察样本的权重集中程度。它不是所有观测量共同的误差保证，也不能发现完全漏采的盆地；相关样本还需另行处理自相关。因此即使 ESS 较高，也应检查独立重复、关键结构子群覆盖及具体性质的误差。

两个同温、同体积且测度一致的平衡体系满足 $U^{\mathrm H}=U^{\mathrm C}+\Delta U$。直接相除正则密度并约去归一化常数，有

$$
\langle A\rangle_{\pi_{\mathrm H}}
=\frac{\langle Ae^{-\beta\Delta U}\rangle_{\pi_{\mathrm C}}}
{\langle e^{-\beta\Delta U}\rangle_{\pi_{\mathrm C}}},\qquad
F_{\mathrm H}-F_{\mathrm C}
=-\beta^{-1}\log\langle e^{-\beta\Delta U}\rangle_{\pi_{\mathrm C}}.
$$

这是平衡扰动恒等式的直接推导；其经典来源为 [Zwanzig（1954）](https://doi.org/10.1063/1.1740409)。恒等式并不保证有限数据能估计指数平均，尤其在两分布重叠不足时。

对玻璃，若路径测度绝对连续，形式上的路径权重应为初态概率比乘以每一步转移核的比，即 $d\mathbb P_{\mathrm H,\mathcal P}/d\mathbb P_{\mathrm C,\mathcal P}$。最终坐标的密度比等于该路径权重在给定最终坐标条件下的条件期望，一般不等于 $e^{-\beta\Delta U(x)}$。确定性动力学下，两种势的路径测度甚至可能相互奇异。因此，经典玻璃的高保真能量差可以作为校正信息，却不能在缺少额外论证时被称为玻璃系综的精确重加权公式。

### 3.2 小数据校正需要额外的可识别性假设

先看最有利的平衡情形。设中间势 $U_\lambda=U^{\mathrm C}+\lambda\Delta U$，在固定温度、体积与测度下对归一化正则平均求导。分子的导数为 $-\beta\int A\Delta Ue^{-\beta U_\lambda}dx$，分母的导数为 $-\beta Z_\lambda\langle\Delta U\rangle_\lambda$。使用商法则，若 $A$ 不显含 $\lambda$，得到

$$
\frac{d\langle A\rangle_\lambda}{d\lambda}
=-\beta\operatorname{Cov}_{\pi_\lambda}(A,\Delta U).
$$

由此可见，能量差的平均值本身不决定性质校正，关键是它与目标性质的相关性。对势能加上常数会改变绝对能量差，却不改变结构概率；相反，只在某个稀有但重要的结构子群上出现的势能误差，可能改变其相对权重。该推导仍只适用于所定义的平衡族；若 $A$ 本身由相应势的松弛过程定义，还需加入 $\langle\partial_\lambda A\rangle_\lambda$，不能忽略观测量定义的改变。

一个可逆校正的概念模型是先从经典预训练分布 $q_{\mathrm C}$ 采样，再经可逆映射 $g_\phi$ 得到新结构。变量替换给出

$$
q_\phi^{\mathrm{corr}}(g_\phi(x))
=q_{\mathrm C}(x)|\det J_{g_\phi}(x)|^{-1}.
$$

这一表达式明确区分了结构移动和概率体积变化，但没有指定怎样从有限标签确定 $g_\phi$。仅要求训练结构能量降低，许多不同映射都可满足；它们可能对训练外盆地给出不同权重。这就是可识别性问题。要缩小候选模型集合，需要引入有效的平衡目标、协议匹配的参考结构、可验证的动力学约束，或清楚标注为先验的结构对称性与正则化。正则化有助于限制过拟合，却不能充当高保真目标分布的实验证据。

因此，“少量数据”必须按信息类型及覆盖范围表述：多少独立制备轨迹、多少结构、多少能量与导数标签，以及是否覆盖不同密度、局部拓扑和受应变环境。大量力分量来自同一结构，不应被当成同样数量的独立结构样本。模型从 $N$ 个原子迁移到更大晶胞时，局部相互作用的可迁移性也不自动保证长程拓扑和整体弹性涨落正确；尺寸推广需要独立验证，而不能从网络可接受变长输入推导出来。

## 4. 扩散模型：从高斯链推导噪声回归

本节暂用欧氏坐标 $x_0\in\mathbb R^d$，下标 $0$ 表示干净数据。设前向链

$$
q(x_t\mid x_{t-1})=\mathcal N(\sqrt{\alpha_t}x_{t-1},\beta_tI),
\quad \alpha_t=1-\beta_t,\quad
\bar\alpha_t=\prod_{s=1}^t\alpha_s.
$$

递推展开时，各步独立高斯噪声的线性组合仍为高斯；其均值系数为 $\sqrt{\bar\alpha_t}$，方差满足 $v_t=\alpha_tv_{t-1}+\beta_t$、$v_0=0$，解为 $v_t=1-\bar\alpha_t$。因此不必真的执行前 $t$ 步即可采样：

$$
x_t=\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon,
\qquad\epsilon\sim\mathcal N(0,I).
$$

由 Bayes 公式，$q(x_{t-1}\mid x_t,x_0)$ 正比于两个高斯因子的乘积。将关于 $x_{t-1}$ 的二次项配方，得到 $t\ge2$ 时

$$
\begin{aligned}
q(x_{t-1}\mid x_t,x_0)&=\mathcal N(\widetilde\mu_t,\widetilde\beta_tI),\\
\widetilde\beta_t&=\frac{1-\bar\alpha_{t-1}}{1-\bar\alpha_t}\beta_t,\\
\widetilde\mu_t&=
\frac{\sqrt{\bar\alpha_{t-1}}\beta_t}{1-\bar\alpha_t}x_0
+\frac{\sqrt{\alpha_t}(1-\bar\alpha_{t-1})}{1-\bar\alpha_t}x_t\\
&=\frac1{\sqrt{\alpha_t}}
\left(x_t-\frac{\beta_t}{\sqrt{1-\bar\alpha_t}}\epsilon\right).
\end{aligned}
$$

反向生成链定义为 $p_\theta(x_{0:T})=p_T(x_T)\prod_{t=1}^{T}p_\theta(x_{t-1}\mid x_t)$。在边缘似然中插入前向条件分布并用 Jensen 不等式，可得负证据下界（negative ELBO）$\mathcal L_{\mathrm{VLB}}\ge-\mathbb E\log p_\theta(x_0)$。利用前向链的条件概率分解，展开为

$$
\begin{aligned}
\mathcal L_{\mathrm{VLB}}
=\mathbb E_{x_0}\bigg[&
D_{\mathrm{KL}}(q(x_T\mid x_0)\|p_T)
-\mathbb E_{q(x_1\mid x_0)}\log p_\theta(x_0\mid x_1)\\
&+\sum_{t=2}^{T}\mathbb E_{q(x_t\mid x_0)}
D_{\mathrm{KL}}\big(q(x_{t-1}\mid x_t,x_0)
\|p_\theta(x_{t-1}\mid x_t)\big)\bigg].
\end{aligned}
$$

假定反向方差固定为 $\sigma_t^2I$，并令反向均值采用上式 $\widetilde\mu_t$ 的形式、将 $\epsilon$ 替换为网络 $\epsilon_\theta(x_t,t)$。两个高斯之间 KL 的均值项为 $\|\widetilde\mu_t-\mu_\theta\|^2/(2\sigma_t^2)$。代入即得每个内部时间步的可训练项

$$
\lambda_t\,\mathbb E\|\epsilon-\epsilon_\theta(x_t,t)\|^2,
\qquad
\lambda_t=\frac{\beta_t^2}
{2\sigma_t^2\alpha_t(1-\bar\alpha_t)}.
$$

这解释了噪声均方误差的来源，也说明均匀抽取 $t$ 并直接使用无权重 MSE，会改变 ELBO 各时间步的相对权重；它是简化训练目标，不能不加限定地称为“精确最大似然”。端点重构项也需单独处理，不能把 $\widetilde\beta_1=0$ 当成普通非退化高斯 KL。上述方法源于 [Ho、Jain 与 Abbeel（2020）](https://arxiv.org/abs/2006.11239)。

噪声预测与得分函数的联系也可直接推导。对 $q_t(x_t)=\int q(x_t\mid x_0)p_{\mathrm{data}}(x_0)dx_0$ 求梯度，在允许交换微分与积分时，有

$$
\begin{aligned}
\nabla_{x_t}\log q_t(x_t)
&=\mathbb E[\nabla_{x_t}\log q(x_t\mid x_0)\mid x_t]\\
&=-\frac{\mathbb E[\epsilon\mid x_t]}{\sqrt{1-\bar\alpha_t}}.
\end{aligned}
$$

而平方损失的总体最优预测正是条件均值 $\epsilon_\theta^*(x_t,t)=\mathbb E[\epsilon\mid x_t]$。因此网络学习的是加噪结构分布的得分，而非原子物理力；物理力与得分仅在特定平衡密度下才有 $\nabla\log\pi=-\beta\nabla U$ 的直接关系。有限网络、有限样本和近似采样器均会产生偏差。得分与反向随机微分方程的原始统一框架见 [Song 等（2021）](https://arxiv.org/abs/2011.13456)。

## 5. 流匹配：条件均值为何能够输运概率

另取噪声 $z\sim\rho$ 与数据 $x\sim p_{\mathrm{data}}$ 的联合耦合 $\gamma(z,x)$。最简单的选择是独立耦合，但这不是唯一选择。定义欧氏直线插值 $x_t=(1-t)z+tx$，其逐对速度为 $u=x-z$，训练目标为

$$
\mathcal L_{\mathrm{FM}}(\theta)
=\mathbb E_{t,(z,x)\sim\gamma}
\|v_\theta(x_t,t)-(x-z)\|^2.
$$

给定 $x_t=y,t$ 后，将任意预测与条件均值相减并展开平方，交叉项因条件残差均值为零而消失。因此

$$
\mathbb E[\|v-u\|^2\mid y,t]
=\|v-\mathbb E[u\mid y,t]\|^2
+\mathbb E[\|u-\mathbb E[u\mid y,t]\|^2\mid y,t],
$$

总体最优速度就是 $v^*(y,t)=\mathbb E[x-z\mid x_t=y]$。单条配对直线即使相互交叉，条件均值也给出该位置的平均概率流；网络无需知道某个中间点具体属于哪一条配对路径。

为了说明它与目标分布的关系，令 $p_t$ 为插值变量的边缘分布，取任意光滑紧支撑测试函数 $\varphi$。由链式法则与条件期望，

$$
\frac d{dt}\mathbb E\varphi(x_t)
=\mathbb E[\nabla\varphi(x_t)\cdot(x-z)]
=\int\nabla\varphi(y)\cdot v^*(y,t)p_t(y)dy.
$$

分部积分后得到弱形式的连续性方程

$$
\partial_tp_t+\nabla\cdot(p_tv^*)=0.
$$

因此，在速度场足够正则、ODE 解及输运方程具有所需唯一性时，$\dot y_t=v^*(y_t,t)$ 从 $p_0=\rho$ 出发具有指定的边缘概率路径。该论证的条件不能省略：有限数据可对应离散终点分布，精确端点可能产生奇异行为；实践中可通过端点平滑并明确所学目标来处理，不能宣称光滑可逆 ODE 无条件地把连续分布变成有限个点质量。

若该 ODE 构成可逆流，沿轨迹有 $d\log p_t(y_t)/dt=-\nabla\cdot v(y_t,t)$，这就是连续归一化流（continuous normalizing flow，CNF）的密度演化公式。因此，流匹配是训练速度场的一种方法，CNF 是由连续可逆流定义的模型形式，两者并非互斥类别。相关原始文献为 [Lipman 等（2023）](https://arxiv.org/abs/2210.02747) 及 [Chen 等（2018）](https://arxiv.org/abs/1806.07366)。其数学时间 $t$ 表示概率输运进度，不能解释为玻璃的真实冷却时间。

## 6. 周期结构要求改变空间与核

分数坐标 $s_i=h^{-1}r_i\bmod1$ 位于三维环面，全部位置属于 $\mathbb T^{3N}$。同一点可以写成 $s$ 或 $s+n$，$n\in\mathbb Z^{3N}$。普通欧氏距离会把 $0.99$ 与 $0.01$ 误判为相距很远；更严重的是，欧氏 DDPM 的收缩项 $\sqrt\alpha\,s$ 在更换代表元 $s+n$ 后通常不能给出同一个环面点，故不能简单“加噪后取模”就沿用整套高斯后验推导。

一种合法的环面加噪方式是加性布朗运动取模。在分数坐标上采用各向同性协方差 $\tau I$ 时，转移密度为包裹高斯核

$$
k_\tau(s\mid s_0)
=\sum_{n\in\mathbb Z^{d}}
\frac{\exp[-\|s-s_0+n\|^2/(2\tau)]}{(2\pi\tau)^{d/2}},
\quad d=3N.
$$

求和把所有整数像的概率集中到基本胞元，保证周期性和归一化。其得分需要对整个像求和的对数求梯度，而非只对未经包裹的坐标差求梯度。小噪声且远离坐标切口时，单像近似或有用；大噪声时不可依赖该近似。固定晶胞下，若希望噪声在笛卡尔空间各向同性，则分数坐标噪声协方差应与 $h^{-1}h^{-T}$ 成比例，而非必然为 $I$。环面上长时间扩散趋于均匀分布，也不应继续把标准欧氏高斯当作完全相同的先验。流形扩散的原始处理可见 [Huang 等（2022）](https://arxiv.org/abs/2208.07949)。

流匹配的线性插值同样需要选定周期路径，例如使用合适的环面测地路径及其切向速度，并处理最短路径非唯一的切割集合。只在训练后把坐标截断到 $[0,1)$，不能修复训练路径的几何错误。组成固定时，还应尊重同种原子置换对称性；平移中心约束会降低有效维数，密度、雅可比和噪声都必须定义在同一约束空间。晶胞可变时，$h$ 的正体积约束、分数坐标到笛卡尔坐标的体积因子及胞元等价表示也需明确。能量模型的旋转不变性与坐标生成模型的等变性是不同要求，均需在具体参数化中验证。

## 7. 物理引导会改变权重，不能替代分布校准

设已有生成密度为 $q_0$。若显式设计能量倾斜分布 $q_\lambda(x)\propto q_0(x)e^{-\lambda\beta U^{\mathrm H}(x)}$，其得分为

$$
\nabla\log q_\lambda
=\nabla\log q_0-\lambda\beta\nabla U^{\mathrm H}.
$$

该恒等式说明能量梯度具有怎样的偏置方向，并不说明任意去噪步加入该梯度就能精确采样上述终点分布。对于加噪时刻，正确修正一般涉及条件期望的梯度，而非把干净结构能量直接套到含噪坐标；若引导只在低噪声时或少数步使用，更应将其称为受限启发式，并用独立数据评价其偏差。能量下降、消除重叠和短程松弛可以提高结构可用性，但同时会改变盆地权重。松弛映射 $M$ 输出的是推前分布 $M_\#q$，通常不能继续使用原始 $q$ 的密度计算权重。

由此，研究中的比较应区分仅经典预训练、仅结构微调、增加高保真物理约束及后续松弛各自的作用。关键证据不是生成平均能量降低，而是独立参考协议下的结构统计、盆地或拓扑子群比例以及力学响应分布是否共同接近目标。若真实目标权重未知，应报告可检验的分布特征及偏差，不应使用“无偏高保真玻璃采样”的结论。

## 8. 结构误差如何进入体积模量

考虑零温、同一稳定盆地内的准静态体积变化。定义 $\eta=(V-V_0)/V_0$，以 $u$ 表示相对于仿射缩放后的内部非仿射位移，并写能量为 $U(u,\eta)$。这里偏导数对 $\eta$ 的定义已包含选定的仿射胞元变形。内部松弛满足 $\nabla_uU(u^*(\eta),\eta)=0$。记

$$
\mathcal H=\partial_u^2U,\qquad
\Xi=\partial_u\partial_\eta U.
$$

对平衡条件求导，有 $\mathcal H\,du^*/d\eta+\Xi=0$。周期体系的整体平移产生零模，因此先在去除整体平移的空间中定义响应；若其中所有内部模均稳定，$\mathcal H$ 在该空间正定。记原空间的相应伪逆为 $\mathcal H^+$，则 $du^*/d\eta=-\mathcal H^+\Xi$。沿松弛分支 $\overline U(\eta)=U(u^*(\eta),\eta)$，一次导数因内部力为零而化为 $U_\eta$，再次求导得到

$$
\overline U''(0)=U_{\eta\eta}-\Xi^T\mathcal H^+\Xi,
\qquad
K_0=V_0\left.\frac{d^2\overline U}{dV^2}\right|_{V_0}
=\frac1{V_0}\left(U_{\eta\eta}-\Xi^T\mathcal H^+\Xi\right).
$$

第一项是固定内部坐标时的仿射曲率，第二项是允许原子重新排列带来的软化。在上述稳定性条件下，第二项非负。若除平移外仍有零模，需要额外可解性条件；若接近失稳、跨盆地或发生塑性事件，光滑分支推导不再适用。非仿射弹性及准静态稳定分支的原始讨论见 [Maloney 与 Lemaître（2006）](https://doi.org/10.1103/PhysRevE.74.016118)。此处是将同类隐函数求导用于所定义的体积应变，非引用该文提供 SiO$_2$ 的具体模量。

该结果给出物理上的研究动机：生成结构不仅决定势能值，还决定 Hessian 软模以及应变与软模的耦合。两批结构即使平均能量相近，也可能有不同的体积模量分布。若 $K(x)$ 由统一的高保真评估流程定义，目标性质分布为 $p_K(k)=\int\delta(k-K(x))p_{\mathrm H,\mathcal P}(dx)$；仅拟合少数标量均值不能确定它。

在稳定子空间按特征模展开，还可写成 $\Xi^T\mathcal H^+\Xi=\sum_\nu|e_\nu^T\Xi|^2/\lambda_\nu$，其中 $\lambda_\nu>0$。这表明软模误差可放大非仿射响应，故较小的平均力误差并不单独保证模量精度。实际比较还须固定体积扰动幅度、内部松弛阈值及是否允许胞形改变；若把其他胞元自由度一起松弛，应在扩展的内部变量空间重新推导相应曲率。

有限温度等温模量应从 Helmholtz 自由能而非单个最小点能量定义：$K_T=V(\partial^2F/\partial V^2)_{N,T}$。自由能包含振动熵与热涨落；对玻璃还须指定受限盆地或有限时间响应的含义。因此，零温松弛模量、有限温等温模量和实验有限频率模量必须分别报告，不能共用同一个数值标签。

## 9. 本方案需要验证的科学命题

以上推导建立的是问题定义及方法之间的联系，并未证明少量高保真标签足以完成分布迁移。最关键的待检验命题是：在固定材料、尺寸和制备协议下，经典预训练是否提供可迁移的结构支持；高保真校正能否改善独立测试系综的结构概率及体积模量分布；这种改善是否超出简单松弛与同预算经典采样的效果。训练规模、候选材料和评价精度应由这些检验决定。理论上必须始终保留三条边界：能量准确不等于结构权重准确，平衡恒等式不等于玻璃路径校正公式，大量生成样本不等于大量独立高保真证据。

## 参考文献

1. Vollmayr, K., Kob, W. & Binder, K. Cooling-rate effects in amorphous silica: A computer-simulation study. *Physical Review B* **54**, 15808–15827 (1996). [DOI: 10.1103/PhysRevB.54.15808](https://doi.org/10.1103/PhysRevB.54.15808).
2. Zhang, L., Han, J., Wang, H., Car, R. & E, W. Deep Potential Molecular Dynamics: A Scalable Model with the Accuracy of Quantum Mechanics. *Physical Review Letters* **120**, 143001 (2018). [原始论文预印本](https://arxiv.org/abs/1707.09571).
3. Noé, F., Olsson, S., Köhler, J. & Wu, H. Boltzmann generators: Sampling equilibrium states of many-body systems with deep learning. *Science* **365**, eaaw1147 (2019). [DOI: 10.1126/science.aaw1147](https://doi.org/10.1126/science.aaw1147).
4. Zwanzig, R. W. High-Temperature Equation of State by a Perturbation Method. I. Nonpolar Gases. *The Journal of Chemical Physics* **22**, 1420–1426 (1954). [DOI: 10.1063/1.1740409](https://doi.org/10.1063/1.1740409).
5. Ho, J., Jain, A. & Abbeel, P. Denoising Diffusion Probabilistic Models. *Advances in Neural Information Processing Systems* **33**, 6840–6851 (2020). [原始论文](https://arxiv.org/abs/2006.11239).
6. Song, Y. et al. Score-Based Generative Modeling through Stochastic Differential Equations. *ICLR* (2021). [原始论文](https://arxiv.org/abs/2011.13456).
7. Lipman, Y., Chen, R. T. Q., Ben-Hamu, H., Nickel, M. & Le, M. Flow Matching for Generative Modeling. *ICLR* (2023). [原始论文](https://arxiv.org/abs/2210.02747).
8. Chen, R. T. Q., Rubanova, Y., Bettencourt, J. & Duvenaud, D. Neural Ordinary Differential Equations. *Advances in Neural Information Processing Systems* **31** (2018). [原始论文](https://arxiv.org/abs/1806.07366).
9. Huang, C.-W., Aghajohari, M., Bose, A. J., Panangaden, P. & Courville, A. Riemannian Diffusion Models. *NeurIPS* (2022). [原始论文](https://arxiv.org/abs/2208.07949).
10. Maloney, C. E. & Lemaître, A. Amorphous systems in athermal, quasistatic shear. *Physical Review E* **74**, 016118 (2006). [DOI: 10.1103/PhysRevE.74.016118](https://doi.org/10.1103/PhysRevE.74.016118).
