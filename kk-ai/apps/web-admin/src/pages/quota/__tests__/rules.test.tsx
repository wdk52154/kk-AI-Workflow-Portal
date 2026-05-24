import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import QuotaRulesPage from "../rules";

vi.mock("../../../services/quota", () => ({
  quotaApi: {
    getRules: vi.fn().mockResolvedValue({
      items: [
        {
          id: "rule-1",
          project_name: "project-a",
          daily_limit: 1000,
          monthly_limit: 30000,
          alert_threshold: 80,
          status: "active" as const,
          created_at: "2026-05-23T00:00:00Z",
          updated_at: "2026-05-23T00:00:00Z",
        },
        {
          id: "rule-2",
          project_name: "project-b",
          daily_limit: 5000,
          monthly_limit: 100000,
          alert_threshold: 90,
          status: "active" as const,
          created_at: "2026-05-23T00:00:00Z",
          updated_at: "2026-05-23T00:00:00Z",
        },
      ],
      total: 2,
      page: 1,
      page_size: 20,
    }),
    getProjects: vi.fn().mockResolvedValue({
      items: ["project-a", "project-b", "project-c"],
    }),
    createRule: vi.fn().mockResolvedValue({}),
    updateRule: vi.fn().mockResolvedValue({}),
    deleteRule: vi.fn().mockResolvedValue({}),
  },
}));

describe("QuotaRulesPage", () => {
  it("renders quota rules list", async () => {
    render(<QuotaRulesPage />);
    await waitFor(() => {
      expect(screen.getByText("project-a")).toBeInTheDocument();
      expect(screen.getByText("project-b")).toBeInTheDocument();
    });
  });

  it("opens create modal when clicking new button", async () => {
    render(<QuotaRulesPage />);
    const btn = screen.getByText("新建规则");
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByText("新建配额规则")).toBeInTheDocument();
    });
  });

  it("shows delete buttons for each rule", async () => {
    const { container } = render(<QuotaRulesPage />);
    await waitFor(() => {
      expect(screen.getByText("project-a")).toBeInTheDocument();
    });
    // Find delete buttons by antd danger button style
    const deleteBtns = container.querySelectorAll("button.ant-btn-dangerous");
    expect(deleteBtns.length).toBeGreaterThan(0);
  });
});
