package com.sfsai.core;

import java.nio.file.*;

/**
 * 官方引擎 + 自研蓝图：用 sfsai 的 SimVehicle/自动飞控跑 blueprint 里定义的火箭。
 * 放在 com.sfsai.core 包内，以便给 SimVehicle 设初速度（vx/vy 为包私有）。
 * 用法: java com.sfsai.core.Fly <blueprint.json> <script.json> [body] [maxSec] [startAlt] [startVs] [fromStage] [startHs]
 */
public final class Fly {
  public static void main(String[] a) throws Exception {
    String bp = a[0], sp = a[1];
    String body = a.length > 2 ? a[2] : "earth";
    double max = a.length > 3 ? Double.parseDouble(a[3]) : 900;
    double alt = a.length > 4 ? Double.parseDouble(a[4]) : 0;
    double vs = a.length > 5 ? Double.parseDouble(a[5]) : 0;
    int from = a.length > 6 ? Integer.parseInt(a[6]) : 0;
    double hs = a.length > 7 ? Double.parseDouble(a[7]) : 0;

    String src = new String(Files.readAllBytes(Paths.get(sp)), java.nio.charset.StandardCharsets.UTF_8);
    Script sc = Script.load(src, sp);
    Craft craft = CraftSpec.build(bp, from);
    double tick = sc.tickMs / 1000.0;

    SimVehicle v = new SimVehicle(craft, body, tick, alt, vs);
    v.vx = hs;
    Autopilot ap = new Autopilot(sc);
    ap.arm();
    ap.startNow(0);

    System.out.printf("=== 蓝图飞行: %s / %s (body=%s tick=%dms 初始 alt=%.1fkm vs=%.0f hs=%.0f)%n",
        sc.name, craft.name, body, sc.tickMs, alt / 1000, vs, hs);
    Runner.Result r = Runner.run(v, ap, tick, max, true, System.out);

    System.out.println();
    System.out.println("--- 结果 ---");
    System.out.println("阶段: " + r.phase + "  原因: " + r.reason);
    System.out.printf("仿真 %.1fs  maxAlt %.1f km  maxSpeed %.0f m/s  maxQ %.0f Pa  crashed=%s%n",
        r.simTime, r.maxAlt / 1000, r.maxSpeed, r.maxQ, r.crashed);
    Telemetry t = r.last;
    System.out.printf("末态: alt %.1f km  vs %.1f  hs %.1f  apo %.1f km  peri %.1f km  ecc %.3f  fuel %.3f  stage %d  mass %.0f kg%n",
        t.altitude / 1000, t.vs, t.hs, t.apoapsis / 1000, t.periapsis / 1000, t.ecc, t.fuel, t.stage, t.mass);
    System.exit(r.crashed ? 3 : 0);
  }
}
