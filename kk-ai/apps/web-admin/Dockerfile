FROM node:20-alpine AS builder

WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm@9

# 复制 workspace 配置
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY .npmrc ./

# 复制依赖包
COPY packages/ ./packages/
COPY apps/web-admin/package.json ./apps/web-admin/

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源码
COPY apps/web-admin/ ./apps/web-admin/

# 构建
RUN pnpm run build

# 生产阶段
FROM nginx:alpine

COPY --from=builder /app/apps/web-admin/dist /usr/share/nginx/html
COPY apps/web-admin/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
