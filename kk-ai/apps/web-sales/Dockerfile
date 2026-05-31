FROM node:20-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm@9

COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY .npmrc ./

COPY packages/ ./packages/
COPY apps/web-sales/package.json ./apps/web-sales/

RUN pnpm install --frozen-lockfile

COPY apps/web-sales/ ./apps/web-sales/

RUN pnpm run build

FROM nginx:alpine

COPY --from=builder /app/apps/web-sales/dist /usr/share/nginx/html
COPY apps/web-sales/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
