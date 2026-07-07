FROM node:20-slim

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY . .
# NEXT_PUBLIC_* is inlined at build time — bake the deployed API URL here.
ARG NEXT_PUBLIC_API_URL=https://wei25-agent-social-api.hf.space
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
