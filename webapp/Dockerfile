FROM node:24-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY src ./src

EXPOSE 5173

CMD ["npx", "vp", "dev", "--host", "0.0.0.0", "--port", "5173"]
