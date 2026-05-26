import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import PromptsPage from "../../pages/prompts";

// Mock fetch
global.fetch = vi.fn();

describe("PromptsPage", () => {
  it("renders prompts title", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
      }),
    } as Response);

    render(
      <BrowserRouter>
        <PromptsPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Prompt 管理")).toBeInTheDocument();
    });
  });

  it("displays empty state", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
      }),
    } as Response);

    render(
      <BrowserRouter>
        <PromptsPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("暂无 Prompt 模板")).toBeInTheDocument();
    });
  });
});
