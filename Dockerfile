FROM python

ENV TOP_CSV_PATH=output/top.csv
ENV LEAST_CSV_PATH=output/least.csv

COPY ./EmexCatalogSpider /app/EmexCatalogSpider
COPY ./main.py /app/main.py
COPY ./requirements.txt /app/requirements.txt
COPY ./http_proxies.txt /app/http_proxies.txt

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT python main.py