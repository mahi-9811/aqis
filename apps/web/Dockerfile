# Multi-stage build for React frontend
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first for better caching
COPY apps/web/package*.json ./

# Install all dependencies (including dev for build)
RUN npm ci

# Copy source files
COPY apps/web/index.html .
COPY apps/web/vite.config.js .
COPY apps/web/vitest.config.js .
COPY apps/web/eslint.config.js .
COPY apps/web/src src

# Build the application
RUN npm run build

# Runtime stage with nginx
FROM nginx:1.27-alpine

# Copy nginx configuration
COPY deployment/nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
