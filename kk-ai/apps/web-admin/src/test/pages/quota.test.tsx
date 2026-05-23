import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import QuotaPage from "../../pages/quota";

describe("QuotaPage", () => {
  it("renders page title", () => {
    render(<QuotaPage />);
    expect(screen.getByText("配额管理")).toBeInTheDocument();
  });

  it("renders KPI cards", () => {
    render(<QuotaPage />);
    expect(screen.getByText("今日总调用")).toBeInTheDocument();
    expect(screen.getByText("本月总调用")).toBeInTheDocument();
    expect(screen.getByText("平均使用率")).toBeInTheDocument();
    expect(screen.getByText("超限项目")).toBeInTheDocument();
  });

  it("renders project table", () => {
    render(<QuotaPage />);
    expect(screen.getByText("项目配额明细")).toBeInTheDocument();
    expect(screen.getByText("康康 AI 中台")).toBeInTheDocument();
  });

  it("marks exceeded projects in red", () => {
    render(<QuotaPage />);
    expect(screen.getByText("超限")).toBeInTheDocument();
  });

  it("marks warning projects in yellow", () => {
    render(<QuotaPage />);
    expect(screen.getByText("预警")).toBeInTheDocument();
  });
});
