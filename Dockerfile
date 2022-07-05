# ---
# --- Builder image
# ---

FROM python:3.10-alpine as builder

# Install build dependancies
RUN apk update && apk add --upgrade --no-cache g++ make

# Install pipenv
RUN pip install --no-cache-dir --upgrade pip
RUN pip install pipenv

WORKDIR /usr/local/src

# Build a venv with dependancies in current directory
ADD Pipfile.lock Pipfile* /usr/local/src/
RUN PIPENV_VENV_IN_PROJECT=1 pipenv sync

# ---
# --- Application image
# ---

FROM python:3.10-alpine as runtime

# Create the user idunn
RUN addgroup --gid 1000 idunn
RUN adduser --disabled-password --home /home/idunn --ingroup idunn \
            --uid 1000 idunn

ENV PYTHONUNBUFFERED=1

# Set the multiprocess mode for gunicorn
ENV IDUNN_PROMETHEUS_MULTIPROC=1
ENV PROMETHEUS_MULTIPROC_DIR=/home/idunn/prometheus_multiproc

# Install lib dependancies
RUN apk update && apk add --upgrade --no-cache geos

RUN mkdir -p /home/idunn/prometheus_multiproc
USER idunn
WORKDIR /home/idunn

# Add files into images
ADD app.py /home/idunn
ADD idunn /home/idunn/idunn
COPY --from=builder /usr/local/src/.venv /home/idunn/.venv

EXPOSE 5000

# You can set the number of workers by passing --workers=${NB_WORKER} to the docker run command.
# For some reason, an array is required here to accept other params on run.
ENTRYPOINT [                                           \
    "./.venv/bin/python", "-m", "gunicorn", "app:app", \
    "--bind=0.0.0.0:5000",                             \
    "--pid=/tmp/gunicorn.pid",                         \
    "-k", "uvicorn.workers.UvicornWorker",             \
    "--preload"                                        \
]
