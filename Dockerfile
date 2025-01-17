FROM python:3.8-alpine

RUN apk update && apk upgrade
# GCC.
RUN apk add --no-cache --virtual .build-deps gcc musl-dev

RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Remove gcc.
RUN apk del .build-deps
# Remove cache.
RUN python -m pip cache purge

WORKDIR /scripts/
COPY submitSignature-replayer.py .

WORKDIR /appdata

ENTRYPOINT ["python3", "/scripts/submitSignature-replayer.py"]