import { useState } from "react";
import { Upload, Button, Input, Select, Form, message, Card } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd/es/upload/interface";
import { createAsset } from "../services/asset";

const { Dragger } = Upload;
const { Option } = Select;

export default function AssetUpload() {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning("请选择要上传的文件");
      return;
    }
    const values = form.getFieldsValue();
    const file = fileList[0].originFileObj;
    if (!file) return;

    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", values.name || file.name);
    fd.append("description", values.description || "");
    fd.append("asset_type", values.asset_type || "image");
    fd.append("category", values.category || "");
    fd.append("status", "pending");
    if (values.tags) {
      values.tags.forEach((t: string) => fd.append("tags", t));
    }

    try {
      await createAsset(fd);
      message.success("素材上传成功，等待审核");
      setFileList([]);
      form.resetFields();
    } catch (e) {
      message.error("上传失败");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h2>上传素材</h2>
      <Card>
        <Dragger
          fileList={fileList}
          onChange={({ fileList: fl }) => setFileList(fl.slice(-1))}
          beforeUpload={() => false}
          multiple={false}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
          <p className="ant-upload-hint">
            支持图片（jpg/png/webp）、视频（mp4/mov）
          </p>
        </Dragger>

        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item name="name" label="素材名称" rules={[{ required: true }]}>
            <Input placeholder="请输入素材名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="素材描述，便于检索" />
          </Form.Item>
          <Form.Item name="asset_type" label="素材类型" initialValue="image">
            <Select>
              <Option value="image">图片</Option>
              <Option value="video">视频</Option>
              <Option value="poster">海报模板</Option>
            </Select>
          </Form.Item>
          <Form.Item name="category" label="分类">
            <Input placeholder="如：产品图、宣传视频、节日海报" />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入标签后回车" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              onClick={handleUpload}
              loading={uploading}
              disabled={fileList.length === 0}
            >
              提交审核
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
