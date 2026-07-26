FROM node:24-alpine AS frontend-build

WORKDIR /workspace
COPY agroq-lab/investor-ui/package*.json ./
RUN npm ci
COPY agroq-lab/investor-ui/ ./
RUN npm run build -- --base=/app/

FROM nginx:1.27-alpine

COPY agroq-lab/deployment/staging/nginx.conf.template \
    /etc/nginx/templates/default.conf.template
COPY --from=frontend-build /workspace/dist /usr/share/nginx/html/app

ENV PORT=10000
EXPOSE 10000
