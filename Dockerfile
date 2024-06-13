FROM docker.io/debian:12.4-slim as webarchive-builder

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

# Extensions (which is needed for singlefile-cli) are not supported on old Chrome headless AKA chrome-headless-shell.
# https://developer.chrome.com/blog/chrome-headless-shell
# Also, despite not needing X, it's still linked to the same X stuff regular Chrome is.
# And chrome-headless-shell seems to refuse to want to start without dbus system session.
# ADD https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/121.0.6167.85/linux64/chrome-headless-shell-linux64.zip /tmp/chrome.zip

# ADD https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/121.0.6167.85/linux64/chrome-linux64.zip /tmp/chrome.zip
# RUN unzip /tmp/chrome.zip -d /opt/chrome

ADD https://github.com/ungoogled-software/ungoogled-chromium-portablelinux/releases/download/125.0.6422.141-1/ungoogled-chromium_125.0.6422.141-1_linux.tar.xz /tmp/chromium.tar.xz
RUN echo "a65a909dedab5eb3d033115bd83e3929012d3725e5f2e9d8db7a91238980575a  /tmp/chromium.tar.xz" | sha256sum -c - && \
    tar -C /tmp -xf /tmp/chromium.tar.xz && \
    mv /tmp/ungoogled-chromium_125.0.6422.141-1_linux /opt/chrome

# npm install --save-exact single-file-cli
# podman run -it webarchive-builder cat /root/package-lock.json > package-lock.json
WORKDIR /opt/webarchive
COPY "package.json" "package-lock.json" .
RUN npm ci --prefer-offline --no-audit

RUN rm -r /opt/node/lib/node_modules/npm

FROM docker.io/python:3.12-slim-bookworm as webarchive

RUN useradd --system -m webarchive

COPY --from=webarchive-builder /opt/chrome /opt/chrome
COPY --from=webarchive-builder /opt/node /opt/node
COPY --from=webarchive-builder --chown=webarchive:webarchive /opt/webarchive /opt/webarchive

ENV PATH="/opt/node/bin:/opt/chrome:${PATH}"

RUN apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends libglib2.0-0 libnss3 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango1.0-0

RUN PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 pip install 'uv==0.2.11'

COPY app/requirements.txt /opt/webarchive/app/requirements.txt
RUN uv pip install --system --no-cache -r opt/webarchive/app/requirements.txt

COPY --chown=webarchive:webarchive app/ /opt/webarchive/app

COPY chrome-extensions /usr/share/chromium/extensions
# ublock origin
ADD https://clients2.google.com/service/update2/crx?response=redirect&acceptformat=crx2,crx3&prodversion=125.0&x=id%3Dcjpalhdlnbpafiamejdnhcphjbkeiagm%26installsource%3Dondemand%26uc /usr/share/chromium/extensions/cjpalhdlnbpafiamejdnhcphjbkeiagm.crx

USER webarchive
WORKDIR /opt/webarchive/app
EXPOSE 5555/tcp
CMD ["/usr/local/bin/flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5555"]
