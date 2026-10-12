# syntax=docker/dockerfile:1

# renovate: datasource=pypi depName=coveralls
ARG COVERALLS_VERSION=4.1.0
# renovate: datasource=repology depName=alpine_3_24/git versioning=loose
ARG GIT_VERSION=2.54.0-r0


FROM python:3.15-alpine3.24

ARG GIT_VERSION
RUN --mount=type=cache,target=/var/cache/apk \
    apk --update add \
        "git=${GIT_VERSION}"

ARG COVERALLS_VERSION
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install \
        "coveralls==${COVERALLS_VERSION}"
