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
