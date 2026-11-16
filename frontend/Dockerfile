FROM node:26-alpine AS deps
WORKDIR /app
RUN npm install --global npm@11
COPY package.json ./
RUN npm install

FROM node:26-alpine AS builder
WORKDIR /app
RUN npm install --global npm@11
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:26-alpine AS runner
WORKDIR /app
RUN npm install --global npm@11
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
