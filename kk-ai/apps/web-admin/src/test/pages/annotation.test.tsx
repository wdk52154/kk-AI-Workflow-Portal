import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import AnnotationPage from "../../pages/annotation";

// Mock fetch
global.fetch = vi.fn();

describe("AnnotationPage", () => {
  it("renders annotation title", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
      }),
    } as Response);

    render(
      <BrowserRouter>
        <AnnotationPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("数据标注")).toBeInTheDocument();
    });
  });

  it("displays empty state when no data", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
      }),
    } as Response);

    render(
      <BrowserRouter>
        <AnnotationPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("暂无待标注数据")).toBeInTheDocument();
    });
  });
});
