import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ApiKeysPage from "../../pages/apiKeys";

// Mock fetch
global.fetch = vi.fn();

describe("ApiKeysPage", () => {
  it("renders api keys title", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
      }),
    } as Response);

    render(
      <BrowserRouter>
        <ApiKeysPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("API Key 管理")).toBeInTheDocument();
    });
  });

  it("displays empty state", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
      }),
    } as Response);

    render(
      <BrowserRouter>
        <ApiKeysPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("暂无 API Key")).toBeInTheDocument();
    });
  });
});
