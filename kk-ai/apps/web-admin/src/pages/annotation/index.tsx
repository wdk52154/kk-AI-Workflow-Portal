import { useState, useEffect, useCallback } from "react";
import { ProTable, ProCard, StatisticCard } from "@ant-design/pro-components";
import {
  Button,
  Drawer,
  Form,
  Input,
  Select,
  Rate,
  Tag,
  Space,
  message,
  Spin,
  Typography,
} from "antd";
import type { ProColumns } from "@ant-design/pro-components";
import { EditOutlined, SaveOutlined } from "@ant-design/icons";
import {
  annotationApi,
  type PendingAnnotationItem,
  type AnnotationStatsResponse,
} from "../../services/annotation";

const { TextArea } = Input;
const { Text } = Typography;

const INTENT_OPTIONS = [
  "咨询",
  "投诉",
  "购买意向",
  "高转化",
  "客户异议",
  "其他",
];

const EMOTION_OPTIONS = [
  { value: "positive", label: "积极" },
  { value: "neutral", label: "中性" },
  { value: "negative", label: "消极" },
];

interface AnnotationForm {
  intent: string;
  emotion: string;
  quality_score: number;
  tags: string[];
  notes: string;
}

export default function AnnotationPage() {
  const [data, setData] = useState<PendingAnnotationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<AnnotationStatsResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentRecord, setCurrentRecord] =
    useState<PendingAnnotationItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm<AnnotationForm>();

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const [pendingRes, statsRes] = await Promise.all([
        annotationApi.getPending({ page, page_size: pageSize }),
        annotationApi.getStats(),
      ]);
      setData(pendingRes.items);
      setTotal(pendingRes.total);
      setStats(statsRes);
    } catch (err) {
      message.error("加载数据失败");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAnnotate = (record: PendingAnnotationItem) => {
    setCurrentRecord(record);
    form.resetFields();
    setDrawerOpen(true);
  };

  const handleSubmit = async (values: AnnotationForm) => {
    if (!currentRecord) return;
    setSubmitting(true);
    try {
      await annotationApi.annotate(currentRecord.id, {
        intent: values.intent,
        emotion: values.emotion,
        quality_score: values.quality_score,
        tags: values.tags,
        notes: values.notes,
      });
      message.success("标注成功");
      setDrawerOpen(false);
      fetchData();
    } catch (err) {
      message.error("标注失败");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const columns: ProColumns<PendingAnnotationItem>[] = [
    {
      title: "ID",
      dataIndex: "id",
      width: 60,
    },
    {
      title: "内容",
      dataIndex: "cleaned_content",
      ellipsis: true,
    },
    {
      title: "质量分",
      dataIndex: "quality_score",
      width: 100,
      align: "center",
      render: (_, record) =>
        record.quality_score !== null ? (
          <Tag color={record.quality_score >= 70 ? "success" : "warning"}>
            {record.quality_score}
          </Tag>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      width: 180,
      render: (val) => new Date(String(val)).toLocaleString(),
    },
    {
      title: "操作",
      width: 100,
      fixed: "right",
      render: (_, record) => (
        <Button
          type="primary"
          size="small"
          icon={<EditOutlined />}
          onClick={() => handleAnnotate(record)}
        >
          标注
        </Button>
      ),
    },
  ];

  // 意图分布 Top 5
  const intentEntries = stats?.intent_distribution
    ? Object.entries(stats.intent_distribution).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>
        数据标注
      </h1>

      {/* 统计卡片 */}
      {stats && (
        <StatisticCard.Group
          direction="row"
          gutter={[16, 16]}
          style={{ marginBottom: 24 }}
        >
          <StatisticCard
            statistic={{
              title: "总记录",
              value: stats.total_records,
            }}
            style={{ flex: 1 }}
          />
          <StatisticCard
            statistic={{
              title: "已标注",
              value: stats.annotated_count,
            }}
            style={{ flex: 1 }}
          />
          <StatisticCard
            statistic={{
              title: "待标注",
              value: stats.pending_count,
            }}
            style={{ flex: 1 }}
          />
          <StatisticCard
            statistic={{
              title: "完成率",
              value: `${(stats.annotation_rate * 100).toFixed(1)}%`,
            }}
            style={{ flex: 1 }}
          />
        </StatisticCard.Group>
      )}

      {/* 意图分布 + 情绪分布 */}
      {stats && (
        <ProCard gutter={[16, 16]} wrap style={{ marginBottom: 24 }}>
          <ProCard
            title="意图分布 Top 5"
            bordered
            style={{ flex: 1, minWidth: 280 }}
          >
            <Space direction="vertical" style={{ width: "100%" }}>
              {intentEntries.slice(0, 5).map(([intent, count]) => (
                <div
                  key={intent}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Tag>{intent}</Tag>
                  <Text strong>{count}</Text>
                </div>
              ))}
              {intentEntries.length === 0 && (
                <Text type="secondary">暂无数据</Text>
              )}
            </Space>
          </ProCard>
          <ProCard title="情绪分布" bordered style={{ flex: 1, minWidth: 280 }}>
            <Space direction="vertical" style={{ width: "100%" }}>
              {stats.emotion_distribution &&
                Object.entries(stats.emotion_distribution).map(
                  ([emotion, count]) => {
                    const colorMap: Record<string, string> = {
                      positive: "#52c41a",
                      neutral: "#8c8c8c",
                      negative: "#f5222d",
                    };
                    return (
                      <div
                        key={emotion}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <Tag color={colorMap[emotion] || "default"}>
                          {emotion}
                        </Tag>
                        <Text strong>{count}</Text>
                      </div>
                    );
                  },
                )}
              {(!stats.emotion_distribution ||
                Object.keys(stats.emotion_distribution).length === 0) && (
                <Text type="secondary">暂无数据</Text>
              )}
            </Space>
          </ProCard>
        </ProCard>
      )}

      {/* 待标注列表 */}
      <Spin spinning={loading}>
        <ProTable<PendingAnnotationItem>
          headerTitle="待标注数据"
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{
            total,
            pageSize: 10,
            showSizeChanger: false,
            onChange: (page) => fetchData(page),
          }}
          search={false}
          locale={{ emptyText: "暂无待标注数据" }}
        />
      </Spin>

      {/* 标注 Drawer */}
      <Drawer
        title={`标注记录 #${currentRecord?.id}`}
        width={480}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        {currentRecord && (
          <div style={{ marginBottom: 24 }}>
            <Text type="secondary">清洗内容:</Text>
            <div
              style={{
                marginTop: 8,
                padding: 12,
                background: "var(--ant-color-bg-container-secondary, #f5f5f5)",
                borderRadius: 6,
                fontSize: 13,
                lineHeight: 1.6,
              }}
            >
              {currentRecord.cleaned_content}
            </div>
          </div>
        )}
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ quality_score: 3, tags: [] }}
        >
          <Form.Item
            name="intent"
            label="意图"
            rules={[{ required: true, message: "请选择意图" }]}
          >
            <Select placeholder="选择意图">
              {INTENT_OPTIONS.map((opt) => (
                <Select.Option key={opt} value={opt}>
                  {opt}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="emotion"
            label="情绪"
            rules={[{ required: true, message: "请选择情绪" }]}
          >
            <Select placeholder="选择情绪">
              {EMOTION_OPTIONS.map((opt) => (
                <Select.Option key={opt.value} value={opt.value}>
                  {opt.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="quality_score"
            label="质量评分"
            rules={[{ required: true, message: "请评分" }]}
          >
            <Rate count={5} />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select
              mode="tags"
              placeholder="输入标签后回车"
              tokenSeparators={[","]}
            />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={3} placeholder="标注备注..." />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={submitting}
              block
            >
              保存标注
            </Button>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
