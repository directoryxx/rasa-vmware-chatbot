FROM rasa/rasa:3.6.18-full

WORKDIR /app

USER root

COPY ./requirements.txt .

RUN pip install -r requirements.txt

USER 1000

# CMD ["/bin/bash"]