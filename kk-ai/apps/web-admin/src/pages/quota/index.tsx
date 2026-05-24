import { useState, useMemo } from "react";
import { ProTable, StatisticCard } from "@ant-design/pro-components";
import { Tag } from "antd";
import type { ProColumns } from "@ant-design/pro-components";

interface QuotaProject {
  projectId: string;
  projectName: string;
  todayUsed: number;
  todayLimit: number;
  monthUsed: number;
  monthLimit: number;
  usageRate: number;
  status: "normal" | "warning" | "exceeded";
}

interface QuotaSummary {
  todayTotal: number;
  monthTotal: number;
  avgUsageRate: number;
  exceededCount: number;
}

/** 模拟数据 */
const mockData: QuotaProject[] = [
  {
    projectId: "proj_001",
    projectName: "康康 AI 中台",
    todayUsed: 5234,
    todayLimit: 10000,
    monthUsed: 89321,
    monthLimit: 300000,
    usageRate: 52.3,
    status: "normal",
  },
  {
    projectId: "proj_002",
    projectName: "客户 A 项目",
    todayUsed: 8500,
    todayLimit: 10000,
    monthUsed: 245000,
    monthLimit: 300000,
    usageRate: 85.0,
    status: "warning",
  },
  {
    projectId: "proj_003",
    projectName: "内部测试项目",
    todayUsed: 12000,
    todayLimit: 10000,
    monthUsed: 320000,
    monthLimit: 300000,
    usageRate: 100.0,
    status: "exceeded",
  },
];

const mockSummary: QuotaSummary = {
  todayTotal: 25734,
  monthTotal: 654321,
  avgUsageRate: 79.1,
  exceededCount: 1,
};

/** 状态 Tag 渲染 */
function StatusTag({ status }: { status: QuotaProject["status"] }) {
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
const columns: ProColumns<QuotaProject>[] = [
  {
    title: "项目名称",
    dataIndex: "projectName",
    key: "projectName",
    search: true,
    sorter: (a, b) => a.projectName.localeCompare(b.projectName),
  },
  {
    title: "今日调用",
    dataIndex: "todayUsed",
    key: "todayUsed",
    align: "right",
    render: (_, record) =>
      `${record.todayUsed.toLocaleString()} / ${record.todayLimit.toLocaleString()}`,
  },
  {
    title: "本月调用",
    dataIndex: "monthUsed",
    key: "monthUsed",
    align: "right",
    render: (_, record) =>
      `${record.monthUsed.toLocaleString()} / ${record.monthLimit.toLocaleString()}`,
  },
  {
    title: "使用率",
    dataIndex: "usageRate",
    key: "usageRate",
    align: "right",
    sorter: (a, b) => a.usageRate - b.usageRate,
    render: (_, record) => <UsageTag rate={record.usageRate} />,
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

export default function QuotaPage() {
  const [loading, setLoading] = useState(false);

  const summary = useMemo(() => mockSummary, []);

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
      <ProTable<QuotaProject>
        headerTitle="项目配额明细"
        columns={columns}
        dataSource={mockData}
        rowKey="projectId"
        loading={loading}
        search={{ labelWidth: "auto" }}
        pagination={{ pageSize: 10 }}
        toolBarRender={() => [
          <span key="tip" style={{ color: "#8c8c8c", fontSize: 13 }}>
            使用率 ≥ 80% 黄色预警，≥ 100% 红色超限
          </span>,
        ]}
        onLoad={() => {
          setLoading(true);
          setTimeout(() => setLoading(false), 300);
        }}
        locale={{ emptyText: "暂无配额数据" }}
      />
    </div>
  );
}
