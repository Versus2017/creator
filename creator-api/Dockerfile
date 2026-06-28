FROM python:3.10

ARG PIP_INDEX_URL
ENV PIP_INDEX_URL=${PIP_INDEX_URL:-https://mirrors.aliyun.com/pypi/simple/}

RUN mkdir /creator
# https://github.com/pypa/pipenv/issues/2924
# https://github.com/pypa/pipenv/issues/2871
RUN pip install pipenv==2023.11.14
RUN pip install pip==20.2.3

COPY Pipfile /creator
COPY Pipfile.lock /creator
WORKDIR /creator
RUN pipenv install --system --deploy

COPY . /creator
WORKDIR /creator
RUN pip install -e .

EXPOSE 8000
ENV WEB_CONCURRENCY=4 WORKER_CONCURRENCY=4
VOLUME ["/creator/local_config.env"]
ENTRYPOINT ["./entrypoint.sh"]
CMD ["web"]

# run web:
#    docker run creator web
# run worker:
#    docker run creator worker
# enter container
#    docker exec -it creator-container bash
