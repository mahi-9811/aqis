FROM node:20-alpine AS build

WORKDIR /app

COPY apps/web/package.json package.json
COPY apps/web/index.html index.html
COPY apps/web/vite.config.js vite.config.js
COPY apps/web/vitest.config.js vitest.config.js
COPY apps/web/eslint.config.js eslint.config.js
COPY apps/web/src src

RUN npm install
RUN npm run build

FROM nginx:1.27-alpine

COPY deployment/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
