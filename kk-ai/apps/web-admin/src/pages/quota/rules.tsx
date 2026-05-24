import { useState, useRef, useCallback } from "react";
import { ProTable } from "@ant-design/pro-components";
import {
  Button,
  Modal,
  Form,
  InputNumber,
  Select,
  Slider,
  Popconfirm,
  Tag,
  message,
  Tooltip,
  Space,
} from "antd";
import type { ProColumns, ActionType } from "@ant-design/pro-components";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import {
  quotaApi,
  type QuotaRule,
  type QuotaRuleCreate,
} from "../../services/quota";

interface FormValues {
  project_name: string;
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number;
}

export default function QuotaRulesPage() {
  const [modalVisible, setModalVisible] = useState(false);
  const [modalTitle, setModalTitle] = useState("新建配额规则");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm<FormValues>();
  const [submitting, setSubmitting] = useState(false);
  const [projects, setProjects] = useState<string[]>([]);
  const actionRef = useRef<ActionType>();

  const fetchProjects = useCallback(async () => {
    try {
      const res = await quotaApi.getProjects();
      setProjects(res.items);
    } catch {
      setProjects(["project-a", "project-b", "project-c", "kk-ai-platform"]);
    }
  }, []);

  const handleOpenCreate = () => {
    setEditingId(null);
    setModalTitle("新建配额规则");
    form.resetFields();
    form.setFieldsValue({ alert_threshold: 80 });
    fetchProjects();
    setModalVisible(true);
  };

  const handleOpenEdit = (record: QuotaRule) => {
    setEditingId(record.id);
    setModalTitle("编辑配额规则");
    form.setFieldsValue({
      project_name: record.project_name,
      daily_limit: record.daily_limit,
      monthly_limit: record.monthly_limit,
      alert_threshold: record.alert_threshold,
    });
    fetchProjects();
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    setSubmitting(true);

    try {
      if (editingId) {
        await quotaApi.updateRule(editingId, {
          daily_limit: values.daily_limit,
          monthly_limit: values.monthly_limit,
          alert_threshold: values.alert_threshold,
        });
        message.success("更新成功");
      } else {
        const data: QuotaRuleCreate = {
          project_name: values.project_name,
          daily_limit: values.daily_limit,
          monthly_limit: values.monthly_limit,
          alert_threshold: values.alert_threshold,
        };
        await quotaApi.createRule(data);
        message.success("创建成功");
      }
      setModalVisible(false);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "操作失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await quotaApi.deleteRule(id);
      message.success("删除成功");
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "删除失败");
    }
  };

  const columns: ProColumns<QuotaRule>[] = [
    {
      title: "项目名称",
      dataIndex: "project_name",
      search: true,
    },
    {
      title: "日限额",
      dataIndex: "daily_limit",
      align: "right",
      render: (_, record) => record.daily_limit.toLocaleString(),
    },
    {
      title: "月限额",
      dataIndex: "monthly_limit",
      align: "right",
      render: (_, record) => record.monthly_limit.toLocaleString(),
    },
    {
      title: "告警阈值",
      dataIndex: "alert_threshold",
      align: "right",
      render: (_, record) => `${record.alert_threshold}%`,
    },
    {
      title: "状态",
      dataIndex: "status",
      align: "center",
      filters: [
        { text: "生效", value: "active" },
        { text: "已删除", value: "deleted" },
      ],
      render: (_, record) => (
        <Tag color={record.status === "active" ? "success" : "default"}>
          {record.status === "active" ? "生效" : "已删除"}
        </Tag>
      ),
    },
    {
      title: "操作",
      align: "center",
      width: 120,
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleOpenEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除？"
            description={`删除项目 ${record.project_name} 的配额规则后，该项目将不再受配额限制。`}
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>
        配额规则配置
      </h1>

      <ProTable<QuotaRule>
        headerTitle="配额规则列表"
        actionRef={actionRef}
        columns={columns}
        rowKey="id"
        search={{ labelWidth: "auto" }}
        pagination={{ pageSize: 10 }}
        toolBarRender={() => [
          <Button
            key="create"
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleOpenCreate}
          >
            新建规则
          </Button>,
        ]}
        request={async (params) => {
          const res = await quotaApi.getRules({
            project_name: params.project_name as string,
            status: params.status as string,
            page: params.current,
            page_size: params.pageSize,
          });
          return {
            data: res.items,
            success: true,
            total: res.total,
          };
        }}
        locale={{ emptyText: "暂无配额规则" }}
      />

      <Modal
        title={modalTitle}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        width={560}
        destroyOnClose
      >
        <Form
          form={form}
          layout="horizontal"
          labelCol={{ span: 6 }}
          wrapperCol={{ span: 16 }}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="project_name"
            label="项目名称"
            rules={[{ required: true, message: "请选择项目名称" }]}
          >
            <Select
              placeholder="请选择项目"
              options={projects.map((p) => ({ label: p, value: p }))}
              disabled={editingId !== null}
            />
          </Form.Item>

          <Form.Item
            name="daily_limit"
            label="日限额"
            rules={[{ required: true, message: "请输入日限额" }]}
          >
            <InputNumber
              min={1}
              style={{ width: "100%" }}
              placeholder="每日调用次数上限"
              addonAfter="次/天"
            />
          </Form.Item>

          <Form.Item
            name="monthly_limit"
            label="月限额"
            rules={[
              { required: true, message: "请输入月限额" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || value >= getFieldValue("daily_limit")) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("月限额不能小于日限额"));
                },
              }),
            ]}
          >
            <InputNumber
              min={1}
              style={{ width: "100%" }}
              placeholder="每月调用次数上限"
              addonAfter="次/月"
            />
          </Form.Item>

          <Form.Item
            name="alert_threshold"
            label="告警阈值"
            rules={[{ required: true }]}
          >
            <Slider
              min={1}
              max={100}
              step={1}
              marks={{ 1: "1%", 50: "50%", 100: "100%" }}
              tooltip={{ formatter: (v) => `${v}%` }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
