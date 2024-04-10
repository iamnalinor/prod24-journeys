FROM python:3.12.1-alpine3.19

WORKDIR /app

ENV POETRY_VERSION=1.8
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=0

STOPSIGNAL SIGKILL

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock /app/
RUN poetry install --only=main --no-interaction --no-ansi

COPY . /app/
RUN chmod +x /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["run-polling"]
