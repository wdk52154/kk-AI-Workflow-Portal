import { useState } from "react";
import { Card, Input, List, Tag, message, Alert, Spin } from "antd";
import { SendOutlined } from "@ant-design/icons";
import { querySales } from "../services/sales";

export default function ScriptAssistant() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await querySales(question);
      setResult(res);
    } catch {
      message.error("查询失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>销售话术助手</h2>
      <Card>
        <Input.Search
          placeholder="输入客户问题，AI 推荐应答话术..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onSearch={handleQuery}
          enterButton={<SendOutlined />}
          loading={loading}
          size="large"
        />
      </Card>

      {loading && (
        <div style={{ textAlign: "center", padding: 40 }}>
          <Spin size="large" />
        </div>
      )}

      {result && (
        <Card title="推荐话术" style={{ marginTop: 16 }}>
          {result.objection_handler && (
            <Alert
              message={result.objection_handler}
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          {result.user_facts?.length > 0 && (
            <Alert
              message={`用户画像：${result.user_facts.join("；")}`}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          <List
            dataSource={result.recommended_scripts}
            renderItem={(item: any) => (
              <List.Item>
                <List.Item.Meta
                  title={item.title}
                  description={
                    <>
                      <p>{item.content}</p>
                      <div>
                        <Tag>{item.category}</Tag>
                        <Tag>
                          转化率 {Math.round(item.conversion_rate * 100)}%
                        </Tag>
                      </div>
                    </>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
}
