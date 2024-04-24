#!/usr/bin/env python3

import backoff
import click
import requests
import yaml
from owslib.wms import WebMapService
from slugify import slugify


class FailedFetch(Exception):
    pass


@backoff.on_exception(
    backoff.expo,
    (FailedFetch, requests.exceptions.Timeout, requests.exceptions.ConnectionError),
)
def load_map(url, version) -> WebMapService:
    wms = WebMapService(url, version=version)

    if len(wms.contents) == 1:
        raise FailedFetch()

    return wms


@click.command()
@click.argument("url")
@click.option("--output", default="mapproxy.yaml")
@click.option("--version", default="1.1.1")
def generate_mapproxy_config(url, output, version):
    wms = load_map(url, version=version)

    sources = {}
    layers = []

    for layer in wms.contents:
        slug = slugify(layer)
        sources[slug] = {
            "type": "wms_retry",
            "retry": {"error_message": "Overforbruk"},
            "req": {
                "url": url + "?",
                "layers": layer,
                "transparent": True,
            },
        }

        layers.append({"name": layer, "title": layer, "sources": [slug]})

    with open(output, "w") as f:
        yaml.dump(
            {
                "services": {"demo": {}, "wms": {}},
                "sources": sources,
                "layers": layers,
            },
            f,
            encoding="utf-8",
            allow_unicode=True,
        )


if __name__ == "__main__":
    generate_mapproxy_config()
