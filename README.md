Два режима работы докера.
1. Режим сбора истории по всем валютам
Для этого в файле docker-compose.yml надо поставить строку 'command: python trends.py all'
2. Режим сбора истории по закачанным валютам
Для этого в файле docker-compose.yml надо поставить строку 'command: python trends.py update'

Внимание!!!! Сначала, надо собрать историю, только после этого можно обновлять данные

P.S. Если очень много качать, google trends блокирует запись на пару часов, потом можно снова начинать 

# Docker template for python development

Implemented to kick start new python projects quickly.
Make your changes to the python version at `docker_conf/python/Dockerfile`

## To run this docker project
```
docker-compose up -d
```

## Check your logs
```
docker logs <CONTAINER_ID> 
```
You should see "Hello World"

## To stop the docker container
```
docker-compose down
```# Trends

##Первый запуск программы, сначала загружается Bitcoin
first_run()
Данные собраны с 2017-01-01 года
Данные по криптовалютам забираются из базы MySQL
Временные данные пишутся в таблицу google.trends prosphero
