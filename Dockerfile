FROM python:3.6-slim@sha256:8aa59c33d0d5b4aa21d2b29c9ca62f1a71d02e4ddaa0193fc749f100dbd7c4d9

# Installing packages
RUN pip install pipenv gunicorn==19.8.1 meinheld==0.6.1

ADD app.py Pipfile* /app/

WORKDIR /app

RUN pipenv install --system --deploy

# the sources are copied as late as possible since they are likely to change often
ADD idunn /app/idunn

EXPOSE 5000

# You can set the number of workers by passing --workers=${NB_WORKER} to the docker run command.
# For some reason, an array is required here to accept other params on run.
ENTRYPOINT ["gunicorn", "app:app", "--bind=0.0.0.0:5000", "--pid=pid", \
  "--worker-class=meinheld.gmeinheld.MeinheldWorker"]
