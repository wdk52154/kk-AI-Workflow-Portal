import { useState, useEffect } from "react";
import {
  Card,
  Button,
  Input,
  Table,
  Tag,
  message,
  Space,
  Timeline,
  Progress,
  Badge,
  Modal,
} from "antd";
import {
  VideoCameraOutlined,
  ScissorOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";

interface LiveRecord {
  record_id: string;
  title: string;
  platform: string;
  status: string;
  duration_seconds: number;
}

interface Highlight {
  start_time: number;
  end_time: number;
  highlight_type: string;
  score: number;
  description: string;
}

interface Clip {
  clip_id: string;
  title: string;
  start_time: number;
  end_time: number;
  duration: number;
  status: string;
  enhancements?: string[];
}

export default function App() {
  const [records, setRecords] = useState<LiveRecord[]>([]);
  const [clips, setClips] = useState<Clip[]>([]);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamUrl, setStreamUrl] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    loadRecords();
    loadClips();
  }, []);

  const loadRecords = async () => {
    try {
      const res = await fetch("/v1/live/records");
      setRecords(await res.json());
    } catch {
      /* ignore */
    }
  };

  const loadClips = async () => {
    try {
      const res = await fetch("/v1/live/clips");
      setClips(await res.json());
    } catch {
      /* ignore */
    }
  };

  const startRecord = async () => {
    if (!streamUrl.trim()) {
      message.warning("请输入推流地址");
      return;
    }
    setLoading(true);
    try {
      await fetch("/v1/live/record/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stream_url: streamUrl,
          title: "直播录制",
          platform: "douyin",
        }),
      });
      message.success("录制已开始");
      loadRecords();
    } catch {
      message.error("启动失败");
    } finally {
      setLoading(false);
    }
  };

  const stopRecord = async (rid: string) => {
    setLoading(true);
    try {
      await fetch("/v1/live/record/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ record_id: rid }),
      });
      message.success("录制已停止");
      loadRecords();
    } catch {
      message.error("停止失败");
    } finally {
      setLoading(false);
    }
  };

  const analyze = async (rid: string) => {
    setLoading(true);
    try {
      const res = await fetch("/v1/live/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ record_id: rid }),
      });
      const data = await res.json();
      setHighlights(data.highlights);
      setSelectedRecord(rid);
      setModalOpen(true);
      message.success(`发现 ${data.highlights.length} 个高光时刻`);
    } catch {
      message.error("分析失败");
    } finally {
      setLoading(false);
    }
  };

  const createClip = async (h: Highlight) => {
    setLoading(true);
    try {
      await fetch("/v1/live/clip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          record_id: selectedRecord,
          start_time: h.start_time,
          end_time: h.end_time,
          title: h.description,
        }),
      });
      message.success("切片已生成");
      loadClips();
    } catch {
      message.error("切片失败");
    } finally {
      setLoading(false);
    }
  };

  const enhance = async (cid: string) => {
    setLoading(true);
    try {
      await fetch("/v1/live/clip/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clip_id: cid,
          add_subtitle: true,
          add_bgm: true,
          add_intro: true,
        }),
      });
      message.success("增强完成");
      loadClips();
    } catch {
      message.error("增强失败");
    } finally {
      setLoading(false);
    }
  };

  const typeColors: Record<string, string> = {
    emotion_peak: "red",
    interaction_peak: "blue",
    product_explain: "green",
  };

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 16 }}>
      <h2 style={{ textAlign: "center" }}>
        <VideoCameraOutlined /> 智能直播切片 Agent
      </h2>

      <Card title="直播录制" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            value={streamUrl}
            onChange={(e) => setStreamUrl(e.target.value)}
            placeholder="输入推流地址 (RTMP/HLS)"
            style={{ width: 350 }}
          />
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={startRecord}
            loading={loading}
          >
            开始录制
          </Button>
        </Space>
      </Card>

      <Card title="直播列表" style={{ marginBottom: 16 }}>
        <Table
          dataSource={records}
          rowKey="record_id"
          columns={[
            { title: "标题", dataIndex: "title" },
            { title: "平台", dataIndex: "platform" },
            {
              title: "状态",
              dataIndex: "status",
              render: (v) => (
                <Badge
                  status={v === "recording" ? "processing" : "success"}
                  text={v}
                />
              ),
            },
            {
              title: "时长",
              dataIndex: "duration_seconds",
              render: (v) => `${Math.floor((v || 0) / 60)}分`,
            },
            {
              title: "操作",
              key: "action",
              render: (_: any, r: LiveRecord) => (
                <Space>
                  {r.status === "recording" && (
                    <Button
                      size="small"
                      danger
                      icon={<PauseCircleOutlined />}
                      onClick={() => stopRecord(r.record_id)}
                    >
                      停止
                    </Button>
                  )}
                  {r.status === "stopped" && (
                    <Button
                      size="small"
                      icon={<ThunderboltOutlined />}
                      onClick={() => analyze(r.record_id)}
                    >
                      分析高光
                    </Button>
                  )}
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Card title="切片管理">
        <Table
          dataSource={clips}
          rowKey="clip_id"
          columns={[
            { title: "标题", dataIndex: "title" },
            {
              title: "时长",
              dataIndex: "duration",
              render: (v) => `${v?.toFixed(1)}s`,
            },
            {
              title: "增强",
              dataIndex: "enhancements",
              render: (v) => v?.map((e: string) => <Tag key={e}>{e}</Tag>),
            },
            {
              title: "状态",
              dataIndex: "status",
              render: (v) => (
                <Tag color={v === "enhanced" ? "success" : "default"}>{v}</Tag>
              ),
            },
            {
              title: "操作",
              key: "action",
              render: (_: any, c: Clip) => (
                <Button
                  size="small"
                  icon={<ScissorOutlined />}
                  onClick={() => enhance(c.clip_id)}
                  disabled={c.status === "enhanced"}
                >
                  增强
                </Button>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title="高光时刻分析"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        width={700}
        footer={null}
      >
        <Timeline
          items={highlights.map((h) => ({
            color: typeColors[h.highlight_type] || "blue",
            children: (
              <div>
                <Tag color={typeColors[h.highlight_type]}>
                  {h.highlight_type}
                </Tag>
                <span style={{ fontWeight: "bold" }}>
                  {h.start_time.toFixed(0)}s - {h.end_time.toFixed(0)}s
                </span>
                <Progress
                  percent={Math.round(h.score * 100)}
                  size="small"
                  showInfo={false}
                />
                <p style={{ color: "#666" }}>{h.description}</p>
                <Button
                  size="small"
                  type="primary"
                  onClick={() => createClip(h)}
                >
                  生成切片
                </Button>
              </div>
            ),
          }))}
        />
      </Modal>
    </div>
  );
}
