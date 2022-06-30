FROM python:3.10-alpine

ENV PYTHONPATH="/usr/local/idunn"
ENV PYTHONUNBUFFERED=1

# create the user idunn
RUN addgroup --gid 1000 idunn \
 && adduser \
      --disabled-password \
      --home /usr/local/idunn \
      --ingroup idunn \
      --uid 1000 \
      idunn

RUN apk update \
    && apk add --upgrade --no-cache \
        bash openssh curl ca-certificates openssl less htop gcc git \
		g++ make wget rsync \
        build-base libpng-dev freetype-dev libexecinfo-dev openblas-dev libgomp lapack-dev \
		libgcc libquadmath musl  \
		libgfortran \
		lapack-dev \
        geos \
	&&  pip install --no-cache-dir --upgrade pip

# for run only: geos

WORKDIR /usr/local/idunn

# Installing packages
RUN pip install pipenv==2022.6.7

ADD --chown=idunn app.py Pipfile* /usr/local/idunn/
RUN pipenv install --system --deploy


USER idunn

# The sources are copied as late as possible since they are likely to change often
ADD --chown=idunn idunn /usr/local/idunn/idunn
RUN mkdir /usr/local/idunn/prometheus_multiproc

# Set the multiprocess mode for gunicorn
ENV IDUNN_PROMETHEUS_MULTIPROC=1
ENV PROMETHEUS_MULTIPROC_DIR=/usr/local/idunn/prometheus_multiproc

EXPOSE 5000

# You can set the number of workers by passing --workers=${NB_WORKER} to the docker run command.
# For some reason, an array is required here to accept other params on run.
ENTRYPOINT ["gunicorn", "app:app", "--bind=0.0.0.0:5000", "--pid=/tmp/gunicorn.pid", \
    "-k", "uvicorn.workers.UvicornWorker", "--preload"]
