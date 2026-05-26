import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import QuotaPage from "../../pages/quota";

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

const mockUsageData = [
  {
    project_name: "康康 AI 中台",
    daily_used: 5200,
    daily_limit: 5000,
    monthly_used: 85000,
    monthly_limit: 100000,
    usage_rate: 104,
    status: "exceeded" as const,
  },
  {
    project_name: "客户 A",
    daily_used: 3200,
    daily_limit: 5000,
    monthly_used: 72000,
    monthly_limit: 100000,
    usage_rate: 72,
    status: "normal" as const,
  },
  {
    project_name: "内部测试",
    daily_used: 4200,
    daily_limit: 5000,
    monthly_used: 82000,
    monthly_limit: 100000,
    usage_rate: 84,
    status: "warning" as const,
  },
];

vi.mock("../../services/quota", () => ({
  quotaApi: {
    getUsage: vi.fn(() => Promise.resolve(mockUsageData)),
  },
}));

describe("QuotaPage", () => {
  it("renders page title", () => {
    renderWithRouter(<QuotaPage />);
    expect(screen.getByText("配额管理")).toBeInTheDocument();
  });

  it("renders KPI cards", () => {
    renderWithRouter(<QuotaPage />);
    expect(screen.getByText("今日总调用")).toBeInTheDocument();
    expect(screen.getByText("本月总调用")).toBeInTheDocument();
    expect(screen.getByText("平均使用率")).toBeInTheDocument();
    expect(screen.getByText("超限项目")).toBeInTheDocument();
  });

  it("renders project table", async () => {
    renderWithRouter(<QuotaPage />);
    expect(screen.getByText("项目配额明细")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("康康 AI 中台")).toBeInTheDocument();
    });
  });

  it("marks exceeded projects in red", async () => {
    renderWithRouter(<QuotaPage />);
    await waitFor(() => {
      expect(screen.getByText("超限")).toBeInTheDocument();
    });
  });

  it("marks warning projects in yellow", async () => {
    renderWithRouter(<QuotaPage />);
    await waitFor(() => {
      expect(screen.getByText("预警")).toBeInTheDocument();
    });
  });
});
