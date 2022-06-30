# ---
# --- Builder image
# ---

FROM python:3.10-alpine as builder

WORKDIR /usr/local/idunn

# Install build dependancies
RUN apk update && apk add --upgrade --no-cache g++ make

# Install pipenv
RUN pip install --no-cache-dir --upgrade pip
RUN pip install pipenv

# Build a venv with dependancies in current directory
ADD Pipfile.lock Pipfile /usr/local/idunn/
RUN PIPENV_VENV_IN_PROJECT=1 pipenv sync

# ---
# --- Application image
# ---

FROM python:3.10-alpine

WORKDIR /usr/local/idunn

ENV PYTHONUNBUFFERED=1

# Set the multiprocess mode for gunicorn
ENV IDUNN_PROMETHEUS_MULTIPROC=1
ENV PROMETHEUS_MULTIPROC_DIR=/usr/local/idunn/prometheus_multiproc
RUN mkdir -p /usr/local/idunn/prometheus_multiproc

# Create the user idunn
RUN addgroup --gid 1000 idunn
RUN adduser --home /usr/local/idunn --ingroup idunn --uid 1000 idunn
USER idunn

# Install lib dependancies
RUN apk update && apk add --upgrade --no-cache geos

# Add files into images
ADD --chown=idunn app.py /usr/local/idunn
ADD --chown=idunn idunn /usr/local/idunn/idunn
COPY --chown=idunn --from=builder /usr/local/idunn/.venv /usr/local/idunn/.venv

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
