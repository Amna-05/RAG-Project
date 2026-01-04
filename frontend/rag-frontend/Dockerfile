# Multi-stage build for Next.js frontend
# Stage 1: Dependencies
FROM node:18-alpine as deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

# Stage 2: Builder
FROM node:18-alpine as builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

COPY src ./src
COPY public ./public
COPY next.config.js .
COPY tsconfig.json .
COPY tailwind.config.ts .
COPY postcss.config.js .

RUN npm run build

# Stage 3: Runtime
FROM node:18-alpine as runner

WORKDIR /app

ENV NODE_ENV production

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME localhost

# Start Next.js server
CMD ["node", "server.js"]
