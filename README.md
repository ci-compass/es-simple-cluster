# A multi-container cluster setup using docker-compose that illustrates how to retrieve data from Apache Kafka into Apache Flink for processing

**Adam Clark<sup>1</sup>, Michael Gottlieb<sup>2</sup>, Rachel Terry<sup>2</sup>, Karan Vahi<sup>3</sup>, Mike Stults<sup>1</sup>**

**<sup>1</sup>Incorporated Research Institutions for Seismology**

**<sup>2</sup>UNAVCO**

**<sup>3</sup>University of Southern California**



# kafka-flink-cluster

This cluster setup is a simplified version of the setup developed jointly by SAGE and GAGE for Data Collection as part of the EarthScope environment. The setup highlights on how to connect data coming from a topic in Apache Kafka and make it available for processing via Apache Flink.  This setup is also inspired from a similar blog [Flink SQL Demo: Building an End-to-End Streaming Application][1] on Apache Flink website. Some of the key differentiators in this setup from the Flink SQL Demo are

* Setup relies on official Confluent Kafka and Flink container images, which make it easier to update to latest versions of containers by Confluent and Flink
* Setup also includes Confluent Schema Registry that allows us to validate data against the schema.
* Includes Landoop topics UI and landoop schema registry UI containers, allowing users to browse Kafka topics and schemas.
* The producer is an example producer for strainmeter bottle files. It contains 1 Day, Hour, and Min file, which it reads, parses, and produces to the kafka topic gtsm_etl

## Apache Kafka (Short Introduction)

Apache Kafka is a distributed publish/subscribe system. The distribution of Kafka brokers (servers) makes it a reliable system. All messages persist on disk and are replicated in the Kafka cluster to prevent data loss. Apache Kafka is built on top of Apache ZooKeeper, which manages and coordinates all Kafka brokers. Thus, if one Kafka broker is lost, ZooKeeper coordinates tasks with other brokers to continue as is with no data loss or disruption.

Apache Kafka Terms: 
* **Producers** push data to brokers by publishing messages to one or more topics. 
* **Consumers** read data from brokers by subscribing to one or more topics. 
* **Topics** contain a stream of messages belonging to a particular category. 
* Messages are ordered in a topic by its unique identifier, an **offset**
* A topic can have a number of **partitions** to divide the data across. Any message containing a unique **key** will always be sent to the same partition to ensure order.
* A **schema** can be applied to any topic to ensure a structured data format. This schema is versioned and can evolve over time.

For this example, we have an example producer that publishes to a topic named **gtsm_etl** . A message (truncated for brevity) published to this topic looks as follows

```json
{
  "topic": "gtsm_etl",
    "key": {
      "site": "B009"
    },
    "value": {
      "site": {
        "string": "B009"
      },
      "time": null,
      "timestamp": {
        "string": "2021-07-01 00:00:00"
      },
      "rs1_t0": null,
      "rs2_t0": null,
      "rs3_t0": null,
      "rs4_t0": null,
      "ls1_t0": {
        "int": 48116355
      },
      "ls2_t0": {
        "int": 49196540
      },
      "bs1_t0": null,
      "bs2_t0": null
    },
    "partition": 0,
    "offset": 0
}
```

### Schema Registry
This setup includes a Confluent Schema Registry alongside  Kafka data streaming model to ensure data coming into the platform is consistent. Attaching a schema to a topic forces producers and consumers to adhere to the defined format. Consumers can pull the schema from the Schema Registry and always be able to read the data pulled from a topic. Producers will not need to “inform” consumers about schema changes.

The format and content of a particular type of data collection event message is defined by a **schema**. Kafka messages consist of **key-value** pairs.  Each data collection stream or event type will be required to have its own value schema, with an optional key schema as well.  The keys are used to logically distribute messages among partitions within a topic. Hence in our setup, we use a station identifier as a key in order to ensure all data for that station ends up on the same partition, and therefore consumed in order.

The AVRO Schema for the key for the topic **gtsm_etl** is described in avro_schemas/gtsm_etl-key.avsc is shown below
```json
{
  "type": "record",
  "name": "gtsm_etl",
  "namespace": "gtsm_etl",
  "fields": [
    {
      "name": "site",
      "type": "string",
      "doc": "Four Character ID of Site"
    }
  ]
}
```

