FROM redis:4@sha256:858b1677143e9f8455821881115e276f6177221de1c663d0abef9b2fda02d065

# ADD Redis Metrics Exporter
ADD "https://github.com/oliver006/redis_exporter/releases/download/v0.21.2/redis_exporter-v0.21.2.linux-amd64.tar.gz" /redis_exporter.tar.gz
RUN tar -xv -f /redis_exporter.tar.gz --directory /usr/local/bin/ && rm /redis_exporter.tar.gz

# ADD Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# ADD an entrypoint
ADD docker-entrypoint.sh /usr/local/bin/

# ADD execution permission to local binaries
RUN chmod 555 /usr/local/bin/*

EXPOSE 9121
