FROM python:3.8.8

WORKDIR /

RUN pip install -r requirements.txt

CMD ["python", "/code/run.py"]