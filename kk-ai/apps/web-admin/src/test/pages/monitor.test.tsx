import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import MonitorPage from "../../pages/monitor";

// Mock fetch for health checks
global.fetch = vi.fn();

describe("MonitorPage", () => {
  it("renders monitor title", () => {
    vi.mocked(fetch).mockRejectedValue(new Error("down"));
    render(
      <BrowserRouter>
        <MonitorPage />
      </BrowserRouter>,
    );
    expect(screen.getByText("服务监控看板")).toBeInTheDocument();
  });

  it("displays service cards after loading", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        status: "ok",
        version: "0.1.0",
        models_loaded: 3,
      }),
    } as Response);

    render(
      <BrowserRouter>
        <MonitorPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("在线服务")).toBeInTheDocument();
    });
  });
});
