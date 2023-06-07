# QA-bask-bot

Вопросно-ответная система для поддержки пользователей. 

## 🐋 Запуск с Docker:

Соберем образ:

`sudo docker build -t bask-qa .`

Запускаем контейнер в первый раз: 

`sudo docker run -v whoosh:/app/core/Reader/bask_products -v qa-expert:/app/core/Expert/qa-expert -p 8000:8000 -d --name Bask-qa bask-qa`

