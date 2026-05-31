import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  querySales,
  startRoleplay,
  chatRoleplay,
  evaluateRoleplay,
  listScripts,
  createScript,
  deleteScript,
} from "../../services/sales";

describe("sales service", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("querySales should return recommended scripts", async () => {
    const mockResponse = {
      recommended_scripts: [{ id: "s1", title: "话术1", content: "内容" }],
      objection_handler: null,
      user_facts: [],
      confidence: 0.85,
    };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await querySales("客户问题");
    expect(result.recommended_scripts).toHaveLength(1);
    expect(result.confidence).toBe(0.85);
    expect(global.fetch).toHaveBeenCalledWith(
      "/v1/sales/query",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("querySales should throw on error", async () => {
    (global.fetch as any).mockResolvedValueOnce({ ok: false });
    await expect(querySales("问题")).rejects.toThrow("查询失败");
  });

  it("startRoleplay should return session", async () => {
    const mockResponse = {
      session_id: "sess-123",
      customer_profile: { name: "犹豫型客户" },
      opening_message: "我再想想...",
      hints: ["hint1"],
    };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await startRoleplay("hesitant");
    expect(result.session_id).toBe("sess-123");
  });

  it("chatRoleplay should return customer reply", async () => {
    const mockResponse = {
      customer_reply: "太贵了",
      real_time_score: { standardization: 80 },
      hints: [],
    };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await chatRoleplay("sess-123", "我们的产品质量很好");
    expect(result.customer_reply).toBe("太贵了");
  });

  it("evaluateRoleplay should return score", async () => {
    const mockResponse = {
      total_score: 82.5,
      dimensions: {},
      suggestions: ["建议1"],
      transcript: [],
    };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await evaluateRoleplay("sess-123");
    expect(result.total_score).toBe(82.5);
  });

  it("listScripts should return paginated data", async () => {
    const mockResponse = { data: [], total: 0, page: 1, page_size: 20 };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await listScripts();
    expect(result.total).toBe(0);
  });

  it("createScript should create and return script", async () => {
    const mockResponse = { id: "s1", title: "话术" };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await createScript({
      title: "话术",
      content: "内容",
      category: "general",
      tags: [],
      scenario: "",
      conversion_rate: 0,
      usage_count: 0,
    });
    expect(result.id).toBe("s1");
  });

  it("deleteScript should call DELETE endpoint", async () => {
    (global.fetch as any).mockResolvedValueOnce({ ok: true });
    await deleteScript("s1");
    expect(global.fetch).toHaveBeenCalledWith(
      "/v1/sales/scripts/s1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
