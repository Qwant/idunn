FROM python:3.8-slim

RUN apt-get update && apt-get -y install git gcc

RUN useradd -r app_user
RUN mkdir /app
RUN chown app_user /app/
WORKDIR /app

# Installing packages
RUN pip install pipenv==2018.11.26

ADD --chown=app_user app.py Pipfile* /app/
RUN pipenv install --system --deploy

USER app_user

# the sources are copied as late as possible since they are likely to change often
ADD --chown=app_user idunn /app/idunn

# set the multiprocess mode for gunicorn
ENV IDUNN_PROMETHEUS_MULTIPROC=1
ENV PROMETHEUS_MULTIPROC_DIR=/app/idunn/prometheus_multiproc
RUN mkdir /app/idunn/prometheus_multiproc

EXPOSE 5000

# You can set the number of workers by passing --workers=${NB_WORKER} to the docker run command.
# For some reason, an array is required here to accept other params on run.
ENTRYPOINT ["gunicorn", "app:app", "--bind=0.0.0.0:5000", "--pid=/tmp/gunicorn.pid", \
    "-k", "uvicorn.workers.UvicornWorker", "--preload"]
