#!/usr/bin/env bash
set -e

###############################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
###############################################################################


# configuration functions picked from the docker-entrypoint.sh of the
# flink containers. we use them to update certain configuration in the flink
# install. this avoids the need for us to create a new docker image and
# rely on official flink provided images for the example.

CONF_FILE="${FLINK_HOME}/conf/flink-conf.yaml"
FLINK_VERSION=`basename $FLINK_ASC_URL | sed  -E "s/flink-(.*)-bin-scala_.*tgz.asc/\1/"`

set_config_option() {
  local option=$1
  local value=$2

  # escape periods for usage in regular expressions
  local escaped_option=$(echo ${option} | sed -e "s/\./\\\./g")

  # either override an existing entry, or append a new one
  if grep -E "^${escaped_option}:.*" "${CONF_FILE}" > /dev/null; then
        sed -i -e "s/${escaped_option}:.*/$option: $value/g" "${CONF_FILE}"
  else
        echo "${option}: ${value}" >> "${CONF_FILE}"
  fi
}

prepare_configuration() {
    # need classloader to be parent first to pick up
    # the additional confluence and avro jars 
    set_config_option classloader.resolve-order parent-first
    set_config_option jobmanager.rpc.address ${FLINK_JOBMANAGER_HOST}
    set_config_option rest.port ${FLINK_JOBMANAGER_REST_PORT}
}

update_flink_install(){
    # we update the flink install with the additional jars we
    # need for our example
    wget -P ${FLINK_HOME}/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka_2.11/${FLINK_VERSION}/flink-sql-connector-kafka_2.11-${FLINK_VERSION}.jar
    wget -P ${FLINK_HOME}/lib https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-avro-confluent-registry/${FLINK_VERSION}/flink-sql-avro-confluent-registry-${FLINK_VERSION}.jar

    cat <<EOF >${FLINK_HOME}/bin/flink-sql-client.sh
#!/bin/bash

${FLINK_HOME}/bin/sql-client.sh embedded -l ${FLINK_HOME}/lib
 
EOF

    chmod +x ${FLINK_HOME}/bin/flink-sql-client.sh
}

update_flink_install

prepare_configuration
