import { useEffect, useState } from "react";
import { Card, Statistic, Row, Col, List, Tag } from "antd";
import {
  MessageOutlined,
  TrophyOutlined,
  TeamOutlined,
  RiseOutlined,
} from "@ant-design/icons";
import { listScripts } from "../services/sales";

export default function Dashboard() {
  const [stats, setStats] = useState({ total: 0, recent: [] as any[] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    listScripts({ page_size: 5 })
      .then((res) => setStats({ total: res.total, recent: res.data }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2>销售看板</h2>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="话术总数"
              value={stats.total}
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="今日陪练次数"
              value={0}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic title="活跃销售" value={12} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="平均陪练评分"
              value={82.5}
              suffix="分"
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最新话术" loading={loading}>
        <List
          dataSource={stats.recent}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                title={item.title}
                description={
                  <>
                    <Tag>{item.category}</Tag>
                    {item.tags?.map((t: string) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                  </>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}
