# syntax=docker/dockerfile:1

# renovate: datasource=pypi depName=coveralls
ARG COVERALLS_VERSION=3.3.1
# renovate: datasource=repology depName=alpine_3_19/git versioning=loose
ARG GIT_VERSION=2.43.0-r0


FROM python:3.12-alpine3.19

ARG GIT_VERSION
RUN --mount=type=cache,target=/var/cache/apk \
    apk --update add \
        "git=${GIT_VERSION}"

ARG COVERALLS_VERSION
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install \
        "coveralls==${COVERALLS_VERSION}"
