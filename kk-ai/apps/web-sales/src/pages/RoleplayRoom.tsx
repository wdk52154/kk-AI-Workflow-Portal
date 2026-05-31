import { useState } from "react";
import {
  Card,
  Button,
  Select,
  Input,
  List,
  Tag,
  Progress,
  message,
  Space,
  Row,
  Col,
} from "antd";
import {
  PlayCircleOutlined,
  SendOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";
import {
  startRoleplay,
  chatRoleplay,
  evaluateRoleplay,
} from "../services/sales";

const { Option } = Select;
const { TextArea } = Input;

export default function RoleplayRoom() {
  const [customerType, setCustomerType] = useState("hesitant");
  const [session, setSession] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [score, setScore] = useState<any>(null);
  const [evalResult, setEvalResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setLoading(true);
    try {
      const res = await startRoleplay(customerType);
      setSession(res);
      setMessages([{ role: "customer", content: res.opening_message }]);
      setEvalResult(null);
      setScore(null);
    } catch {
      message.error("启动陪练失败");
    } finally {
      setLoading(false);
    }
  };

  const send = async () => {
    if (!input.trim() || !session) return;
    const msg = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "sales", content: msg }]);
    setLoading(true);
    try {
      const res = await chatRoleplay(session.session_id, msg);
      setMessages((prev) => [
        ...prev,
        { role: "customer", content: res.customer_reply },
      ]);
      setScore(res.real_time_score);
    } catch {
      message.error("对话失败");
    } finally {
      setLoading(false);
    }
  };

  const evaluate = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await evaluateRoleplay(session.session_id);
      setEvalResult(res);
    } catch {
      message.error("评估失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>AI 陪练室</h2>
      {!session ? (
        <Card title="选择客户类型">
          <Space>
            <Select
              value={customerType}
              onChange={setCustomerType}
              style={{ width: 200 }}
            >
              <Option value="hesitant">犹豫型客户</Option>
              <Option value="price_sensitive">价格敏感型</Option>
              <Option value="clear_need">需求明确型</Option>
            </Select>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={start}
              loading={loading}
            >
              开始陪练
            </Button>
          </Space>
        </Card>
      ) : (
        <Row gutter={16}>
          <Col span={16}>
            <Card
              title={`陪练中 - ${session.customer_profile?.name || ""}`}
              extra={
                <Button
                  icon={<CheckCircleOutlined />}
                  onClick={evaluate}
                  loading={loading}
                >
                  结束并评分
                </Button>
              }
            >
              <List
                dataSource={messages}
                renderItem={(m) => (
                  <List.Item>
                    <Tag color={m.role === "sales" ? "blue" : "orange"}>
                      {m.role === "sales" ? "我" : "客户"}
                    </Tag>
                    <span style={{ marginLeft: 8 }}>{m.content}</span>
                  </List.Item>
                )}
              />
              <Space.Compact style={{ marginTop: 16, width: "100%" }}>
                <TextArea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="输入你的话术..."
                  rows={2}
                  onPressEnter={(e) => {
                    if (!e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
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
          </Col>
          <Col span={8}>
            <Card title="实时评分">
              {score ? (
                <>
                  <p>话术规范度: {score.standardization}分</p>
                  <Progress percent={score.standardization} size="small" />
                  <p>共情能力: {score.empathy}分</p>
                  <Progress percent={score.empathy} size="small" />
                  <p>信息覆盖: {score.information_coverage}分</p>
                  <Progress percent={score.information_coverage} size="small" />
                  <p>转化引导: {score.conversion_guidance}分</p>
                  <Progress percent={score.conversion_guidance} size="small" />
                </>
              ) : (
                <p style={{ color: "#999" }}>开始对话后显示评分</p>
              )}
            </Card>
          </Col>
        </Row>
      )}

      {evalResult && (
        <Card title="综合评估报告" style={{ marginTop: 16 }}>
          <h3>总分: {evalResult.total_score} / 100</h3>
          {Object.entries(evalResult.dimensions).map(([k, v]) => (
            <p key={k}>
              {k}: {v as number}分
            </p>
          ))}
          <h4>改进建议</h4>
          <List
            dataSource={evalResult.suggestions}
            renderItem={(item: string) => <List.Item>• {item}</List.Item>}
          />
        </Card>
      )}
    </div>
  );
}
