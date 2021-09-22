# About this project

## Overview

This is intended to be a starting point for work on a container, and a reference environment for development of cross-container features.

It contains a Kafka subsystem, nginx front end, and various storage layers. It also contains a hodgepodge of custom libraries and applications.

## Installation

From the base directory, run

    docker compose up -d

Check that the web front-end is running at http://localhost:8080/

See [Installation](Installation.md) for more.
See [Notes for MacOS](Installation.md#notesformacos) for MacOS variations.

## How to use

_NOTE_ -- this is not really worked-out yet. Ultimately whatever is convenient for developers should be the usage guidelines.

This project is intended to help a developer build a Dockerizable feature -- code and configuration for a Docker image -- which interoperates with the major platform features of the Earthscope architecture.

To develop "inline", create (or link) a subpath in this project containing a `Dockerfile` defining your image, and add it as a service in `docker-compose.yml` using the `build` option:

eg. create:

    simple-project/
      my_feature/
        Dockerfile

and add to the `docker-compose.yml` like:

    services:
        my_feature:
            build: my_feature

See the [Django](https://github.com/earthscope/es-example-django/) subdirectory for an example.

## Components

### Kafka stack

A minimal Confluent Kafka stack (`broker`, `zookeeper`, and `schema-registry`).

The [avro_schemas] subpath is mounted as `/avro_schemas` -- containers should use that.

### Web front end

An `nginx` server intended to operate as a proxy for other web-facing containers.

### Django server

For basic web applications.

### Storage layers

Postgres