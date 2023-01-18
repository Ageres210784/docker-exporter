#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import docker
import time
import asyncio

from jinja2 import Environment, FileSystemLoader, select_autoescape

scraped = None

env = Environment(
    loader=FileSystemLoader('./templates'),
    autoescape=select_autoescape(['j2'])
)
template = env.get_template('metrics.j2')

async def scrape_containers_info():
    while True:
        global scraped
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

def renderer():
    return(template.render(
        containers=scraped,
        statuses=["created", "restarting", "running", "removing", "paused", "exited", "dead"]
    ))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scrape_containers_info())

@app.get('/metrics')
def metrics():
    return PlainTextResponse(content=renderer(), status_code=200)

app.mount("/", StaticFiles(directory="./static", html="True"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host='0.0.0.0', reload='True')
