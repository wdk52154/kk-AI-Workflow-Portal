import { useState, useEffect, useCallback } from "react";
import { ProTable } from "@ant-design/pro-components";
import {
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Slider,
  Switch,
  Tag,
  Space,
  message,
  Popconfirm,
  Typography,
} from "antd";
import type { ProColumns } from "@ant-design/pro-components";
import { PlusOutlined, CopyOutlined, DeleteOutlined } from "@ant-design/icons";
import {
  apiKeyApi,
  type ApiKeyItem,
  type ApiKeyCreateRequest,
} from "../../services/apiKey";

const { Text } = Typography;

interface ApiKeyForm {
  project_name: string;
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number;
}

export default function ApiKeysPage() {
  const [data, setData] = useState<ApiKeyItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [form] = Form.useForm<ApiKeyForm>();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiKeyApi.getList({ page: 1, page_size: 100 });
      setData(res.items);
      setTotal(res.total);
    } catch (err) {
      message.error("加载 API Key 列表失败");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async (values: ApiKeyForm) => {
    setSubmitting(true);
    try {
      const res = await apiKeyApi.create(values as ApiKeyCreateRequest);
      message.success("API Key 创建成功");
      setNewKey(res.api_key);
      setModalOpen(false);
      form.resetFields();
      fetchData();
    } catch (err) {
      message.error("创建失败");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (record: ApiKeyItem) => {
    try {
      const newStatus = record.status === "active" ? "disabled" : "active";
      await apiKeyApi.update(record.id, { status: newStatus });
      message.success(`已${newStatus === "active" ? "启用" : "禁用"}`);
      fetchData();
    } catch (err) {
      message.error("操作失败");
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiKeyApi.delete(id);
      message.success("删除成功");
      fetchData();
    } catch (err) {
      message.error("删除失败");
      console.error(err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(
      () => message.success("已复制到剪贴板"),
      () => message.error("复制失败"),
    );
  };

  const maskKey = (key: string) => {
    if (key.length <= 12) return key;
    return `${key.slice(0, 8)}...${key.slice(-4)}`;
  };

  const columns: ProColumns<ApiKeyItem>[] = [
    {
      title: "Key ID",
      dataIndex: "id",
      width: 120,
      ellipsis: true,
    },
    {
      title: "项目名称",
      dataIndex: "project_name",
      width: 150,
      search: true,
    },
    {
      title: "API Key",
      dataIndex: "key_prefix",
      width: 200,
      render: (_, record) => (
        <Space>
          <Text code copyable={{ text: record.key_prefix }}>
            {maskKey(record.key_prefix)}
          </Text>
          <Button
            size="small"
            type="text"
            icon={<CopyOutlined />}
            onClick={() => copyToClipboard(record.key_prefix)}
          />
        </Space>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 100,
      align: "center",
      render: (_, record) => (
        <Switch
          checked={record.status === "active"}
          onChange={() => handleToggleStatus(record)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: "日配额",
      dataIndex: "daily_limit",
      width: 100,
      align: "right",
      render: (val) => Number(val).toLocaleString(),
    },
    {
      title: "月配额",
      dataIndex: "monthly_limit",
      width: 100,
      align: "right",
      render: (val) => Number(val).toLocaleString(),
    },
    {
      title: "预警阈值",
      dataIndex: "alert_threshold",
      width: 100,
      align: "center",
      render: (val) => <Tag color="blue">{val}%</Tag>,
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
        <Popconfirm
          title="确认删除此 API Key？"
          onConfirm={() => handleDelete(record.id)}
        >
          <Button size="small" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>
        API Key 管理
      </h1>

      <ProTable<ApiKeyItem>
        headerTitle="项目级 API Key"
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10, total }}
        search={{ labelWidth: "auto" }}
        toolBarRender={() => [
          <Button
            key="add"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setNewKey(null);
              form.resetFields();
              setModalOpen(true);
            }}
          >
            新增 API Key
          </Button>,
        ]}
        locale={{ emptyText: "暂无 API Key" }}
      />

      {/* 新增 Modal */}
      <Modal
        title="新增 API Key"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
        width={520}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{
            daily_limit: 10000,
            monthly_limit: 300000,
            alert_threshold: 80,
          }}
        >
          <Form.Item
            name="project_name"
            label="项目名称"
            rules={[{ required: true, message: "请输入项目名称" }]}
          >
            <Input placeholder="如: proj_001" />
          </Form.Item>
          <Form.Item
            name="daily_limit"
            label="日配额"
            rules={[{ required: true }]}
          >
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              step={1000}
              formatter={(v) => `${Number(v).toLocaleString()}`}
            />
          </Form.Item>
          <Form.Item
            name="monthly_limit"
            label="月配额"
            rules={[{ required: true }]}
          >
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              step={10000}
              formatter={(v) => `${Number(v).toLocaleString()}`}
            />
          </Form.Item>
          <Form.Item
            name="alert_threshold"
            label="预警阈值"
            rules={[{ required: true }]}
          >
            <Slider
              min={0}
              max={100}
              marks={{ 0: "0%", 50: "50%", 100: "100%" }}
            />
          </Form.Item>
        </Form>

        {newKey && (
          <div
            style={{
              marginTop: 16,
              padding: 12,
              background: "#f6ffed",
              border: "1px solid #b7eb8f",
              borderRadius: 6,
            }}
          >
            <Text strong style={{ color: "#52c41a" }}>
              创建成功！请妥善保存 API Key:
            </Text>
            <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <Input value={newKey} readOnly />
              <Button
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard(newKey)}
              >
                复制
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
