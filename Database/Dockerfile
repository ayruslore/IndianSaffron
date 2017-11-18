FROM python:2.7-slim

WORKDIR /indiansaffron

ADD . /indiansaffron

RUN pip install -r requirements.txt

EXPOSE 4000

ENV NAME wrapper

CMD ["python","redis_wrapper.py"]
