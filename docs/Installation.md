# Installation

Run `docker compose up -d` to bootstrap everything:

It should finish with a launch report:

    [+] Running 10/10
    ⠿ Network es-simple-project_default              Created
    ⠿ Volume "es-simple-project_kafka-data"          Created
    ⠿ Volume "es-simple-project_postgres-data"       Created
    ⠿ Container es-simple-project_django_1           Started
    ⠿ Container es-simple-project_zookeeper_1        Started
    ⠿ Container es-simple-project_postgres_1         Started
    ⠿ Container es-simple-project_nginx_1            Started
    ⠿ Container es-simple-project_broker_1           Started
    ⠿ Container es-simple-project_schema-registry_1  Started
    ⠿ Container es-simple-project_django_archiver_1  Started

If everything works, you should be able to get to the example webapp at http://localhost:8080/example/.

If something goes wrong, you can also check:
- http://localhost:8080/ (the main nginx server)
- http://localhost:8888/ (a "safe" nginx server)
- http://localhost:9090/ (django server directly)

So for example if :8080 works but :9090 throws an error, then nginx is fine but django is down.

## Known issues

Especially when running the first time, there are many things that might need intervention.

- **nginx 404**
  - If you http://localhost:8200/example/ works but http://localhost:8080/example/ returns 404 errors, try restarting nginx
- **example-archiver**
  - It may fail with an error like "Subscribed topic not available: example: Broker: Unknown topic or partition"
  - You need to send a message (to get the type into the topic) then restart this part
- **broker**
  - Sometimes fails saying that the broker id is bad
  - Clear the `kafka-data` volume, or disconnect the broker from it


## <a id='notesformacos'>Notes for MacOS</a>

Docker on MacOS is run on a lightweight VM called LinuxKit, which adds a layer of indirection when compared to a Docker on Linux installation. If performance or volume related questions occur on MacOS, it may be beneficial to re-run on a Linux machine to compare results with MacOS.

 This note describes examples of MacOS differences. For more information, see [docker-for-mac](https://collabnix.com/how-docker-for-mac-works-under-the-hood/).

- **volumes**
  - The `docker info | grep "Root Dir"` command shows `Docker Root Dir: /var/lib/docker`, but `/var/lib/docker` will not be directly viewable in MacOS.
  - The same for other Docker documentation references such as `/var/lib/docker/volumes`.
  - to see these volumes; enter the LinuxVM with the following command: ([see reference](https://github.com/justincormack/nsenter1))
  <pre>
  # enter LinuxVM on MacOS
  docker run -it --rm --privileged --pid=host justincormack/nsenter1<
  # e.g. run this command to find total space (in MiB) used on all volumes
  du -ms /var/lib/docker/volumes/
  </pre>

- **performance**
  - A C program reading records from Kafka running on MacOS took around ~ 9 seconds for 145000 records. The same program running in a Docker container, on MacOS took around 10 times longer, i.e. ~ 100 seconds.
  - A quick test running the same Docker image on a Linux machine ran in ~ 11 seconds. The slow Docker-on_MacOS run time was ignored in this case because Linux is the target operating environment.
