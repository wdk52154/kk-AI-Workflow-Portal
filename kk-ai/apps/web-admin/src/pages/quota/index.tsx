import { useState, useEffect, useMemo } from "react";
import { ProTable, StatisticCard } from "@ant-design/pro-components";
import { Tag, message } from "antd";
import type { ProColumns } from "@ant-design/pro-components";
import { quotaApi, type QuotaUsage } from "../../services/quota";

interface QuotaSummary {
  todayTotal: number;
  monthTotal: number;
  avgUsageRate: number;
  exceededCount: number;
}

/** 状态 Tag 渲染 */
function StatusTag({ status }: { status: QuotaUsage["status"] }) {
  const config = {
    normal: { color: "success" as const, text: "正常" },
    warning: { color: "warning" as const, text: "预警" },
    exceeded: { color: "error" as const, text: "超限" },
  };
  const c = config[status];
  return <Tag color={c.color}>{c.text}</Tag>;
}

/** 使用率颜色 */
function UsageTag({ rate }: { rate: number }) {
  if (rate >= 100)
    return <span style={{ color: "#ef4444", fontWeight: 600 }}>{rate}%</span>;
  if (rate >= 80)
    return <span style={{ color: "#f59e0b", fontWeight: 600 }}>{rate}%</span>;
  return <span style={{ color: "#52c41a", fontWeight: 600 }}>{rate}%</span>;
}

/** 表格列定义 */
const columns: ProColumns<QuotaUsage>[] = [
  {
    title: "项目名称",
    dataIndex: "project_name",
    key: "project_name",
    search: true,
    sorter: (a, b) => a.project_name.localeCompare(b.project_name),
  },
  {
    title: "今日调用",
    dataIndex: "daily_used",
    key: "daily_used",
    align: "right",
    render: (_, record) =>
      `${record.daily_used.toLocaleString()} / ${record.daily_limit.toLocaleString()}`,
  },
  {
    title: "本月调用",
    dataIndex: "monthly_used",
    key: "monthly_used",
    align: "right",
    render: (_, record) =>
      `${record.monthly_used.toLocaleString()} / ${record.monthly_limit.toLocaleString()}`,
  },
  {
    title: "使用率",
    dataIndex: "usage_rate",
    key: "usage_rate",
    align: "right",
    sorter: (a, b) => a.usage_rate - b.usage_rate,
    render: (_, record) => <UsageTag rate={record.usage_rate} />,
  },
  {
    title: "状态",
    dataIndex: "status",
    key: "status",
    align: "center",
    filters: [
      { text: "正常", value: "normal" },
      { text: "预警", value: "warning" },
      { text: "超限", value: "exceeded" },
    ],
    onFilter: (value, record) => record.status === value,
    render: (_, record) => <StatusTag status={record.status} />,
  },
];

function useQuotaData() {
  const [data, setData] = useState<QuotaUsage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    quotaApi
      .getUsage()
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "加载失败");
          message.error("配额数据加载失败");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const summary = useMemo<QuotaSummary>(() => {
    if (data.length === 0) {
      return {
        todayTotal: 0,
        monthTotal: 0,
        avgUsageRate: 0,
        exceededCount: 0,
      };
    }
    const todayTotal = data.reduce((sum, d) => sum + d.daily_used, 0);
    const monthTotal = data.reduce((sum, d) => sum + d.monthly_used, 0);
    const avgUsageRate =
      data.reduce((sum, d) => sum + d.usage_rate, 0) / data.length;
    const exceededCount = data.filter((d) => d.status === "exceeded").length;
    return {
      todayTotal,
      monthTotal,
      avgUsageRate: Math.round(avgUsageRate * 10) / 10,
      exceededCount,
    };
  }, [data]);

  return { data, loading, error, summary };
}

export default function QuotaPage() {
  const { data, loading, error, summary } = useQuotaData();

  if (error) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>
          配额管理
        </h2>
        <p style={{ color: "#ef4444", marginBottom: 16 }}>
          数据加载失败: {error}
        </p>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: "8px 16px",
            borderRadius: 6,
            border: "none",
            background: "#2563eb",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          重新加载
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>
        配额管理
      </h1>

      {/* KPI 卡片 */}
      <StatisticCard.Group
        direction="row"
        gutter={[16, 16]}
        style={{ marginBottom: 24 }}
      >
        <StatisticCard
          statistic={{
            title: "今日总调用",
            value: summary.todayTotal.toLocaleString(),
            description: <span style={{ color: "#8c8c8c" }}>所有项目合计</span>,
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "本月总调用",
            value: summary.monthTotal.toLocaleString(),
            description: <span style={{ color: "#8c8c8c" }}>所有项目合计</span>,
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "平均使用率",
            value: `${summary.avgUsageRate}%`,
            description: <span style={{ color: "#8c8c8c" }}>项目平均</span>,
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "超限项目",
            value: summary.exceededCount,
            description: <span style={{ color: "#ef4444" }}>需关注</span>,
          }}
          style={{ flex: 1 }}
        />
      </StatisticCard.Group>

      {/* 配额明细表格 */}
      <ProTable<QuotaUsage>
        headerTitle="项目配额明细"
        columns={columns}
        dataSource={data}
        rowKey="project_name"
        loading={loading}
        search={{ labelWidth: "auto" }}
        pagination={{ pageSize: 10 }}
        toolBarRender={() => [
          <span key="tip" style={{ color: "#8c8c8c", fontSize: 13 }}>
            使用率 ≥ 80% 黄色预警，≥ 100% 红色超限
          </span>,
        ]}
        locale={{ emptyText: "暂无配额数据" }}
      />
    </div>
  );
}