The corresponding value schema is described in avro_schemas/gtsm_etl-value.avsc and a truncated version shown below
```json
{
            "namespace": "gtsm_etl",
            "name": "gtsm_etl",
            "type": "record",
            "fields": [
                {"name": "site", "type": ["string","null"], "doc":"four character id of site"},
                {"name": "time", "type": ["long","null"], "logicaltype": "timestamp-millis", "doc":"unix epoch milliseconds timestamp"},
                {"name": "timestamp", "type": ["string","null"], "doc":"yyyy-mm-dd hh:mm:ss.fff"},
                {"name": "rs1_t0", "type": ["int","null"], "doc":"10 min strain counts ch0"},
                {"name": "rs2_t0", "type": ["int","null"], "doc":"10 min strain counts ch1"}
            ]
}
```

## Running in Docker Compose

From the root of this project run:

    docker compose up -d

See [Installation](docs/Installation.md) for more.
See [Notes for MacOS](docs/Installation.md#notesformacos) for MacOS variations.

## Services

Below is the list of various containers spun up and main ports to which they bind to.
The hostname is the internal docker assigned hostname for the containers that can be used to access or ping a container when logged into another container of this setup
 
- **kafka-broker**  
  - Kafka broker bound to port 9092
  - Hostname: kafka-broker
- **kafka-zookeeper**  
  - Kafka zookeeper bound to port 2181
  - Hostname: kafka-zookeeper
- **kafka-schema-registry**  
  - Kafka schema registry bound to port 8081
  - Hostname: kafka-schema-registry
- **landoop topics UI**  
  - Kafka topics UI  viewable at http://localhost:8093
  - Hostname: landoop-topics-ui
- **landoop schema registry UI**  
  - Kafka schema registry UI viewable at http://localhost:8094
  - Hostname: landoop-schema-ui
- **flink-sql-client**  
  - Flink container to which we logon to in order to issue sql commands
  - Hostname: flink-sql-client
- **flink-jobmanager**  
  - Jobmanager that schedules flink jobs. Flink Web Dashboard viewable http://localhost:8083 
  - Hostname: flink-jobmanager
- **flink-taskmanager**  
  - Taskmanager on which flink jobs are executed
  - Hostname: flink-taskmanager
  
## Volumes

For the most part, you only need volumes when you want **persistent** or **shared** data.

## AVRO Schemas

For now, AVRO schemas are shared through a file mount.

This path typically gets passed to components like:

    volumes:
      - ./avro_schemas:/avro_schemas:ro
    environment:
      - AVRO_SCHEMAS_ROOT=/avro_schemas

## Kafka brokers and schema registry

Use the following to connect to kafka.

For code running internal to docker-compose network
BOOTSTRAP_SERVERS="kafka-broker:9092"
SCHEMA_REGISTRY_URL="http://kafka-schema-registry:8081"

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
    -- in our example that filed is 'site'
    `key_site` STRING,
    
    -- a few columns mapped to the Avro fields of the Kafka value
    `timestamp` STRING
    
  ) WITH (
  
    'connector' = 'kafka', -- using kafka connector
    'topic' = 'gtsm_etl',   -- kafka topic
    'properties.bootstrap.servers' = 'kafka-broker:9092', -- kafka broker address
    'scan.startup.mode' = 'earliest-offset'  -- reading from the beginning
  
    -- Watch out: schema evolution in the context of a Kafka key is almost never backward nor
    -- forward compatible due to hash partitioning.
    'key.format' = 'avro-confluent',   -- we are using confluent schema registry to host the avro schemas
    'key.avro-confluent.url' = 'http://kafka-schema-registry:8081', -- the url where the schema registry can be accessed
    'key.fields' = 'key_site',
  
    -- In this example, we want the Avro types of both the Kafka key and value to contain the field 'site'
    -- => adding a prefix to the table column associated to the Kafka key field avoids clashes
    'key.fields-prefix' = 'key_',
  
    'value.format' = 'avro-confluent', -- we are using confluent schema registry to host the avro schemas
    'value.avro-confluent.url' = 'http://kafka-schema-registry:8081', -- the url where the schema registry can be accessed
    'value.fields-include' = 'EXCEPT_KEY',
    'properties.group.id' = 'testGroup'
     
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

![Apache Flink Dashboard](/flink/images/flink-taskmanager.png)

There you will see a job running. You can click on the job to get futher details
 ![Apache Flink Dashboard](/flink/images/flink-taskmanager-running-job.png)

# References
[1]: https://flink.apache.org/2020/07/28/flink-sql-demo-building-e2e-streaming-application.html "Flink SQL Demo: Building an End-to-End Streaming Application"
