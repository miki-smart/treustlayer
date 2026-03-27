import { describe, it, expect } from "vitest";
import { evaluatePolicy } from "./policy";

describe("evaluatePolicy", () => {
  it("rejects tier_0", () => {
    const p = evaluatePolicy("tier_0", 100, false);
    expect(p.decision).toBe("reject");
  });

  it("rejects any tier when risk_flag", () => {
    const p = evaluatePolicy("tier_2", 90, true);
    expect(p.decision).toBe("reject");
    expect(p.reason).toBe("risk_flag_active");
  });

  it("tier_1 score 55 allows step-up band", () => {
    const p = evaluatePolicy("tier_1", 55, false);
    expect(p.decision).toBe("allow_with_step_up");
    expect(p.maxSingleTxn).toBe(100);
    expect(p.stepUpRequired).toBe(true);
  });

  it("tier_2 score 80 allows high limits", () => {
    const p = evaluatePolicy("tier_2", 80, false);
    expect(p.decision).toBe("allow");
    expect(p.maxSingleTxn).toBe(5000);
  });
});
