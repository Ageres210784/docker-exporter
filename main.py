#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import docker
import time
import asyncio
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from typing import List
import re

scraped = None

exporter_mode = os.environ.get("EXPORTER_MODE", "docker")

if exporter_mode == "swarm":
    status_list=["new", "pending", "assigned", "accepted", "ready", "preparing", "starting", "running", "complete", "failed", "shutdown", "rejected", "orphaned", "remove"]
else:
    status_list=["created", "restarting", "running", "removing", "paused", "exited", "dead"]

env = Environment(
    loader=FileSystemLoader('./templates'),
    autoescape=select_autoescape(['j2'])
)
template = env.get_template(exporter_mode + '_metrics.j2')

async def scrape_containers_info():
    while True:
        global scraped
        if exporter_mode == "swarm":
           scraped = await get_services()
        else:
           scraped = await get_containers()
        await asyncio.sleep(10)

app = FastAPI()

async def get_containers():
    cli = docker.from_env()
    t = []
    for container in cli.containers.list(all=True,ignore_removed=True):
        t.append({
            "image": container.attrs['Config']['Image'],
            "name": container.name,
            "status": container.status,
            "time": int(time.time())
        })
    return(t)

async def get_tasks(service):
    t = []
    for task in service.tasks():
        if task['DesiredState'] == "running":
            t.append({
                "id": task['ID'],
                "desired_state": task['DesiredState'],
                "status": task['Status']['State']
            })
    return(t)

async def get_services():
    cli = docker.from_env()
    s = []
    for service in cli.services.list():
        s.append({
            "name": service.name,
            "image": service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'],
            "tasks": await get_tasks(service),
            "time": int(time.time())
        })
    return(s)

def renderer(scraped):
    if exporter_mode == "swarm":
        return(template.render(
            services=scraped,
            statuses=status_list
        ))
    else:
        return(template.render(
            containers=scraped,
            statuses=status_list
        ))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scrape_containers_info())

@app.get('/metrics')
async def metrics():
    return PlainTextResponse(content=renderer(scraped), status_code=200)

@app.get("/probe")
async def probe(
        include: str = '.*',
        exclude: str = ''):
    containers = []
    for container in scraped:
        if re.fullmatch(include,container['name']) and not re.fullmatch(exclude,container['name']):
            containers.append(container)
    return PlainTextResponse(content=renderer(containers), status_code=200)

app.mount("/", StaticFiles(directory="./static", html="True"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host='0.0.0.0', reload='True')
