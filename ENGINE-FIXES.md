# SFS-AI 引擎修复记录（v1.0.3 → 本机修复版）

源码来源：树莓派 DSH 工作区 `~/dsh-work/sfs-ai`（与 GitHub `cswfwm/sfs-ai` 一致）。
改动文件：`core/src/main/java/com/sfsai/core/` 下 Bodies / Guidance / Hub / SimVehicle / Autopilot / Script。

## 一、修掉的硬伤

### 1. 到达段是伪造的（Hub）
旧逻辑：到达段 `alt0 = 0` 从天体表面起步，制导启动后 2 秒内还在地面就判「该段视为完成」。
实测证据：earth→mars 时，到达段把同一枚已逃逸的火箭搬到火星地面，land 制导反而把它加速到 626 km。

现逻辑：
- 到达段按转移轨道近地点进场，高度取大气层顶（`radius + max(1500, atmoHeight*1.1)`）；
- 进场速度由霍曼到达 Δv 换算成双曲余速 `v∞`，再算近地点速度 `√(v∞² + 2μ/r)`；
- 携带出发段末态（剩余级与燃料），不再满油整箭重来；
- 通过判据改为「脚本正常跑完且未坠毁」，删除所有「视为完成」分支。

### 2. circularize 用有符号切向速度（Guidance）
`dv = vc - t.hs` 改成 `vc - abs(t.hs)`。`hs` 是切向分量，逆向/西向运动会变成负数，
旧写法会朝错误方向加速。

### 3. 制导油门量纲错（Guidance）
遥测 `twr` 已经是「推力 / 当地重力」，旧代码又乘了一次 `g`：
`aDes / max(0.05, t.twr * g)`。地球低轨可用加速度被高估约 6 倍，悬停/着陆/定量点火的油门严重偏小。
改为 `accel(t) = twr × 当地重力`。影响 hover / land / burn_dv / raise_apo / circularize 的 Δv 扣减。

### 4. 到达段质量算错（SimVehicle）
`setStateFrom` 只改了当前级燃料，已抛掉的上面级仍被 `mass()` 计入
（火星到达段实测 33968 kg，实际只剩 13781 kg）。改为拷贝一个新 `Craft` 去掉已抛级；
同时 `craft` 字段去掉 `final`，并避免直接改共享的火箭定义。

## 二、日心尺度（按用户选定：真实尺度）

旧值 `SUN_MU = 真实/400` 配「轨道半径 1.516e8（真实/1000）」，两者不自洽：
- 地球公转 46.8 km/s（真实 29.8）
- 地火转移 4.0 小时（真实 258.9 天）
- 出发 Δv 4488 m/s，比本地仿真实测的整段逃逸需求（约 650 m/s）还大
- 到达 Δv 4051 m/s 被当成进近切向速度 → 一进场 4.8 km/s、动压 2.3 MPa，直接结构过载

现改为真实尺度：`SUN_MU = 1.32712440018e20`，半径 1.496e11 / 2.279e11 / 1.082e11。

| 项 | 修复前 | 修复后 | 真实值 |
|---|---|---|---|
| 地球公转 | 46.8 km/s | 29.8 km/s | 29.8 |
| 地火出发 Δv | 4488 | 2944 | 2945 |
| 地火到达 Δv | 4051 | 2648 | 2650 |
| 转移时间 | 4.0 h | 258.8 天 | 258.9 天 |
| 相位角 | 244.7° | 240.6° | — |

**这套真实尺度只用于解析计算，不参与本地仿真**。星球参数（earth R=315 km、g0=9.8）
是游戏的压缩尺度，两者相差约 20 倍，这是有意并存的，不要互相换算。
到达段进场因此必须把真实 Δv 换算到本地尺度：`v∞ = 0.4 × 当地逃逸速度`，
日志里同时打印真实 Δv 与换算值，不隐藏。

## 三、新增：步骤分段标签（Script / Autopilot / Hub）

转移任务的出发段与到达段动作完全不同，塞在一个 `program` 里会让出发段一直等到超时。

```jsonc
{"id": "escape", "segment": "depart", ...}   // 只在出发段跑
{"id": "arrival_final", "segment": "arrive", ...}  // 只在到达段跑
```

- `segment` 只能是 `depart` / `arrive` 或留空；留空表示两段都跑。非法值报 `E008`。
- `Autopilot.setSegmentFilter()` 在 `Hub.runSegment` 里按段设置，不匹配的步骤直接跳过。

## 四、验证结果

在容器本地编译同一份源码，并用 `api` 的 headless 模式跑（与树莓派同一套引擎）。

| 场景 | 结果 |
|---|---|
| 地球入轨（单天体） | 通过：81.5 km，近地点 70.7 km，252.8 s，maxQ 14798 Pa |
| 出发段（earth，segment=depart） | 通过：175 km，ecc≥1 双曲逃逸，443.7 s，燃料 17 t → 13.8 t |
| 到达段（mars，segment=arrive） | 未通过：进场后 Δv 不足，末级燃料耗尽于 2.4 km |

到达段失败是**火箭设计问题**，不是引擎问题：Ares-III 的 S3（132 kN / 13.8 t）
在火星只能提供约 9.6 m/s² 推力与 4.5 km/s Δv，但进场时已 1180 m/s 切向 + 需要捕获、
降轨、着陆，Δv 与推重比都不够。日志如实报「末级燃料低于 0.002」，不再假装通过。

## 五、部署

树莓派 `192.168.31.17`：

```bash
sudo cp /opt/sfsai/sfsai.jar /opt/sfsai/sfsai.jar.bak-<时间戳>   # 已备份
sudo cp sfsai-new.jar /opt/sfsai/sfsai.jar
sudo systemctl restart sfsai-bridge
systemctl is-enabled sfsai-bridge   # enabled
systemctl is-active  sfsai-bridge   # active
```

- 服务是 `DynamicUser=yes` + `StateDirectory=sfsai`，脚本目录 `/var/lib/sfsai/scripts`
- 端口 7790（API）/ 7788（手机 bridge），开机自启已启用
- 从容器侧 `curl http://192.168.31.17:7790/health` 返回 `{"ok":true}`，
  上传脚本跑 headless 得到的数值与容器本地完全一致（252.7 s / 81.5 km）

## 六、仍待处理

- 到达段需要一枚真正的火星着陆级（更高推重比 + 足够 Δv），蓝图侧要重做
- `land` 制导在油门被钳到 0 时会稳态悬停（高度不再下降），到不了 `landed`
- 巡航段是解析解，不做本地仿真；游戏内的航向/窗口对齐仍需靠转移动窗口
