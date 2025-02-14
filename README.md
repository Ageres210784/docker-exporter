# ageres210784/docker-exporter

## Start a docker-exporter instance
```bash
docker run --name docker_exporter -p 127.0.0.1:8000:8000 -v /var/run/docker.sock:/var/run/docker.sock -d ageres210784/docker-exporter
```
## ... or via `docker-compose`
```docker
---
services:
  docker-exporter:
    container_name: docker_exporter
    image: ageres210784/docker-exporter
    restart: always
    ports:
      - 127.0.0.1:8000:8000
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```
Run `docker compose up -d`

## ... or via `docker swarm stack`
```docker
---
services:
  docker-exporter:
    container_name: docker-exporter
    image: ageres210784/docker-exporter
    ports:
      - 8000:8000
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      EXPORTER_MODE: swarm
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role==manager
      restart_policy:
        condition: any
```

Run `docker stack deploy -c docker-compose.yml monitoring`

Visit `http://localhost:8000/metrics`

## Recomendation
For less problems with restarting docker.socket you should use hardlink to /var/run/docker.sock

### Example
Add file /etc/systemd/system/docker.socket.d/override.conf
```ini
[Socket]
ExecStartPost=/bin/ln -f /var/run/docker.sock /var/run/docker.run/docker.sock
```

Use
```Docker
    environment:
      DOCKER_HOST: unix:///var/run/docker.run/docker.sock
    volumes:
      - /var/run/docker.run:/var/run/docker.run:ro
```

## Environment
You can use environment variables:
- `DOCKER_HOST` - path to docker socket (default - unix:///var/run/docker.sock)
- `EXPORTER_MODE` - exporter mode:
  - `"docker"` (default) - scrape containers
  - `"swarm"` - scrape services and tasks
- `SCRAPE_DELAY` - delay between container information updates (default - 10)

## Filter containers
For include/exclude containers, use regexp parameters:
```
http://localhost:8000/probe?include=<regexp>
http://localhost:8000/probe?exclude=<regexp>
http://localhost:8000/probe?include=<regexp>&exclude=<regexp>
```
For example:
```
http://localhost:8000/probe?include=.*exporter&exclude=docker.*
```

## Using in prometheus (victoriametrics) scrape configs
Example:
```yml
- job_name: example.com_docker_exporter
  metrics_path: /probe
  params:
    include:
    - .*exporter
    exclude:
    - docker.*
  scheme: https
  static_configs:
  - targets:
    - example.com:9080
```

## License

Apache 2.0