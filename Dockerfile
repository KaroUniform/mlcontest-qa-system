FROM python:3.11
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt
COPY gunicorn_conf.py /gunicorn_conf.py
COPY ./app /app
WORKDIR /app
COPY ssl/chat.services.kily.ru.cer /ssl/chat.services.kily.ru.cer
COPY ssl/chat.services.kily.ru.key /ssl/chat.services.kily.ru.key
CMD ["gunicorn", "--conf", "../gunicorn_conf.py", "--bind", "0.0.0.0:8000", "main:app"]