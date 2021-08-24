# es-simple-cluster

A multi-container cluster using docker-compose, including the basic services that are part of the EarthScope environment.

See [docs](docs/) for general documentation.

## Running in Docker Compose

From the root of this project run:

    docker compose up -d

See [Installation](docs/Installation.md) for more.

## Services

Ideally, every available service should be included in this project, but for any particular bit of development most of them should probably be commented out for size/performance.

- **broker** (core)
  - Kafka broker
- **zookeeper** (core)
  - Kafka zookeeper
- **schema-registry** (core)
  - Kafka schema registry
- **nginx** (core)
  - external web interface
- **vouch-proxy**
  - provides [CILogon](https://cilogon.org/) authentication for the nginx server
- **postgres**
  - postgres database
- **redis**
  - redis key/value store
- **prometheus**
  - metrics backend
- **grafana**
  - metrics front end
- **examples**
  - some [example](docs/example/) functionality

## Volumes

For the most part, you only need volumes when you want **persistent** or **shared** data.

- **web-static**
  - Static web content produced by Django, surfaced by nginx
- **kafka-data**
  - Data backend for the broker
  - _Disabled by default_ to avoid kafka errors
- **postgres-data**
  - Storage for postgres
- **prometheus**
  - Storage for prometheus
- **grafana**
  - Storage for grafana (ie. user accounts, dashboards)

## /avro_schemas

For now, AVRO schemas are shared through a file mount.

This path typically gets passed to components like:

    volumes:
      - ./avro_schemas:/avro_schemas:ro
    environment:
      - AVRO_SCHEMAS_ROOT=/avro_schemas

## Kafka brokers and schema registry

Use the following to connect to kafka.

For code running internal to docker-compose network
BOOTSTRAP_SERVERS="broker:9092"
SCHEMA_REGISTRY_URL="http://schema-registry:8081"

Code running on local machine, not in docker-compose env
BOOTSTRAP_SERVERS='localhost:19092'
SCHEMA_REGISTRY_URL='http://localhost:8081'
