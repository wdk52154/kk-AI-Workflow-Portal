import { useState } from "react";
import {
  Card,
  Input,
  Button,
  Form,
  message,
  Space,
  Select,
  ColorPicker,
} from "antd";
import { generatePoster } from "../services/asset";

const { Option } = Select;

export default function PosterEditor() {
  const [form] = Form.useForm();
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleGenerate = async () => {
    const values = form.getFieldsValue();
    if (!values.template_id) {
      message.warning("请选择海报模板");
      return;
    }
    setGenerating(true);
    try {
      const res = await generatePoster(values.template_id, {
        title: values.title || "",
        subtitle: values.subtitle || "",
        brand: values.brand || "",
        bg_color: values.bg_color?.toHexString?.() || "#ffffff",
      });
      setResult(res.url);
      message.success("海报生成成功");
    } catch (e) {
      message.error("生成失败");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div>
      <h2>海报编辑器</h2>
      <Space align="start" style={{ width: "100%" }}>
        <Card title="编辑区" style={{ width: 400 }}>
          <Form form={form} layout="vertical">
            <Form.Item name="template_id" label="模板">
              <Select placeholder="选择海报模板">
                <Option value="tmpl-001">产品促销海报</Option>
                <Option value="tmpl-002">节日活动海报</Option>
                <Option value="tmpl-003">品牌宣传海报</Option>
              </Select>
            </Form.Item>
            <Form.Item name="title" label="主标题">
              <Input placeholder="如：夏季大促，全场5折起" />
            </Form.Item>
            <Form.Item name="subtitle" label="副标题">
              <Input placeholder="如：限时3天，手慢无" />
            </Form.Item>
            <Form.Item name="brand" label="品牌名">
              <Input placeholder="如：康康精选" />
            </Form.Item>
            <Form.Item name="bg_color" label="背景色">
              <ColorPicker defaultValue="#ffffff" showText />
            </Form.Item>
            <Button
              type="primary"
              onClick={handleGenerate}
              loading={generating}
            >
              生成海报
            </Button>
          </Form>
        </Card>

        <Card title="预览区" style={{ flex: 1, minHeight: 400 }}>
          {result ? (
            <div style={{ textAlign: "center" }}>
              <img
                src={result}
                alt="海报预览"
                style={{ maxWidth: "100%", borderRadius: 8 }}
              />
              <p style={{ marginTop: 16, color: "#888" }}>
                海报生成结果（模拟）
              </p>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: 300,
                color: "#ccc",
              }}
            >
              点击左侧「生成海报」预览结果
            </div>
          )}
        </Card>
      </Space>
    </div>
  );
}
