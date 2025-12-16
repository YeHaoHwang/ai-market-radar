# syntax=docker/dockerfile:1

FROM node:20-alpine AS base
WORKDIR /app

# Enable pnpm
RUN corepack enable

# Install dependencies
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY frontend ./
RUN pnpm build

EXPOSE 3000

ENV PORT=3000
# Expect NEXT_PUBLIC_API_BASE to be provided at runtime
# Use explicit host/port flags to avoid CLI interpreting args as directory
CMD ["pnpm", "next", "start", "-H", "0.0.0.0", "-p", "3000"]
