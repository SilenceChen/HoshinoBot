FROM python:3.8.8

ADD ./hoshino /code/hoshino
ADD ./res /code/res
ADD ./requirements.txt /code
ADD ./run.py /code

WORKDIR /code

RUN pip install -r ./requirements.txt

CMD ["python", "/code/run.py"]