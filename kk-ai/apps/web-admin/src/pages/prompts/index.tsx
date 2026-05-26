import { useState, useEffect, useCallback } from "react";
import { ProTable } from "@ant-design/pro-components";
import {
  Button,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  Space,
  message,
  Popconfirm,
  Typography,
  Divider,
} from "antd";
import type { ProColumns } from "@ant-design/pro-components";
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";
import {
  promptApi,
  type PromptListItem,
  type PromptDetail,
  type RenderPromptResponse,
} from "../../services/prompt";

const { TextArea } = Input;
const { Text } = Typography;

const CATEGORY_OPTIONS = [
  "system",
  "user",
  "assistant",
  "tool",
  "rag",
  "sales",
  "voice",
];

interface PromptForm {
  id: string;
  name: string;
  category: string;
  template: string;
  description: string;
}

export default function PromptsPage() {
  const [data, setData] = useState<PromptListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [previewPrompt, setPreviewPrompt] = useState<PromptDetail | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [renderResult, setRenderResult] = useState<RenderPromptResponse | null>(
    null,
  );
  const [renderVars, setRenderVars] = useState<Record<string, string>>({});
  const [rendering, setRendering] = useState(false);
  const [form] = Form.useForm<PromptForm>();
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>();

  const fetchData = useCallback(
    async (_page = 1, _pageSize = 10) => {
      setLoading(true);
      try {
        const res = await promptApi.list(categoryFilter);
        setData(res.items);
        setTotal(res.total);
      } catch (err) {
        message.error("加载 Prompt 列表失败");
        console.error(err);
      } finally {
        setLoading(false);
      }
    },
    [categoryFilter],
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async (values: PromptForm) => {
    setSubmitting(true);
    try {
      await promptApi.register({
        id: values.id,
        name: values.name,
        category: values.category,
        template: values.template,
        description: values.description,
      });
      message.success("Prompt 创建成功");
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

  const handleDelete = async (promptId: string) => {
    try {
      await promptApi.delete(promptId);
      message.success("删除成功");
      fetchData();
    } catch (err) {
      message.error("删除失败");
      console.error(err);
    }
  };

  const openPreview = async (promptId: string) => {
    try {
      const detail = await promptApi.get(promptId);
      setPreviewPrompt(detail);
      setRenderVars({});
      setRenderResult(null);
      setPreviewOpen(true);
    } catch (err) {
      message.error("加载 Prompt 详情失败");
      console.error(err);
    }
  };

  const handleRender = async () => {
    if (!previewPrompt) return;
    setRendering(true);
    try {
      const result = await promptApi.render(previewPrompt.id, renderVars);
      setRenderResult(result);
    } catch (err) {
      message.error("渲染失败");
      console.error(err);
    } finally {
      setRendering(false);
    }
  };

  const columns: ProColumns<PromptListItem>[] = [
    {
      title: "ID",
      dataIndex: "prompt_id",
      width: 120,
      ellipsis: true,
    },
    {
      title: "名称",
      dataIndex: "name",
      width: 150,
    },
    {
      title: "分类",
      dataIndex: "category",
      width: 100,
      filters: CATEGORY_OPTIONS.map((c) => ({ text: c, value: c })),
      onFilter: (value, record) => record.category === value,
      render: (_, record) => <Tag>{record.category}</Tag>,
    },
    {
      title: "版本",
      dataIndex: "version",
      width: 80,
    },
    {
      title: "描述",
      dataIndex: "description",
      ellipsis: true,
    },
    {
      title: "操作",
      width: 160,
      fixed: "right",
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => openPreview(record.prompt_id)}
          >
            预览
          </Button>
          <Popconfirm
            title="确认删除？"
            onConfirm={() => handleDelete(record.prompt_id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>
        Prompt 管理
      </h1>

      <ProTable<PromptListItem>
        headerTitle="Prompt 模板列表"
        columns={columns}
        dataSource={data}
        rowKey="prompt_id"
        loading={loading}
        pagination={{ pageSize: 10, total }}
        search={false}
        toolBarRender={() => [
          <Select
            key="category"
            placeholder="按分类筛选"
            allowClear
            style={{ width: 140 }}
            value={categoryFilter}
            onChange={(val) => setCategoryFilter(val)}
          >
            {CATEGORY_OPTIONS.map((c) => (
              <Select.Option key={c} value={c}>
                {c}
              </Select.Option>
            ))}
          </Select>,
          <Button
            key="add"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              form.resetFields();
              setModalOpen(true);
            }}
          >
            新增 Prompt
          </Button>,
        ]}
        locale={{ emptyText: "暂无 Prompt 模板" }}
      />

      {/* 新增 Prompt Modal */}
      <Modal
        title="新增 Prompt"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ category: "system" }}
        >
          <Form.Item
            name="id"
            label="ID"
            rules={[{ required: true, message: "请输入唯一标识" }]}
          >
            <Input placeholder="如: sales_greeting_v1" />
          </Form.Item>
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: "请输入名称" }]}
          >
            <Input placeholder="如: 销售开场白" />
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true }]}>
            <Select>
              {CATEGORY_OPTIONS.map((c) => (
                <Select.Option key={c} value={c}>
                  {c}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="template"
            label="模板内容 (YAML / Jinja2)"
            rules={[{ required: true, message: "请输入模板内容" }]}
          >
            <TextArea
              rows={8}
              placeholder={`如:\n您好 {{ name }}，\n我是 {{ company }} 的顾问...`}
            />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="Prompt 用途描述" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 预览 Modal */}
      <Modal
        title={`预览: ${previewPrompt?.name || ""}`}
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        width={800}
        footer={null}
      >
        {previewPrompt && (
          <Space direction="vertical" style={{ width: "100%" }} size="large">
            <div>
              <Text strong>模板内容:</Text>
              <pre
                style={{
                  marginTop: 8,
                  padding: 12,
                  background:
                    "var(--ant-color-bg-container-secondary, #f5f5f5)",
                  borderRadius: 6,
                  fontSize: 13,
                  overflow: "auto",
                  maxHeight: 200,
                }}
              >
                {previewPrompt.template}
              </pre>
            </div>

            <Divider style={{ margin: "8px 0" }} />

            <div>
              <Text strong>变量输入:</Text>
              <Space
                direction="vertical"
                style={{ width: "100%", marginTop: 8 }}
              >
                {previewPrompt.variables &&
                previewPrompt.variables.length > 0 ? (
                  previewPrompt.variables.map((v) => (
                    <div
                      key={v.name}
                      style={{ display: "flex", gap: 8, alignItems: "center" }}
                    >
                      <Tag>{v.name}</Tag>
                      <Input
                        placeholder={
                          v.default || v.description || `输入 ${v.name}`
                        }
                        value={renderVars[v.name] || ""}
                        onChange={(e) =>
                          setRenderVars((prev) => ({
                            ...prev,
                            [v.name]: e.target.value,
                          }))
                        }
                        style={{ flex: 1 }}
                      />
                    </div>
                  ))
                ) : (
                  <Text type="secondary">此模板无变量</Text>
                )}
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleRender}
                  loading={rendering}
                  disabled={
                    !previewPrompt.variables ||
                    previewPrompt.variables.length === 0
                  }
                >
                  渲染预览
                </Button>
              </Space>
            </div>

            {renderResult && (
              <div>
                <Text strong>渲染结果:</Text>
                <pre
                  style={{
                    marginTop: 8,
                    padding: 12,
                    background:
                      "var(--ant-color-bg-container-secondary, #f5f5f5)",
                    borderRadius: 6,
                    fontSize: 13,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {renderResult.rendered}
                </pre>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  使用变量: {renderResult.variables_used.join(", ") || "无"}
                </Text>
              </div>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
}
