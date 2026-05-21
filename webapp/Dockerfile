FROM node:24-slim

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY index.html tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY src ./src

EXPOSE 5173

CMD ["pnpm", "exec", "vp", "dev", "--host", "0.0.0.0", "--port", "5173"]
