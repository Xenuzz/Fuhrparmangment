FROM node:22-alpine AS build
WORKDIR /app
COPY webui/package.json /app/package.json
RUN npm install
COPY webui /app
COPY config/system_config.json /app/public/system_config.json
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
