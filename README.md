# es-simple-cluster

A multi-container cluster using docker-compose, including the basic services that are part of the EarthScope environment.

See [docs](docs/) for general documentation.

## Running in Docker Compose

From the root of this project run:

    docker compose up -d

See [Installation](docs/Installation.md) for more.
See [Notes for MacOS](docs/Installation.md#notesformacos) for MacOS variations.

## Services

Ideally, every available service should be included in this project, but for any particular bit of development most of them should probably be commented out for size/performance.

- **broker** (core)
  - Kafka broker
- **zookeeper** (core)
  - Kafka zookeeper
- **schema-registry** (core)
  - Kafka schema registry
- **landoop topics UI** (core)
  - Kafka topics UI
- **landoop schema registry UI** (core)
  - Kafka schema registry UI
- **nginx** (core)
  - external web interface
- **vouch-proxy**
  - provides [CILogon](https://cilogon.org/) authentication for the nginx server
- **postgres**
  - postgres database
- **redis**
  - redis key/value store
- **localstack**
  - [local implementation](docs/localstack/) of AWS (S3, lambda, etc) services
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

## Kafka UIs

topics UI
landoop free UI, shows topics and messages
localhost:8093

schema registry UI
landoop free UI, shows schemas
localhost:8094

## Data collection prototype components so far

strain-producer - image contains sample gtsm bottle files, which it reads in and produces to topic 'gtsm_etl' based on the schema 'gtsm_etl.avsc'.  container exits when done reading files.

ggkx-producer - container connects to RT-GNSS GGKX stream (NTRIP Castor) for station P225 and produces 1 sample per second messages containing an epoch of data.  Uses all_GNSS_position_metadata.avsc schema, and includes original ggkx data and also maps to unified 'position' schema.

slink-producer - connects to rtserve and produces packets from network code HL to topic 'binarypackets'

## Flink Components

 jobmanager - the endpoint to which apache flink jobs are submitted. the web frontend runs on port 8083 that you can access on the host machine (outside the docker network) via http://localhost:8083
 
 taskmanager - the container to which the jobmanager farms out flink jobs. the parallelism of jobs is dictated by the number of slots made available 
 
 sql-client - a vanilla flink container that serves as a standalone client to submit jobs to flink. In our setup, we use it to invoke  `flink-sql-client.sh` after logging in to get the flink sql command line client interface.
