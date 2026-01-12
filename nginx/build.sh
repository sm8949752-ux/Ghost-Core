#!/bin/bash
set -e

NGINX_VERSION=$1
NJS_VERSION=$2
NGINX_SHA256=$3
NJS_SHA256=$4

check_hash() {
    local file=$1
    local hash=$2
    if [ -n "$hash" ]; then
        echo "$hash  $file" | sha256sum -c -
    fi
}

mkdir -p /rootfs/usr/sbin /rootfs/usr/lib/nginx/modules /rootfs/etc/nginx \
         /rootfs/var/log/nginx /rootfs/var/cache/nginx /rootfs/var/run

echo 'root:x:0:0:root:/root:/sbin/nologin' > /rootfs/etc/passwd
echo 'nginx:x:101:101:nginx:/var/cache/nginx:/sbin/nologin' >> /rootfs/etc/passwd
echo 'root:x:0:' > /rootfs/etc/group
echo 'nginx:x:101:' >> /rootfs/etc/group

ZLIB_CFLAGS=$(pkg-config --cflags zlib)
ZLIB_LDFLAGS=$(pkg-config --libs zlib)

HARDENING_CFLAGS="-fstack-protector-strong -D_FORTIFY_SOURCE=2 -fPIC"
HARDENING_LDFLAGS="-Wl,-z,relro -Wl,-z,now -fPIC"

CC_OPT="-Wno-error $ZLIB_CFLAGS $HARDENING_CFLAGS"
LD_OPT="$ZLIB_LDFLAGS $HARDENING_LDFLAGS"

CONFIG_ARGS=(
    "--prefix=/etc/nginx"
    "--sbin-path=/usr/sbin/nginx"
    "--modules-path=/usr/lib/nginx/modules"
    "--conf-path=/etc/nginx/nginx.conf"
    "--error-log-path=/var/log/nginx/error.log"
    "--http-log-path=/var/log/nginx/access.log"
    "--pid-path=/var/run/nginx.pid"
    "--lock-path=/var/run/nginx.lock"
    "--http-client-body-temp-path=/var/cache/nginx/client_temp"
    "--http-proxy-temp-path=/var/cache/nginx/proxy_temp"
    "--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp"
    "--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp"
    "--http-scgi-temp-path=/var/cache/nginx/scgi_temp"
    "--user=nginx"
    "--group=nginx"
    "--with-compat"
    "--with-file-aio"
    "--with-threads"
    "--with-http_ssl_module"
    "--with-http_v2_module"
    "--with-http_realip_module"
    "--with-http_gunzip_module"
    "--with-http_gzip_static_module"
    "--with-http_slice_module"
    "--with-http_stub_status_module"
    "--with-stream=dynamic"
    "--with-stream_ssl_module"
    "--with-stream_realip_module"
    "--with-cc-opt=${CC_OPT}"
    "--with-ld-opt=${LD_OPT}"
)

if [ -n "$NJS_VERSION" ]; then
    wget -qO njs.tar.gz "https://github.com/nginx/njs/archive/refs/tags/${NJS_VERSION}.tar.gz"
    check_hash "njs.tar.gz" "$NJS_SHA256"
    tar -xzf njs.tar.gz
    CONFIG_ARGS+=("--add-dynamic-module=../njs-${NJS_VERSION}/nginx")
fi

wget -qO nginx.tar.gz "http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz"
check_hash "nginx.tar.gz" "$NGINX_SHA256"
tar -xzf nginx.tar.gz
cd nginx-${NGINX_VERSION}

./configure "${CONFIG_ARGS[@]}" || { echo "Configure Failed"; cat objs/autoconf.err; exit 1; }

make -j"$(nproc)"
make install DESTDIR=/rootfs

strip /rootfs/usr/sbin/nginx
if [ -d "/rootfs/usr/lib/nginx/modules" ]; then
    strip /rootfs/usr/lib/nginx/modules/*.so 2>/dev/null || true
fi

if [ -z "$NJS_VERSION" ]; then
    rm -f /rootfs/usr/lib/nginx/modules/ngx_http_js_module.so \
          /rootfs/usr/lib/nginx/modules/ngx_stream_js_module.so
fi

ln -sf /dev/stdout /rootfs/var/log/nginx/access.log
ln -sf /dev/stderr /rootfs/var/log/nginx/error.log

cd ..
rm -rf nginx.tar.gz nginx-${NGINX_VERSION} njs.tar.gz njs-${NJS_VERSION}