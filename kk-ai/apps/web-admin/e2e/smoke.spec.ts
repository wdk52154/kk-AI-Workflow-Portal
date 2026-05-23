import { test, expect } from "@playwright/test";

test.describe("Smoke Tests", () => {
  test("homepage loads with correct title", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/康康 AI/);
  });

  test("dashboard displays KPI cards", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("今日调用")).toBeVisible();
    await expect(page.getByText("活跃项目")).toBeVisible();
    await expect(page.getByText("平均延迟")).toBeVisible();
    await expect(page.getByText("异常告警")).toBeVisible();
  });

  test("theme toggle buttons are visible", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("button", { name: /亮色|暗色|系统/ }).first(),
    ).toBeVisible();
  });

  test("navigation sidebar is visible on desktop", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("总览")).toBeVisible();
    await expect(page.getByText("模型管理")).toBeVisible();
  });
});
