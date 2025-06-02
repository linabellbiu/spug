FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/guergeiro/pnpm:18-9-alpine AS builder

WORKDIR /app
ADD . .
#RUN npm config set electron_mirror https://cdn.npm.taobao.org/dist/electron/
RUN export NODE_OPTIONS=--openssl-legacy-provider && \
    rm -rf node_modules package-lock.json && \
    pnpm i && \
    pnpm run build

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nginx:alpine

WORKDIR /data/spug/spug_web/build

COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build /data/spug/spug_web/build

# 修复权限问题
RUN chmod -R 755 /data/spug/spug_web/build && \
    chown -R nginx:nginx /data/spug/spug_web/build

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
