import { useState } from "react";
import {
  Card,
  Input,
  Button,
  Select,
  List,
  Tag,
  message,
  Tabs,
  Space,
  Table,
  Badge,
} from "antd";
import {
  EditOutlined,
  ScheduleOutlined,
  BulbOutlined,
} from "@ant-design/icons";
import type { TabsProps } from "antd";

const { Option } = Select;

interface ContentItem {
  id: string;
  platform: string;
  title: string;
  content: string;
  tags: string[];
  status: string;
}

export default function App() {
  const [topic, setTopic] = useState("");
  const [platform, setPlatform] = useState("xiaohongshu");
  const [tone, setTone] = useState("lively");
  const [generated, setGenerated] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [topics, setTopics] = useState<any[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [schedules, setSchedules] = useState<any[]>([]);

  const generate = async () => {
    if (!topic.trim()) {
      message.warning("请输入主题");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/v1/content/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, topic, tone }),
      });
      const data = await res.json();
      setGenerated(data);
      setContents((prev) => [
        {
          id: data.id,
          platform,
          title: data.title,
          content: data.content,
          tags: data.tags,
          status: "draft",
        },
        ...prev,
      ]);
      message.success("生成成功");
    } catch {
      message.error("生成失败");
    } finally {
      setLoading(false);
    }
  };

  const generateTopics = async () => {
    setLoading(true);
    try {
      const res = await fetch("/v1/content/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          industry: "美妆",
          account_positioning: "护肤",
          count: 5,
        }),
      });
      setTopics((await res.json()).topics);
    } catch {
      message.error("选题生成失败");
    } finally {
      setLoading(false);
    }
  };

  const schedule = async () => {
    if (!generated) return;
    try {
      const res = await fetch("/v1/content/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_id: generated.id,
          platform,
          scheduled_at: new Date().toISOString(),
        }),
      });
      const scheduleData = await res.json();
      setSchedules((prev) => [...prev, scheduleData]);
      message.success("已排期");
    } catch {
      message.error("排期失败");
    }
  };

  const platformLabels: Record<string, string> = {
    xiaohongshu: "小红书",
    wechat: "公众号",
    douyin: "抖音",
    moments: "朋友圈",
  };

  const tabItems: TabsProps["items"] = [
    {
      key: "generate",
      label: "内容生成",
      children: (
        <Space direction="vertical" style={{ width: "100%" }}>
          <Card title="AI 内容生成">
            <Space wrap>
              <Input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="输入内容主题"
                style={{ width: 300 }}
              />
              <Select
                value={platform}
                onChange={setPlatform}
                style={{ width: 120 }}
              >
                <Option value="xiaohongshu">小红书</Option>
                <Option value="wechat">公众号</Option>
                <Option value="douyin">抖音</Option>
                <Option value="moments">朋友圈</Option>
              </Select>
              <Select value={tone} onChange={setTone} style={{ width: 120 }}>
                <Option value="lively">活泼</Option>
                <Option value="professional">专业</Option>
                <Option value="premium">高端</Option>
              </Select>
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={generate}
                loading={loading}
              >
                生成
              </Button>
            </Space>
          </Card>

          {generated && (
            <Card
              title={`已生成 - ${platformLabels[generated.platform]}`}
              extra={
                <Space>
                  <Button
                    size="small"
                    onClick={schedule}
                    icon={<ScheduleOutlined />}
                  >
                    排期发布
                  </Button>
                </Space>
              }
            >
              <h4>{generated.title}</h4>
              <pre
                style={{
                  whiteSpace: "pre-wrap",
                  background: "#f5f5f5",
                  padding: 12,
                  borderRadius: 8,
                }}
              >
                {generated.content}
              </pre>
              <Space>
                {generated.tags?.map((t: string) => (
                  <Tag key={t}>#{t}</Tag>
                ))}
              </Space>
            </Card>
          )}
        </Space>
      ),
    },
    {
      key: "topics",
      label: "选题看板",
      children: (
        <Card title="AI 选题推荐">
          <Button
            onClick={generateTopics}
            loading={loading}
            icon={<BulbOutlined />}
          >
            生成选题
          </Button>
          <List
            style={{ marginTop: 16 }}
            dataSource={topics}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button
                    size="small"
                    onClick={() => {
                      setTopic(item.title);
                    }}
                  >
                    采用
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={item.title}
                  description={
                    <>
                      <Tag>{item.category}</Tag>
                      <Tag color="red">热度 {item.trending_score}</Tag>
                      <span style={{ color: "#888" }}>{item.reason}</span>
                    </>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      ),
    },
    {
      key: "library",
      label: "内容库",
      children: (
        <Table
          dataSource={contents}
          rowKey="id"
          columns={[
            { title: "标题", dataIndex: "title" },
            {
              title: "平台",
              dataIndex: "platform",
              render: (v) => platformLabels[v] || v,
            },
            {
              title: "标签",
              dataIndex: "tags",
              render: (v) => v?.map((t: string) => <Tag key={t}>{t}</Tag>),
            },
            {
              title: "状态",
              dataIndex: "status",
              render: (v) => (
                <Badge
                  status={v === "published" ? "success" : "processing"}
                  text={v}
                />
              ),
            },
          ]}
        />
      ),
    },
    {
      key: "schedule",
      label: "发布日历",
      children: (
        <Card title="发布排期">
          <Table
            dataSource={schedules}
            rowKey="id"
            columns={[
              { title: "内容", dataIndex: "title" },
              { title: "平台", dataIndex: "platform" },
              { title: "计划时间", dataIndex: "scheduled_at" },
              { title: "状态", dataIndex: "status" },
            ]}
          />
        </Card>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 16 }}>
      <h2 style={{ textAlign: "center" }}>📱 自媒体运营 Agent</h2>
      <Tabs items={tabItems} />
    </div>
  );
}
