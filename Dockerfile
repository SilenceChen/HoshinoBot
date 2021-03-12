FROM python:3.8.8

ADD ./hoshino /hoshino/
ADD ./res /res/
ADD ./requirements.txt /
ADD ./run.py /

WORKDIR /

RUN pip install -r ./requirements.txt

CMD ["python", "/code/run.py"]