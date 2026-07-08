# AgentReplay dashboard image (compose service: frontend) — local/demo use;
# Vercel remains the hosted deploy target. Config via environment variables only.
FROM node:24-alpine AS build
WORKDIR /app
# NEXT_PUBLIC_* vars are inlined into the client bundle at build time —
# must be present here, not just at container runtime.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_AGENTREPLAY_API_KEY=dev-key
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_AGENTREPLAY_API_KEY=$NEXT_PUBLIC_AGENTREPLAY_API_KEY
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
EXPOSE 3000
CMD ["npm", "run", "start"]
