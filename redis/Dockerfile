FROM redis:4@sha256:b6977d3ce8c7ee5c1a59146cd58912b5945b8b5ecf887ef2f3d1b2e402387f4e

# ADD redis-trib for redis:4
RUN apt update && apt install -y ruby-redis
ADD "https://raw.githubusercontent.com/antirez/redis/4.0/src/redis-trib.rb" '/usr/local/bin/redis-trib'

# ADD Redis Metrics Exporter
ADD "https://github.com/oliver006/redis_exporter/releases/download/v0.21.2/redis_exporter-v0.21.2.linux-amd64.tar.gz" /redis_exporter.tar.gz
RUN tar -xv -f /redis_exporter.tar.gz --directory /usr/local/bin/ && rm /redis_exporter.tar.gz

# ADD Redis configuration
ADD redis.conf /etc/redis/redis.conf

# ADD an entrypoint
ADD docker-entrypoint.sh /usr/local/bin/

# ADD execution permission to local binaries
RUN chmod 555 /usr/local/bin/*

EXPOSE 9121
