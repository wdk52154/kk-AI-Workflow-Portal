const API_BASE =
  (import.meta as unknown as { env: Record<string, string> }).env
    .VITE_API_BASE_URL || "http://localhost:8000";

export interface ServiceHealth {
  name: string;
  port: number;
  url: string;
  status: "ok" | "degraded" | "down";
  version: string;
  metrics: Record<string, unknown>;
  latencyMs: number;
  checkedAt: string;
}

const SERVICES = [
  { name: "MCP HUB", port: 8000, path: "/health" },
  { name: "LLM Gateway", port: 9001, path: "/health" },
  { name: "RAG Service", port: 9002, path: "/health" },
  { name: "Memory Service", port: 9003, path: "/health" },
  { name: "Prompt Center", port: 9004, path: "/health" },
  { name: "Data Center", port: 9005, path: "/health" },
];

function getBaseHost(): string {
  // Strip port from API_BASE, e.g. "http://localhost:8000" -> "http://localhost"
  try {
    const url = new URL(API_BASE);
    return `${url.protocol}//${url.hostname}`;
  } catch {
    return API_BASE.replace(/:\d+$/, "");
  }
}

export async function checkAllServices(): Promise<ServiceHealth[]> {
  const base = getBaseHost();
  return Promise.all(
    SERVICES.map(async (svc) => {
      const start = performance.now();
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        const res = await fetch(`${base}:${svc.port}${svc.path}`, {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        const latency = Math.round(performance.now() - start);
        if (res.ok) {
          const data = (await res.json()) as Record<string, unknown>;
          return {
            name: svc.name,
            port: svc.port,
            url: `${base}:${svc.port}`,
            status: "ok" as const,
            version: String(data.version || "unknown"),
            metrics: data,
            latencyMs: latency,
            checkedAt: new Date().toISOString(),
          };
        }
        return {
          name: svc.name,
          port: svc.port,
          url: `${base}:${svc.port}`,
          status: "degraded" as const,
          version: "unknown",
          metrics: {},
          latencyMs: latency,
          checkedAt: new Date().toISOString(),
        };
      } catch {
        return {
          name: svc.name,
          port: svc.port,
          url: `${base}:${svc.port}`,
          status: "down" as const,
          version: "unknown",
          metrics: {},
          latencyMs: -1,
          checkedAt: new Date().toISOString(),
        };
      }
    }),
  );
}
