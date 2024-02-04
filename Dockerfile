FROM docker.io/debian:12.4-slim as builder

# git, ssh required to install @postlight/parser... and it still doesn't work lol
RUN apt-get update -qq \
    && apt-get install -qq -y --no-install-recommends xz-utils

ENV PATH="/opt/node/bin:${PATH}"

ADD https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-x64.tar.xz /tmp/node.tar.xz
RUN echo "822780369d0ea309e7d218e41debbd1a03f8cdf354ebf8a4420e89f39cc2e612  /tmp/node.tar.xz" | sha256sum -c - && \
    tar -C /tmp -xf /tmp/node.tar.xz && \
    mv /tmp/node-v20.11.0-linux-x64 /opt/node && \
    node -v && \
    # update npm to latest
    npm i -g npm

# https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json
# https://developer.chrome.com/blog/chrome-for-testing/#how_can_i_get_chrome_for_testing_binaries
ENV CHROME_VERSION=120.0.6099.109 \
    PATH="/opt/node/bin:${PATH}"

WORKDIR /root
RUN npx @puppeteer/browsers install "chrome@${CHROME_VERSION}" \
    && npm install --save-exact single-file-cli

# COPY "package-lock.json" .
# && npm ci --prefer-offline --no-audit --cache /root/.npm \

# FROM docker.io/python:3.12-alpine3.19

# node_modules should be all we need
# COPY --from=builder

# ENV PATH="/app/chrome/linux-${CHROME_VERSION}/chrome-linux64:/app/node_modules/.bin:$PATH"
