FROM node:20-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm@9

COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY .npmrc ./

COPY packages/ ./packages/
COPY apps/web-asset/package.json ./apps/web-asset/

RUN pnpm install --frozen-lockfile

COPY apps/web-asset/ ./apps/web-asset/

RUN pnpm run build

FROM nginx:alpine

COPY --from=builder /app/apps/web-asset/dist /usr/share/nginx/html
COPY apps/web-asset/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
