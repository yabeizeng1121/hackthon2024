FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONFAULTHANDLER 1

WORKDIR /src

COPY src/requirements.txt /src/requirements.txt

RUN pip3 install -r requirements.txt

COPY src/ /src

EXPOSE 5001

ENTRYPOINT ["gunicorn", "app:app"]