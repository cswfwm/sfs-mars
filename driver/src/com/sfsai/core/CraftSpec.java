package com.sfsai.core;
import java.nio.file.*;
import java.util.*;

/**
 * 从蓝图 JSON 的 craft.stages 构造引擎可用的 Craft。
 * 蓝图字段：name / payload / stages[{dry,fuel,thrustAsl,thrustVac,isp}]
 * 只读，不参与 sfsai/1 的 validate（Script.load 只取 craft.name）。
 */
public final class CraftSpec {
  public static Craft build(String blueprintPath, int fromStage) throws Exception {
    JsonValue root = JsonParser.parse(new String(Files.readAllBytes(Paths.get(blueprintPath)),
        java.nio.charset.StandardCharsets.UTF_8));
    JsonValue c = root.get("craft");
    String name = c.str("name", "craft");
    double payload = c.num("payload", 0);
    List<JsonValue> arr = c.arr("stages");
    List<Craft.Stage> st = new ArrayList<>();
    for (int i = fromStage; i < arr.size(); i++) {
      JsonValue s = arr.get(i);
      st.add(new Craft.Stage(s.num("dry", 0), s.num("fuel", 0), s.num("thrustAsl", 0),
          s.num("thrustVac", 0), s.num("isp", 300)));
    }
    return new Craft(name, payload, st.toArray(new Craft.Stage[0]));
  }

  public static double dryMass(String blueprintPath) throws Exception {
    JsonValue root = JsonParser.parse(new String(Files.readAllBytes(Paths.get(blueprintPath)),
        java.nio.charset.StandardCharsets.UTF_8));
    JsonValue c = root.get("craft");
    double m = c.num("payload", 0);
    for (JsonValue s : c.arr("stages")) m += s.num("dry", 0) + s.num("fuel", 0);
    return m;
  }
}
