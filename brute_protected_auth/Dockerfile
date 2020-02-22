FROM python:3.7

RUN apt update && apt install -y netcat

RUN pip install --upgrade pip

RUN pip install gunicorn

COPY requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY docker/bin /bin

WORKDIR /srv/server

COPY . .

RUN rm -rf docker

ENV WORKERS=2

ENTRYPOINT ["entrypoint.sh"]
CMD /bin/server.sh



