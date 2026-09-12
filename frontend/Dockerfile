# ArthSaathi web — React + Vite. Self-contained: build context is this
# directory, nothing outside frontend/ is needed.
#
#   cd frontend && docker build --target runtime -t arthsaathi-web .
#   cd frontend && docker compose up --build
#
# Two targets:
#   --target dev      Vite dev server with hot reload
#   --target runtime  static build served by nginx, /api proxied to the API

# ---------- stage 1: node_modules ---------------------------------------
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---------- dev: Vite dev server (source is bind-mounted over this) -----
FROM node:22-alpine AS dev
WORKDIR /app
ENV NODE_ENV=development
COPY --from=deps /app/node_modules ./node_modules
COPY . ./
EXPOSE 5173
# --host binds 0.0.0.0 so the port is reachable from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# ---------- stage 2: production bundle -----------------------------------
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . ./
RUN npm run build

# ---------- stage 3: nginx runtime ---------------------------------------
FROM nginx:1.27-alpine AS runtime

# The upstream is a deploy-time decision, not a build-time one: nginx's own
# entrypoint renders templates/ through envsubst on boot.
#
# LOCAL_RESOLVERS makes that entrypoint read the container's own nameservers
# out of /etc/resolv.conf into NGINX_LOCAL_RESOLVERS — hardcoding Docker's
# 127.0.0.11 would only be right on a user-defined network.
#
# The filter keeps substitution to those two names, so nginx's own $host,
# $remote_addr and friends survive untouched.
ENV API_UPSTREAM=http://api:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1 \
    NGINX_ENVSUBST_FILTER='^(API_|NGINX_LOCAL_RESOLVERS)'

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 5173
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
  CMD wget -qO- http://127.0.0.1:5173/ >/dev/null || exit 1
