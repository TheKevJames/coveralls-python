# syntax=docker/dockerfile:1

# renovate: datasource=pypi depName=coveralls
ARG COVERALLS_VERSION=4.0.2
# renovate: datasource=repology depName=alpine_3_22/git versioning=loose
ARG GIT_VERSION=2.49.1-r0


FROM python:3.14-alpine3.22

ARG GIT_VERSION
RUN --mount=type=cache,target=/var/cache/apk \
    apk --update add \
        "git=${GIT_VERSION}"

ARG COVERALLS_VERSION
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install \
        "coveralls==${COVERALLS_VERSION}"
