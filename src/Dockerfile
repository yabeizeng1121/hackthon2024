FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONFAULTHANDLER 1

WORKDIR /src

COPY requirements.txt /src

RUN pip3 install -r requirements.txt

COPY . /src

EXPOSE 5001

ENTRYPOINT ["gunicorn", "app:app"]