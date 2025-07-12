## Create network (once)
docker network create parliametrics-net

## BUILD PROD
docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml up -d --build


## BUILD DEV
docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Run worker script
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm worker python /worker/scripts/seed_parties.py
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm worker python /worker/scripts/seed_parties.py