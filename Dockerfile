FROM python3.8.8

ADD ./* /code

WORKDIR /code

RUN pip install -r requirements.txt

CMD ["python", "/code/run.py"]