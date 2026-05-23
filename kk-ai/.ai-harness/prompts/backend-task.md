# 后端任务 Prompt 模板

## Situation

项目使用 FastAPI + Python 3.13，服务位于 `services/{service-name}/`。
中间件链：Auth → RateLimit → Quota → Router → Logger

## Task

{task_description}

## Action

1. 在指定目录创建/修改文件
2. 使用 `redis.asyncio` 进行异步 Redis 操作
3. 配置管理使用 Pydantic Settings（`MCPHUB_` 前缀）
4. 接口响应格式：`{ data: T, error?: { code, message } }`

## Constraint

- [ ] 类型注解覆盖率 > 90%
- [ ] 所有函数必须有 Google docstring
- [ ] 错误处理必须记录 `trace_id`
- [ ] Redis 操作使用 pipeline 减少网络往返
- [ ] 外部服务不可用时降级处理，不阻塞主流程
- [ ] 限流/配额超限后 rollback 已添加的计数

## Verification

```bash
cd services/{service-name}
pytest
mypy app/
python run.py  # 启动验证
curl http://localhost:8000/health  # 健康检查
```
