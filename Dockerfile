FROM python:3.11.4
ADD auto-serve/main.py .
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /tmp/requirements.txt
CMD python main.py