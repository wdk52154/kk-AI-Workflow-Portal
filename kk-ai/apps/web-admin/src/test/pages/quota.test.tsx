import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import QuotaPage from "../../pages/quota";

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

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

  it("renders project table", () => {
    renderWithRouter(<QuotaPage />);
    expect(screen.getByText("项目配额明细")).toBeInTheDocument();
    expect(screen.getByText("康康 AI 中台")).toBeInTheDocument();
  });

  it("marks exceeded projects in red", () => {
    renderWithRouter(<QuotaPage />);
    expect(screen.getByText("超限")).toBeInTheDocument();
  });

  it("marks warning projects in yellow", () => {
    renderWithRouter(<QuotaPage />);
    expect(screen.getByText("预警")).toBeInTheDocument();
  });
});
