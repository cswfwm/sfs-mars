#!/usr/bin/env python3
"""蓝图规格自检：质量、Δv、各级 TWR、质量比。纯算术，不依赖 JVM。"""
import json, sys, math

def main(path):
    b = json.load(open(path))
    c = b["craft"]
    stages = c["stages"]
    payload = c.get("payload", 0)
    G0 = 9.80665
    dv_total = 0.0
    upper = payload
    print(f"蓝图: {b['meta']['name']}  v{b['meta'].get('version','-')}")
    print(f"载荷: {payload:.0f} kg  级数: {len(stages)}")
    # 自末级向上计算
    masses = []
    for i, s in enumerate(stages):
        m0 = s["dry"] + s["fuel"] + sum(x["dry"] + x["fuel"] for x in stages[i+1:]) + payload
        mf = s["dry"] + sum(x["dry"] + x["fuel"] for x in stages[i+1:]) + payload
        dv = s["isp"] * G0 * math.log(m0 / mf)
        masses.append((m0, mf, dv))
        print(f"  {s['id']:3s} m0={m0:8.0f} mf={mf:8.0f} mr={m0/mf:5.2f} "
              f"isp={s['isp']:5.0f} Δv={dv:6.0f} m/s  "
              f"TWR0={s['thrustAsl']/(m0*9.8):5.2f}")
        dv_total += dv
    print(f"总 Δv(真空) = {dv_total:.0f} m/s")
    # 地球（SFS 尺度）入轨所需 ≈ 1.75~1.85 km/s 理想，加损失约 2.2
    need = {"earth_orbit_80km": 2200, "mars_capture": 900, "mars_landing": 700}
    print("参考预算:", ", ".join(f"{k}={v}" for k,v in need.items()),
          f"合计={sum(need.values())}")
    ok = dv_total >= sum(need.values())
    print(("✓ 总 Δv 足够" if ok else "✗ 总 Δv 不足") + f"（{dv_total:.0f} vs {sum(need.values())}）")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
