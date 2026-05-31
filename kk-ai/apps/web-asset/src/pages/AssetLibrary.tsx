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
  Popconfirm,
} from "antd";
import {
  SearchOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SafetyOutlined,
} from "@ant-design/icons";
import type { Asset, AssetSearchResponse } from "../services/asset";
import {
  fetchAssets,
  precheckAsset,
  approveAsset,
  rejectAsset,
} from "../services/asset";

const { Option } = Select;

const STATUS_COLORS: Record<string, string> = {
  uploaded: "default",
  precheck: "processing",
  pending_review: "warning",
  approved: "success",
  rejected: "error",
};

const STATUS_LABELS: Record<string, string> = {
  uploaded: "已上传",
  precheck: "预检中",
  pending_review: "待审核",
  approved: "已上架",
  rejected: "已拒绝",
};

export default function AssetLibrary() {
  const [query, setQuery] = useState("");
  const [assetType, setAssetType] = useState<string | undefined>(undefined);
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [data, setData] = useState<AssetSearchResponse>({
    items: [],
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
        status: status,
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

  const handleAction = async (
    action: () => Promise<Asset>,
    successMsg: string,
  ) => {
    try {
      await action();
      message.success(successMsg);
      load(data.page);
    } catch (e) {
      message.error("操作失败");
    }
  };

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
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (s: string) => (
        <Tag color={STATUS_COLORS[s] || "default"}>{STATUS_LABELS[s] || s}</Tag>
      ),
    },
    {
      title: "操作",
      key: "action",
      render: (_: any, record: Asset) => (
        <Space>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => {
              window.open(`/v1/assets/${record.asset_id}/download`, "_blank");
            }}
          >
            下载
          </Button>
          {record.status === "uploaded" && (
            <Button
              size="small"
              icon={<SafetyOutlined />}
              onClick={() =>
                handleAction(() => precheckAsset(record.asset_id), "预检完成")
              }
            >
              预检
            </Button>
          )}
          {record.status === "pending_review" && (
            <>
              <Button
                size="small"
                type="primary"
                icon={<CheckCircleOutlined />}
                onClick={() =>
                  handleAction(() => approveAsset(record.asset_id), "审核通过")
                }
              >
                通过
              </Button>
              <Popconfirm
                title="确认拒绝该素材？"
                onConfirm={() =>
                  handleAction(() => rejectAsset(record.asset_id), "已拒绝")
                }
              >
                <Button size="small" danger icon={<CloseCircleOutlined />}>
                  拒绝
                </Button>
              </Popconfirm>
            </>
          )}
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
            <Option value="poster_template">海报模板</Option>
          </Select>
          <Select
            placeholder="审核状态"
            allowClear
            style={{ width: 150 }}
            value={status}
            onChange={setStatus}
          >
            <Option value="uploaded">已上传</Option>
            <Option value="precheck">预检中</Option>
            <Option value="pending_review">待审核</Option>
            <Option value="approved">已上架</Option>
            <Option value="rejected">已拒绝</Option>
          </Select>
          <Button type="primary" onClick={() => load(1)}>
            搜索
          </Button>
        </Space>
      </Card>

      <Table
        loading={loading}
        dataSource={data.items}
        columns={columns}
        rowKey="asset_id"
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
