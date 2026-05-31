import { useState, useRef, useEffect } from "react";
import { Card, Input, Button, List, Tag, message, Spin, Space } from "antd";
import {
  AudioOutlined,
  SendOutlined,
  CustomerServiceOutlined,
} from "@ant-design/icons";

interface Message {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  media_urls?: string[];
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "您好！我是康康 AI 客服，请问有什么可以帮您？",
      intent: "chat",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const send = async () => {
    if (!input.trim()) return;
    const text = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await fetch("/v1/voice/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          user_id: "user-web-001",
          session_id: sessionId,
          platform: "web",
        }),
      });
      const data = await res.json();
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.text_reply,
          intent: data.intent,
          media_urls: data.media_urls,
        },
      ]);
    } catch {
      message.error("发送失败");
    } finally {
      setLoading(false);
    }
  };

  const intentColors: Record<string, string> = {
    order: "red",
    consult: "blue",
    complaint: "orange",
    chat: "default",
    transfer: "purple",
  };

  return (
    <div
      style={{
        maxWidth: 800,
        margin: "0 auto",
        padding: 16,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <h2 style={{ textAlign: "center" }}>
        <CustomerServiceOutlined /> AI 语音客服
      </h2>

      <Card
        style={{
          flex: 1,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          ref={listRef}
          style={{ flex: 1, overflowY: "auto", paddingBottom: 16 }}
        >
          <List
            dataSource={messages}
            renderItem={(m) => (
              <List.Item
                style={{
                  justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    maxWidth: "70%",
                    padding: "8px 12px",
                    borderRadius: 12,
                    background: m.role === "user" ? "#1677ff" : "#f5f5f5",
                    color: m.role === "user" ? "#fff" : "#333",
                  }}
                >
                  <div>{m.content}</div>
                  {m.intent && (
                    <Tag
                      color={intentColors[m.intent] || "default"}
                      style={{ marginTop: 4, fontSize: 11 }}
                    >
                      意图: {m.intent}
                    </Tag>
                  )}
                  {m.media_urls?.map((url, i) => (
                    <img
                      key={i}
                      src={url}
                      alt=""
                      style={{ maxWidth: 200, marginTop: 8, borderRadius: 8 }}
                    />
                  ))}
                </div>
              </List.Item>
            )}
          />
          {loading && (
            <div style={{ textAlign: "center", padding: 12 }}>
              <Spin />
            </div>
          )}
        </div>

        <Space.Compact style={{ marginTop: 16 }}>
          <Button
            type={isRecording ? "primary" : "default"}
            danger={isRecording}
            icon={<AudioOutlined />}
            onClick={() => {
              setIsRecording(!isRecording);
              message.info(isRecording ? "已停止录音" : "开始录音（模拟）");
            }}
          >
            {isRecording ? "录音中" : "语音"}
          </Button>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            onPressEnter={send}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={send}
            loading={loading}
          >
            发送
          </Button>
        </Space.Compact>
      </Card>

      <div
        style={{
          textAlign: "center",
          marginTop: 8,
          color: "#999",
          fontSize: 12,
        }}
      >
        支持文字/语音对话 · 实时意图识别 · 多模态回复
      </div>
    </div>
  );
}
