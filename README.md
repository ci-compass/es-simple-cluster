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

### Using Flink to query from Kafka topic using Flink SQL Client
```bash 
$ docker-compose  exec  sql-client /bin/bash

root@4a339a52acba:/opt/flink# ls
LICENSE  NOTICE  README.txt  bin  conf	examples  lib  licenses  log  opt  plugins  update_flink_install.sh
```

We now have to run a script that will update the flink install to download the relevant kafka jars that enable us to query kafka topics and also do schema registry validation

```bash
root@4a339a52acba:/opt/flink# ./update_flink_install.sh 
...
Saving to: ‘/opt/flink/lib/flink-sql-connector-kafka_2.11-1.14.2.jar’
Saving to: ‘/opt/flink/lib/flink-sql-avro-confluent-registry-1.14.2.jar’
```

Now we can run the sql client to bring up the sql interface
```bash
root@4a339a52acba:/opt/flink# /opt/flink/bin/flink-sql-client.sh
Command history file path: /root/.flink-sql-history

                                   ...
          
    ______ _ _       _       _____  ____  _         _____ _ _            _  BETA   
   |  ____| (_)     | |     / ____|/ __ \| |       / ____| (_)          | |  
   | |__  | |_ _ __ | | __ | (___ | |  | | |      | |    | |_  ___ _ __ | |_ 
   |  __| | | | '_ \| |/ /  \___ \| |  | | |      | |    | | |/ _ \ '_ \| __|
   | |    | | | | | |   <   ____) | |__| | |____  | |____| | |  __/ | | | |_ 
   |_|    |_|_|_| |_|_|\_\ |_____/ \___\_\______|  \_____|_|_|\___|_| |_|\__|
          
        Welcome! Enter 'HELP;' to list all available commands. 'QUIT;' to exit.


Flink SQL> 
```

We will now first create a SQL table that maps to the kafka topic `gtsm_etl` that we have . 
To do issue the following commands in flink sql interface

```sql
Flink SQL> CREATE TABLE gtsm_etl (
    
    -- one column mapped to the 'id' Avro field of the Kafka key
    `key_site` STRING,
    
    -- a few columns mapped to the Avro fields of the Kafka value
    `timestamp` STRING
    
  ) WITH (
  
    'connector' = 'kafka',
    'topic' = 'gtsm_etl',
    'properties.bootstrap.servers' = 'broker:9092',
  
    -- Watch out: schema evolution in the context of a Kafka key is almost never backward nor
    -- forward compatible due to hash partitioning.
    'key.format' = 'avro-confluent',
    'key.avro-confluent.url' = 'http://schema-registry:8081',
    'key.fields' = 'key_site',
  
    -- In this example, we want the Avro types of both the Kafka key and value to contain the field 'id'
    -- => adding a prefix to the table column associated to the Kafka key field avoids clashes
    'key.fields-prefix' = 'key_',
  
    'value.format' = 'avro-confluent',
    'value.avro-confluent.url' = 'http://schema-registry:8081',
    'value.fields-include' = 'EXCEPT_KEY',
    'properties.group.id' = 'testGroup',
    'scan.startup.mode' = 'earliest-offset'
     
    -- subjects have a default value since Flink 1.13, though can be overriden:
    -- 'key.avro-confluent.schema-registry.subject' = 'user_events_example2-key2',
    -- 'value.avro-confluent.schema-registry.subject' = 'user_events_example2-value2'
  );
[INFO] Execute statement succeed.

```

Now we have a Flink SQL table that maps directly to query the Kafka topic `gtsm_etl`
Lets query the table and retrieve the data from this topic

```sql

Flink SQL> select * from gtsm_etl;

                      key_site                      timestamp
                           B009            2021-07-01 16:50:00
                           B009            2021-07-01 17:00:00
                           B009            2021-07-01 17:10:00
                           B009            2021-07-01 17:20:00
                           B009            2021-07-01 17:30:00
                           ....
```

### Behind the scenes. 

When we issued the select command, a flink job gets launched by the jobmanager, and the jobs run in the task manager container

You can navigate to http://localhost:8083 in your local web browser 

![Apache Flink Dashboard](/images/flink-taskmanager.png)

There you will see a job running. You can click on the job to get futher details
 ![Apache Flink Dashboard](/images/flink-taskmanager-running-job.png)

