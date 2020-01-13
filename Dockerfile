FROM python:3-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apk del .build-deps

COPY storybot storybot/

CMD ["python", "-u", "-m", "storybot", "--post", "/etc/storybot.yaml"]
