import { useEffect, useState } from "react";
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Form,
  Modal,
  message,
  Tag,
  Pagination,
  Space,
} from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { listScripts, createScript, deleteScript } from "../services/sales";

const { Option } = Select;

export default function ScriptLibrary() {
  const [data, setData] = useState({
    data: [],
    total: 0,
    page: 1,
    page_size: 20,
  });
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [query, setQuery] = useState("");

  const load = async (page = 1) => {
    setLoading(true);
    try {
      const res = await listScripts({
        q: query || undefined,
        page,
        page_size: 10,
      });
      setData(res);
    } catch {
      message.error("加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1);
  }, []);

  const handleCreate = async () => {
    const values = form.getFieldsValue();
    try {
      await createScript(values);
      message.success("话术录入成功，已同步到数据中心");
      setModalOpen(false);
      form.resetFields();
      load(1);
    } catch {
      message.error("创建失败");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteScript(id);
      message.success("已删除");
      load(data.page);
    } catch {
      message.error("删除失败");
    }
  };

  const columns = [
    { title: "标题", dataIndex: "title", key: "title" },
    { title: "分类", dataIndex: "category", key: "category" },
    {
      title: "标签",
      dataIndex: "tags",
      key: "tags",
      render: (tags: string[]) => tags?.map((t) => <Tag key={t}>{t}</Tag>),
    },
    { title: "场景", dataIndex: "scenario", key: "scenario" },
    {
      title: "转化率",
      dataIndex: "conversion_rate",
      key: "conversion_rate",
      render: (v: number) => `${Math.round(v * 100)}%`,
    },
    { title: "使用次数", dataIndex: "usage_count", key: "usage_count" },
    {
      title: "操作",
      key: "action",
      render: (_: any, record: any) => (
        <Button
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => handleDelete(record.id)}
        >
          删除
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h2>话术库管理</h2>
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input.Search
            placeholder="搜索话术"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={() => load(1)}
            style={{ width: 300 }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          >
            录入新话术
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

      <Modal
        title="录入新话术"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input placeholder="话术标题" />
          </Form.Item>
          <Form.Item
            name="content"
            label="话术内容"
            rules={[{ required: true }]}
          >
            <Input.TextArea rows={4} placeholder="完整话术内容" />
          </Form.Item>
          <Form.Item name="category" label="分类" initialValue="general">
            <Select>
              <Option value="general">通用</Option>
              <Option value="promotion">促销</Option>
              <Option value="objection">异议处理</Option>
              <Option value="closing">成交促成</Option>
            </Select>
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入标签后回车" />
          </Form.Item>
          <Form.Item name="scenario" label="适用场景">
            <Input placeholder="如：电话销售、微信私聊" />
          </Form.Item>
          <Form.Item name="conversion_rate" label="历史转化率" initialValue={0}>
            <Input type="number" max={1} min={0} step={0.01} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
