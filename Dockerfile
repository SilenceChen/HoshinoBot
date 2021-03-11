FROM python:3.8.8

RUN pip install -r requirements.txt

CMD ["python", "/code/run.py"]