FROM node:20-slim

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY . .
# NEXT_PUBLIC_* is inlined at build time. On HF Spaces, Space *variables* with
# matching names are passed as build args automatically.
ARG NEXT_PUBLIC_API_URL=https://wei25-agent-social-api.hf.space
ARG NEXT_PUBLIC_SUPABASE_URL=""
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
