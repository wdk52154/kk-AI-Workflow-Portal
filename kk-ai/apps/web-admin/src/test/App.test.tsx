import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "../App";

describe("App", () => {
  it("renders without crashing", () => {
    render(
      <App
        theme="light"
        resolvedTheme="light"
        setTheme={() => {}}
        toggleTheme={() => {}}
      />,
    );
    expect(screen.getByText("康康 AI")).toBeInTheDocument();
  });

  it("displays dashboard title", () => {
    render(
      <App
        theme="light"
        resolvedTheme="light"
        setTheme={() => {}}
        toggleTheme={() => {}}
      />,
    );
    expect(screen.getByText("中台管理后台")).toBeInTheDocument();
  });
});
