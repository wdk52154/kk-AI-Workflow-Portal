import { useEffect, useState } from "react";
import {
  Card,
  Input,
  Select,
  Tag,
  Button,
  Table,
  Pagination,
  Space,
  message,
} from "antd";
import { SearchOutlined, DownloadOutlined } from "@ant-design/icons";
import type { Asset, AssetSearchResponse } from "../services/asset";
import { fetchAssets } from "../services/asset";

const { Option } = Select;

export default function AssetLibrary() {
  const [query, setQuery] = useState("");
  const [assetType, setAssetType] = useState<string | undefined>(undefined);
  const [data, setData] = useState<AssetSearchResponse>({
    data: [],
    total: 0,
    page: 1,
    page_size: 12,
  });
  const [loading, setLoading] = useState(false);

  const load = async (page = 1) => {
    setLoading(true);
    try {
      const res = await fetchAssets({
        q: query || undefined,
        asset_type: assetType,
        page,
        page_size: 12,
      });
      setData(res);
    } catch (e) {
      message.error("加载素材失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1);
  }, []);

  const columns = [
    { title: "名称", dataIndex: "name", key: "name" },
    { title: "类型", dataIndex: "asset_type", key: "type" },
    { title: "分类", dataIndex: "category", key: "category" },
    {
      title: "标签",
      dataIndex: "tags",
      key: "tags",
      render: (tags: string[]) =>
        tags?.map((t) => <Tag key={t}>{t}</Tag>) || null,
    },
    { title: "状态", dataIndex: "status", key: "status" },
    {
      title: "操作",
      key: "action",
      render: (_: any, record: Asset) => (
        <Space>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => {
              window.open(`/v1/assets/${record.id}/download`, "_blank");
            }}
          >
            下载
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2>素材库</h2>
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input.Search
            placeholder="搜索素材名称、描述、标签"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={() => load(1)}
            style={{ width: 300 }}
            enterButton={<SearchOutlined />}
          />
          <Select
            placeholder="素材类型"
            allowClear
            style={{ width: 150 }}
            value={assetType}
            onChange={setAssetType}
          >
            <Option value="image">图片</Option>
            <Option value="video">视频</Option>
            <Option value="poster">海报模板</Option>
          </Select>
          <Button type="primary" onClick={() => load(1)}>
            搜索
          </Button>
        </Space>
      </Card>

      <Table
        loading={loading}
        dataSource={data.data}
        columns={columns}
        rowKey="id"
        pagination={false}
      />
      <div style={{ marginTop: 16, textAlign: "right" }}>
        <Pagination
          current={data.page}
          pageSize={data.page_size}
          total={data.total}
          onChange={(p) => load(p)}
        />
      </div>
    </div>
  );
}
