# eg. docker build --build-arg COVERALLS="coveralls==1.2.3" -t coveralls:1.2.3 .
ARG COVERALLS=coveralls

FROM python:3.10-alpine

ARG COVERALLS
RUN apk add --update git && \
    python3 -m pip install "${COVERALLS}"
