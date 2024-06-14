import os
import shutil
import platform

macos = platform.system() == "Darwin"

chrome = shutil.which("chrome")

if macos:
    chrome = os.environ.get(
        "WEBARCHIVE_CHROME",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",  # --cask eloston-chromium
    )

if chrome is None:
    raise SystemExit("couldn't find chrome")

singlefile = os.environ.get(
    "WEBARCHIVE_SINGLEFILE", "/opt/webarchive/node_modules/single-file-cli/single-file"
)

import hashlib
import time
import functools
import os
import json
import urllib.parse
import subprocess

chrome_args = json.dumps(
    [
        "--headless=new",
        "--no-sandbox",
        "--no-zygote",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--no-first-run",
        "--disable-sync",
        "--ignore-certificate-errors",
        "--disable-breakpad",
        "--disable-software-rasterizer",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        "--use-mock-keychain",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--autoplay-policy=user-gesture-required",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-desktop-notifications",
        "--disable-domain-reliability",
        "--disable-logging",
        "--disable-hang-monitor",
        "--disable-notifications",
        "--disable-popup-blocking",
        "--no-default-browser-check",
        "--disable-extensions-file-access-check",
    ]
)

from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)

BASE_WORKDIR = os.path.expanduser("~/.local/share/webarchive")

WORKERS: dict[str, subprocess.Popen] = {}


@functools.cache
def slug_workdir(slug: str) -> str:
    slug_blake2b = hashlib.blake2b(slug.encode()).hexdigest()
    return f"{BASE_WORKDIR}/{slug_blake2b}"


@app.route("/p/<slug>", methods=("GET",))
def page(slug):
    proc = WORKERS[slug]
    rc = proc.poll()
    if rc is None:
        return "pending"

    swd = slug_workdir(slug)
    fp = f"{swd}/singlefile.html"  # TODO: datetime and page with links
    if os.path.exists(fp):
        return send_file(fp, mimetype="text/html")

    err = "worker error, singlefile was not written."

    with open(f"{slug_workdir(slug)}/out") as f:
        err = f"{err}\nout:\n{f.read()}"

    return err


# TODO: /archive should just list the workdir
# we can have a fancier javascript search indexer later
# @app.route("/archive", methods=("GET", "POST"))
# def archive():


@app.route("/", methods=("GET", "POST"))
def home():
    if request.method == "GET":
        # TODO: home.html should validate that it looks at least like a url
        # TODO: we'll have to add a form to optionally enable
        # singlefile --load-deferred-images-dispatch-scroll-event
        # aaaand then we'll need to add more stuff like a delete button
        return render_template("home.html")

    url = request.form["url"]
    now = time.gmtime()
    slug = f"{now.tm_year}-{now.tm_mon}-{now.tm_hour}-{urllib.parse.quote_plus(url)}"

    if WORKERS.get(slug):
        return redirect(url_for("page", slug=slug))

    workdir = slug_workdir(slug)
    os.makedirs(workdir, exist_ok=True)

    out = open(f"{workdir}/out", "ab", buffering=0)

    proc = subprocess.Popen(
        (
            singlefile,
            f"--browser-executable-path={chrome}",
            f"--browser-args={chrome_args}",
            "--dump-content",
            url,
            # TODO: include datetime
            "singlefile.html",
        ),
        stdout=out,
        stderr=subprocess.PIPE,
        cwd=workdir,
    )

    WORKERS[slug] = proc

    # BUG: if there's an error that happens very quickly, /page will just stay on pending and you need to refresh manually
    return redirect(url_for("page", slug=slug))
