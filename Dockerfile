FROM python:3.8.8

ADD ./hoshino /hoshino/code/
ADD ./res /res/code/
ADD ./requirements.txt /code/
ADD ./run.py /code/

WORKDIR /code

RUN pip install -r ./requirements.txt

CMD ["python", "/code/run.py"]