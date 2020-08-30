FROM python:3.8-slim-buster

# Add a user, best practice to not run as root:
RUN adduser --gecos "" --disabled-password debian

# Common apt stuff
RUN apt-get update && \
  apt-get install -y nano curl wget

COPY requirements.txt /home/debian/requirements.txt

# Python packages
RUN pip install --upgrade pip && \
    pip install --upgrade -r /home/debian/requirements.txt

COPY app.py /home/debian/app.py

WORKDIR /home/debian/service

USER debian

CMD ["streamlit", "run", "/home/debian/app.py"]
