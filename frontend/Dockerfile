# ArthSaathi web — React + Vite
#
# Two targets:
#   --target dev      Vite dev server with hot reload (docker-compose.dev.yml)
#   --target runtime  static build served by nginx, /api proxied to the API
#
# Build context is the REPO ROOT:
#   docker build -f frontend/Dockerfile --target runtime -t arthsaathi-web .

# ---------- stage 1: node_modules ---------------------------------------
FROM node:22-alpine AS deps
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# ---------- dev: Vite dev server (source is bind-mounted over this) -----
FROM node:22-alpine AS dev
WORKDIR /app/frontend
ENV NODE_ENV=development
COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend/ ./
EXPOSE 5173
# --host binds 0.0.0.0 so the port is reachable from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# ---------- stage 2: production bundle -----------------------------------
FROM node:22-alpine AS build
WORKDIR /app/frontend
COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend/ ./
RUN npm run build

# ---------- stage 3: nginx runtime ---------------------------------------
FROM nginx:1.27-alpine AS runtime
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
EXPOSE 5173
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
  CMD wget -qO- http://127.0.0.1:5173/ >/dev/null || exit 1
