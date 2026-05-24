import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import App from "../App";

describe("App", () => {
  it("renders without crashing", () => {
    render(
      <BrowserRouter>
        <App
          theme="light"
          resolvedTheme="light"
          setTheme={() => {}}
          toggleTheme={() => {}}
        />
      </BrowserRouter>,
    );
    expect(screen.getByText("康康 AI")).toBeInTheDocument();
  });

  it("displays dashboard title", () => {
    render(
      <BrowserRouter>
        <App
          theme="light"
          resolvedTheme="light"
          setTheme={() => {}}
          toggleTheme={() => {}}
        />
      </BrowserRouter>,
    );
    expect(screen.getByText("中台管理后台")).toBeInTheDocument();
  });
});
