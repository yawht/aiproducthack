FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install -Ue '.'

CMD ["yap-worker", "-A", "yap.jobs worker", "--loglevel=DEBUG"]
