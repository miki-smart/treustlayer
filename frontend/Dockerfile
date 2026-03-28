# ---- Stage 1: Build ----
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
# Using npm install (not npm ci) because the project uses Bun as its primary
# package manager so package-lock.json may not be fully in sync.
COPY package.json ./
RUN npm install --legacy-peer-deps

# Copy source and build (browser calls same-origin /api/v1; nginx proxies to backend)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
COPY . .
RUN npm run build

# ---- Stage 2: Serve with nginx ----
FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy Vite build output
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
