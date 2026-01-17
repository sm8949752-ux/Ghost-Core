echo "Downloading: http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz"
wget -O nginx.tar.gz "http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz"
if [ -n "$NGINX_SHA256" ]; then echo "$NGINX_SHA256  nginx.tar.gz" | sha256sum -c -; fi
tar -xzf nginx.tar.gz
cd nginx-${NGINX_VERSION}

./configure "$@" || { echo "Configure Failed"; cat objs/autoconf.err; exit 1; }

bear -- make -j"$(nproc)"

mkdir -p /rootfs/usr/share/doc/nginx/
cdxgen -t c --compile-commands compile_commands.json -o /rootfs/usr/share/doc/nginx/nginx.cdx.json .

make install DESTDIR=/rootfs

strip /rootfs/usr/sbin/nginx
find /rootfs/usr/lib/nginx/modules -name "*.so" -exec strip {} \;