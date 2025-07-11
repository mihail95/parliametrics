## BUILD PROD
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml up -d --build


## BUILD DEV
docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --build