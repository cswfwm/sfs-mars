# Ares-III 蓝图与飞行脚本 · 验证记录

## 产物

| 文件 | 内容 |
|---|---|
| `blueprint/ares-iii.json` | 三级运载器蓝图（质量、推力、Isp 可被官方引擎直接装载） |
| `scripts/earth_ascent.json` | 地球 80 km 入轨 |
| `scripts/earth_escape.json` | 转移注入（地球 80 km LEO → 双曲轨道） |
| `scripts/mars_capture_landing.json` | 火星捕获 → 降轨 → 动力着陆 |
| `driver/` | 自研驱动：用官方 `SimVehicle`/`Autopilot` 跑蓝图（`sim` 只认内置三种火箭） |
| `tools/check_blueprint.py` | 蓝图 Δv / TWR / 质量比自检 |

## 驱动说明

官方 `sfsai.jar` 的 `sim` 只能选择 `ascent|lander|heavy` 三种内置模型，
脚本里的 `craft` 块只读 `name`。所以本项目的火箭用 `driver/` 直接构造
`com.sfsai.core.Craft`，其余（物理、制导、飞控、事件）全部是官方类：

```bash
sh driver/run.sh blueprint/ares-iii.json scripts/earth_ascent.json earth 900
sh driver/run.sh blueprint/ares-iii.json scripts/mars_capture_landing.json mars 3000 150000 0 2 579
```

`mars_capture_landing.json` 的初始条件是火星本地 150 km 圆轨道（vs=0, hs=579 m/s），
因为引擎是单天体 2D 模型，没有星际会合。

## 结果（官方引擎，2026-11-19）

| 场景 | 结束原因 | 末态 | 最大动压 |
|---|---|---|---|
| 地球入轨 | 脚本正常结束 | alt 80.4 km, apo 81.2 / peri 71.0 km, 残油 63.2% | 15459 Pa |
| 转移注入 | 脚本正常结束 | alt 85.9 km, ecc 1.003, 残油 54.8% | 0 Pa |
| 火星捕获着陆 | 脚本正常结束 | 触地 alt 0.0 km, vs -0.2 m/s, 残油 69.5% | 9070 Pa |

## 树莓派 API（192.168.31.17:7790）

- `lint`：三个脚本全部 `ok:true, warnings:[]`
- `headless`：火星段 `可行性通过`，地球入轨 `未通过（末级燃料低于 0.01）`
  —— headless 固定用内置 **两级入轨器（21000 kg）**，不是本蓝图（80600 kg 三级）。
  故 headless 只验证脚本流程不报错，性能结论以上表为准。

## 关于「飞到火星」

引擎（`Bodies`）只有 earth/moon/mars/venus 四个独立天体，`SimVehicle` 是单中心天体的
2D 模型，没有多体、没有转移轨道求解。因此"飞到火星"在可验证范围内拆成三段：

1. 地球入轨（完整验证）
2. 地球逃逸 / 转移注入（完整验证，Δv 燃烧）
3. 火星本地捕获与着陆（完整验证）

蓝图总 Δv 9380 m/s，其中地球段约 2981+1899、火星段 4501，预算仍有余量。
真正的跨天体会合需要 SFS 游戏内的地图转移窗口，本工具链无法仿真。
