FROM python:3.8

ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN set -e; \
    apt-get update; \
    apt-get install -y --no-install-recommends tini; \
    apt-get install -y --no-install-recommends pandoc; \
    apt-get clean; \
    rm -rf /var/tmp/* /tmp/* /var/lib/apt/lists/*

RUN set -e; \
    pip install sqlitedict flask requests uwsgi Markdown pygments pymdown-extensions markdown bs4 html5 python-slugify python-dateutil rdflib rdflib-jsonld PyLD PyJWT pyyaml Pillow cryptography expiringdict google-cloud google-auth google-cloud-storage 

WORKDIR /usr/src/app

ADD server server
ADD creds creds
ADD index.html .
ADD js js
ADD css css
ADD images images
ADD components components

ENV PORT 8080

WORKDIR /usr/src/app/server

ENTRYPOINT ["tini", "--"]
CMD uwsgi --http :${PORT} --manage-script-name --mount /app=main:app --enable-threads --processes 4