FROM python:3.6
RUN mkdir /code
RUN mkdir /config
COPY ./ /code/
WORKDIR /code
COPY ./requirements.txt /config/


ENV host 185.230.142.61
ENV login externalanna
ENV password 44iAipyAjHHxkwHgyAPrqPSR5

ENV host_mysql clh.datalight.me
ENV user reader
ENV password_mysql nb7hd-1HG6f
ENV db_mysql coins_dict

ENV login_MQ google_trends
ENV password_MQ X3g6unrboVScnyfe
ENV host_MQ parser.datalight.me
ENV queue google_trends

ENV start 0
ENV end 450


RUN pip install -r /config/requirements.txt


ENV http_proxy 'http://35.235.89.78:85'
ENV https_proxy 'https://165.22.254.98:3128'
