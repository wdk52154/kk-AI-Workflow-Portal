import { useEffect, useState } from "react";
import { Card, Statistic, Row, Col, Table, Tag } from "antd";
import {
  FileImageOutlined,
  FileTextOutlined,
  SyncOutlined,
  RiseOutlined,
} from "@ant-design/icons";
import type { AssetStats } from "../services/asset";
import { fetchAssetStats, fetchAssets } from "../services/asset";

export default function Dashboard() {
  const [stats, setStats] = useState<AssetStats | null>(null);
  const [topAssets, setTopAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchAssetStats(), fetchAssets({ page_size: 5 })])
      .then(([s, list]) => {
        setStats(s);
        setTopAssets(list.data || []);
      })
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: "素材名称", dataIndex: "name", key: "name" },
    {
      title: "类型",
      dataIndex: "asset_type",
      key: "type",
      render: (t: string) => <Tag>{t}</Tag>,
    },
    { title: "下载次数", dataIndex: "download_count", key: "downloads" },
    { title: "复用次数", dataIndex: "reuse_count", key: "reuse" },
  ];

  return (
    <div>
      <h2>运营看板</h2>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="素材总量"
              value={stats?.total_count || 0}
              prefix={<FileImageOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="图片素材"
              value={stats?.by_type?.image || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="视频素材"
              value={stats?.by_type?.video || 0}
              prefix={<SyncOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="平均复用率"
              value={stats?.reuse_rate || 0}
              suffix="%"
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="热门素材排行" loading={loading}>
        <Table
          dataSource={topAssets}
          columns={columns}
          rowKey="id"
          pagination={false}
        />
      </Card>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="按分类分布" loading={loading}>
            {stats?.by_category &&
              Object.entries(stats.by_category).map(([k, v]) => (
                <p key={k}>
                  {k}: {v}
                </p>
              ))}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="按状态分布" loading={loading}>
            {stats?.by_status &&
              Object.entries(stats.by_status).map(([k, v]) => (
                <p key={k}>
                  {k}: {v}
                </p>
              ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
