#!/usr/bin/env python3
"""蓝图仿真：按 sfsai SimVehicle 的同一套公式复算，验证蓝图火箭在本引擎物理下能否完成任务。"""
import json, math, sys

G0 = 9.80665

class Body:
    def __init__(s, i, r, g0, atmo, rho0):
        s.id, s.radius, s.g0, s.atmo, s.rho0 = i, r, g0, atmo, rho0
    def mu(s): return s.g0 * s.radius * s.radius
    def density(s, alt):
        if s.atmo <= 0 or alt >= s.atmo: return 0.0
        return s.rho0 * math.exp(-max(alt,0) / (s.atmo / 6.0))

BODIES = {
 "earth": Body("earth", 315000, 9.8, 30000, 1.225),
 "mars":  Body("mars", 170000, 3.71, 8000, 0.9),
}

class Stage:
    def __init__(s, d):
        s.dry, s.fuel0, s.fuel = d["dry"], d["fuel"], d["fuel"]
        s.thrustAsl, s.thrustVac, s.isp = d["thrustAsl"], d["thrustVac"], d["isp"]
        s.id = d.get("id", "S")

def thrust_now(st, alt, body, throttle, engineOn):
    if st is None or not engineOn or st.fuel <= 0: return 0.0
    f = 0.0
    if body.atmo > 0:
        f = max(0.0, 1.0 - max(alt,0)/body.atmo)
    return (st.thrustVac + (st.thrustAsl - st.thrustVac) * f) * throttle

def run(bp_path, body_id, pitch_program, dry_cut_alt=42000, tick=0.05, max_t=900, verbose=True):
    b = json.load(open(bp_path))
    c = b["craft"]
    stages = [Stage(x) for x in c["stages"]]
    payload = c.get("payload", 0)
    body = BODIES[body_id]
    idx = 0
    alt = 0.0; vs = 0.0; hs = 0.0
    t = 0.0; throttle = 1.0; engineOn = True
    trace = []
    while t < max_t:
        # 分级
        if stages[idx].fuel <= 0 and idx < len(stages)-1:
            idx += 1
        cur = stages[idx]
        mass = payload + sum(s.dry for s in stages[idx:]) + sum(s.fuel for s in stages[idx:])
        thr = thrust_now(cur, alt, body, throttle, engineOn)
        g = body.g0 * (body.radius/(body.radius+max(alt,0)))**2
        mu = body.mu()
        r = body.radius + max(alt, 0)
        hspeed_orb = math.sqrt(mu/r)
        rho = body.density(max(alt,0))
        speed = math.hypot(vs, hs)
        drag = 0.5*rho*speed*speed*4.5 if rho > 0 and speed > 0.01 else 0.0
        # 姿态：重力转弯俯仰程序
        pitch = pitch_program(alt, t)
        pr = math.radians(pitch)
        ax = (thr*math.cos(pr) - drag*vs/speed)/mass if speed > 0.01 else thr*math.cos(pr)/mass
        ay = (thr*math.sin(pr) - drag*hs/speed)/mass if speed > 0.01 else thr*math.sin(pr)/mass
        vs += ax*tick
        hs += ay*tick
        alt += vs*tick
        # 燃耗
        if thr > 0:
            mdot = thr/(cur.isp*G0)
            cur.fuel = max(0.0, cur.fuel - mdot*tick)
        # 圆轨道判据
        e = 0.5*speed*speed - mu/r
        h = (alt+body.radius)*(hs)
        ecc = math.sqrt(max(0.0, 1 + 2*e*h*h/(mu*mu)))
        a = -mu/(2*e) if abs(e) > 1e-12 else 1e12
        apo = (a*(1+ecc) - body.radius)/1000 if e < 0 else 999999
        peri = (a*(1-ecc) - body.radius)/1000 if e < 0 else -999999
        if verbose and abs(t*10 - round(t*10)) < 1e-9 and int(t*10) % 100 == 0:
            print(f"t={t:6.1f}s stage={idx} alt={alt/1000:7.1f}km vs={vs:7.1f} hs={hs:7.1f} "
                  f"apo={apo:8.1f} peri={peri:8.1f} m={mass:8.0f} fuel={cur.fuel:7.0f}")
        trace.append((t, alt, vs, hs, apo, peri))
        if apo > 80 and peri > 70:
            print(f"★ 入轨成功 t={t:.1f}s alt={alt/1000:.1f}km apo={apo:.1f} peri={peri:.1f}")
            return trace, "ORBIT"
        t += tick
        if alt < -1: return trace, "CRASH"
    return trace, "TIMEOUT"

if __name__ == "__main__":
    bp = sys.argv[1]; body = sys.argv[2] if len(sys.argv) > 2 else "earth"
    tr, why = run(bp, body, lambda alt,t: max(8.0, 90 - 90*min(1.0, max(0.0, (alt-1200)/(42000-1200)))**0.65))
    print("结果:", why)
