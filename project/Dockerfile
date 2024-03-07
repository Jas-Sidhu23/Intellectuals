FROM python:3.8

ENV HOME /root
WORKDIR /root

COPY . .

#Download Dependencies

EXPOSE 8000

CMD /wait && python -u manage.py