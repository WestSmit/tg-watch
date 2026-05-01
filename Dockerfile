FROM python:3.12-alpine

RUN pip install --no-cache-dir telethon requests

WORKDIR /app
COPY run.sh /app/run.sh
COPY tg_watch.py /app/tg_watch.py
COPY app /app/app
RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]