FROM node:22-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
COPY src ./src

# Test stage: `docker build --target test ./backend` runs the node:test suite
FROM base AS test
COPY test ./test
RUN npm test

FROM base AS runtime
ENV NODE_ENV=production PORT=__API_PORT__
USER node
EXPOSE __API_PORT__
CMD ["node", "src/server.js"]
