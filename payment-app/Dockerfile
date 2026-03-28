# Build SPA + run Express (API + static) on one port for Docker
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev && npm install tsx@4.21.0 --no-save
COPY --from=builder /app/dist ./dist
COPY server ./server
COPY shared ./shared
EXPOSE 8080
ENV PORT=8080
CMD ["./node_modules/.bin/tsx", "server/index.ts"]
