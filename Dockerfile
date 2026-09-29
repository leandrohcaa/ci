# Local Postgres image used by `make db`.
FROM postgres:16

ENV POSTGRES_USER=db_user
ENV POSTGRES_PASSWORD=db_pass
ENV POSTGRES_DB=db_name

EXPOSE 5432
