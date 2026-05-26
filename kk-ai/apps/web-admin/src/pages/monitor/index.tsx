import { useState, useEffect, useCallback } from "react";
import { ProCard, StatisticCard } from "@ant-design/pro-components";
import { Badge, Button, Space, Tag, Typography, Spin, message } from "antd";
import {
  ReloadOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { checkAllServices, type ServiceHealth } from "../../services/monitor";

const { Text } = Typography;

function StatusIcon({ status }: { status: ServiceHealth["status"] }) {
  if (status === "ok")
    return <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 20 }} />;
  if (status === "degraded")
    return <WarningOutlined style={{ color: "#faad14", fontSize: 20 }} />;
  return <CloseCircleOutlined style={{ color: "#f5222d", fontSize: 20 }} />;
}

function StatusTag({ status }: { status: ServiceHealth["status"] }) {
  const config = {
    ok: { color: "success" as const, text: "正常" },
    degraded: { color: "warning" as const, text: "降级" },
    down: { color: "error" as const, text: "离线" },
  };
  const c = config[status];
  return <Tag color={c.color}>{c.text}</Tag>;
}

function MetricRow({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        padding: "4px 0",
        fontSize: 13,
      }}
    >
      <Text type="secondary">{label}</Text>
      <Text strong>{value}</Text>
    </div>
  );
}

export default function MonitorPage() {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>("-");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const results = await checkAllServices();
      setServices(results);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (err) {
      message.error("刷新服务状态失败");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 30000);
    return () => clearInterval(timer);
  }, [refresh]);

  const okCount = services.filter((s) => s.status === "ok").length;
  const degradedCount = services.filter((s) => s.status === "degraded").length;
  const downCount = services.filter((s) => s.status === "down").length;

  const avgLatency =
    services.length > 0
      ? Math.round(
          services
            .filter((s) => s.latencyMs > 0)
            .reduce((sum, s) => sum + s.latencyMs, 0) /
            Math.max(1, services.filter((s) => s.latencyMs > 0).length),
        )
      : 0;

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>
        服务监控看板
      </h1>

      {/* 总体统计 */}
      <StatisticCard.Group
        direction="row"
        gutter={[16, 16]}
        style={{ marginBottom: 24 }}
      >
        <StatisticCard
          statistic={{
            title: "在线服务",
            value: `${okCount} / ${services.length || 6}`,
            description: (
              <span style={{ color: "#52c41a" }}>
                {okCount === (services.length || 6) ? "全部正常" : "需关注"}
              </span>
            ),
            icon: (
              <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "降级服务",
            value: degradedCount,
            description: (
              <span
                style={{ color: degradedCount > 0 ? "#faad14" : "#8c8c8c" }}
              >
                {degradedCount > 0 ? "需排查" : "无"}
              </span>
            ),
            icon: (
              <WarningOutlined style={{ color: "#faad14", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "离线服务",
            value: downCount,
            description: (
              <span style={{ color: downCount > 0 ? "#f5222d" : "#8c8c8c" }}>
                {downCount > 0 ? "紧急" : "无"}
              </span>
            ),
            icon: (
              <CloseCircleOutlined style={{ color: "#f5222d", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "平均延迟",
            value: `${avgLatency}ms`,
            description: <span style={{ color: "#8c8c8c" }}>探测延迟</span>,
            icon: (
              <ThunderboltOutlined style={{ color: "#2563eb", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
      </StatisticCard.Group>

      {/* 操作栏 */}
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} loading={loading} onClick={refresh}>
          立即刷新
        </Button>
        <Text type="secondary" style={{ fontSize: 13 }}>
          上次更新: {lastUpdate}（每 30 秒自动刷新）
        </Text>
      </Space>

      {/* 服务卡片网格 */}
      <Spin spinning={loading && services.length === 0}>
        <ProCard gutter={[16, 16]} wrap>
          {services.map((svc) => (
            <ProCard
              key={svc.name}
              title={
                <Space>
                  <StatusIcon status={svc.status} />
                  <span>{svc.name}</span>
                  <StatusTag status={svc.status} />
                </Space>
              }
              subTitle={`端口 ${svc.port}`}
              bordered
              headerBordered
              style={{ flex: 1, minWidth: 280, maxWidth: "100%" }}
              extra={
                <Badge
                  status={
                    svc.status === "ok"
                      ? "success"
                      : svc.status === "degraded"
                        ? "warning"
                        : "error"
                  }
                />
              }
            >
              <MetricRow label="版本" value={svc.version} />
              <MetricRow
                label="延迟"
                value={svc.latencyMs >= 0 ? `${svc.latencyMs}ms` : "-"}
              />
              {/* 服务专属指标 */}
              {svc.metrics.models_loaded !== undefined && (
                <MetricRow
                  label="模型数"
                  value={String(svc.metrics.models_loaded)}
                />
              )}
              {svc.metrics.collections_count !== undefined && (
                <MetricRow
                  label="集合数"
                  value={String(svc.metrics.collections_count)}
                />
              )}
              {svc.metrics.hot_memories !== undefined && (
                <MetricRow
                  label="热记忆"
                  value={String(svc.metrics.hot_memories)}
                />
              )}
              {svc.metrics.prompts_loaded !== undefined && (
                <MetricRow
                  label="Prompt数"
                  value={String(svc.metrics.prompts_loaded)}
                />
              )}
              {svc.metrics.total_records !== undefined && (
                <MetricRow
                  label="记录数"
                  value={`${svc.metrics.total_records} / ${svc.metrics.total_cleaned || 0}`}
                />
              )}
              <MetricRow
                label="检查时间"
                value={new Date(svc.checkedAt).toLocaleTimeString()}
              />
            </ProCard>
          ))}
        </ProCard>
      </Spin>
    </div>
  );
}
