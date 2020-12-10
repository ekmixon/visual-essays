FROM python:3.8

ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN set -e; \
    apt-get update; \
    apt-get install -y --no-install-recommends tini; \
    apt-get clean; \
    rm -rf /var/tmp/* /tmp/* /var/lib/apt/lists/*

RUN set -e; \
    pip install sqlitedict flask requests uwsgi Markdown pygments pymdown-extensions markdown markdown-captions bs4 html5 python-slugify python-dateutil rdflib rdflib-jsonld PyLD PyJWT pyyaml Pillow cryptography expiringdict google-cloud google-auth google-cloud-storage 

WORKDIR /usr/src/app

ADD server server
ADD index.html .
ADD static static
ADD components components

ENV PORT 8080

WORKDIR /usr/src/app/server

ENTRYPOINT ["tini", "--"]
CMD uwsgi --http :${PORT} --manage-script-name --mount /app=main:app --enable-threads --processes 4