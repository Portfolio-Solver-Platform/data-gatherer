#!/usr/bin/env bash
HARBOR_URL="${HARBOR_URL:-harbor.local}"

REF="$HARBOR_URL/psp/data-gatherer"

docker logout $HARBOR_URL || true
docker login $HARBOR_URL -u admin -p admin

docker build -t data-gatherer:latest .
docker tag data-gatherer:latest $HARBOR_URL/psp/data-gatherer:latest
PUSH_OUT="$(docker push "$REF:latest" 2>&1 | tee /dev/stderr)"
