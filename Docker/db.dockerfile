FROM --platform=linux/amd64 postgres:16.8

RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y libpq-dev gcc curl

RUN mkdir -p /project/backup/
RUN mkdir -p /project/query/

#COPY backup/backup.sql /project/backup/
#COPY init.sql /docker-entrypoint-initdb.d/

# launch postgres
CMD ["postgres"]

