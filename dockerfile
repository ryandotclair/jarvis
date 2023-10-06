FROM alpine:latest

RUN apk --update add python3 \
    && apk add py3-pip \
    && rm -f /var/cache/apk/* \
    && pip3 install --upgrade pip \
    && pip3 install --upgrade setuptools
ENTRYPOINT /bin/ash
