# TASK-501：素材管理与运营平台

## 元信息

| 字段    | 值                                                       |
| ------- | -------------------------------------------------------- |
| TASK ID | TASK-501                                                 |
| 标题    | 素材管理与运营平台（service-asset + web-asset）          |
| 优先级  | P1                                                       |
| 类型    | fullstack                                                |
| 关联    | service-rag:9002, service-prompt:9004, service-data:9005 |

## 目标

建设多模态素材资产管理平台，支持图片/视频/海报模板的存储、检索、审核、复用追踪。

## 验收标准

### 后端（service-asset, Port 9010）

- [ ] `GET /v1/assets/search?q=xxx&type=image&tags=xxx` - 素材检索（文件名+标签+描述语义搜索）
- [ ] `GET /v1/assets/{id}` - 获取素材详情
- [ ] `POST /v1/assets` - 上传素材（multipart/form-data）
- [ ] `POST /v1/assets/{id}/generate_poster` - 基于模板生成海报
- [ ] `GET /v1/assets/stats` - 素材使用统计
- [ ] 素材审核工作流：uploaded → precheck → pending_review → approved → rejected
- [ ] 复用率追踪：记录调用次数、关联项目

### 前端（apps/web-asset, Port 5174）

- [ ] 素材库网格浏览 + 筛选器（类型/标签/状态）
- [ ] 素材上传：拖拽上传 + 进度条
- [ ] 运营看板：总量/复用率/热门排行
- [ ] 海报生成器：选择模板 + 变量替换

## 技术约束

- 素材存储使用本地文件系统（当前阶段），接口抽象便于后续迁移 OSS
- 素材描述调用 service-rag:9002 向量化
- 海报生成调用 service-prompt:9004 获取模板
- pytest 覆盖率 ≥50%
