FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* /app/
ENV NODE_ENV=development
RUN npm install

COPY frontend/index.html frontend/tsconfig.json frontend/vite.config.ts /app/
COPY frontend/src /app/src

CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3001"]
