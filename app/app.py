import shutil

chrome = shutil.which("chrome")
if chrome is None:
    raise SystemExit("couldn't find chrome")

singlefile = "/opt/webarchive/node_modules/single-file-cli/single-file"
# singlefile = "/Users/josh/webarchive/node_modules/single-file-cli/single-file"

import sys
import hashlib
import time
import functools
import os
import json
import urllib.parse
import subprocess
import multiprocessing

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

multiprocessing.set_start_method("fork")
# multiprocessing.set_start_method("spawn")
# multiprocessing.set_executable(os.path.join(sys.exec_prefix, 'python'))

from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)

BASE_WORKDIR = os.path.expanduser("~/.local/share/webarchive")


def run(workdir: str, cmd: tuple[str]):
    out = open(f"{workdir}/out", "wb")
    sys.stdout = out

    proc = subprocess.run(
        cmd,
        stdout=out,
        stderr=subprocess.PIPE,
        cwd=workdir,
    )
    return proc.returncode


@functools.cache
def slug_workdir(slug: str) -> str:
    slug_blake2b = hashlib.blake2b(slug.encode()).hexdigest()
    return f"{BASE_WORKDIR}/{slug_blake2b}"


@app.route("/p/<slug>", methods=("GET",))
def page(slug):
    # actual page should be stored on disk at slug hash
    # at some point would probably be nice to have sqlite

    swd = slug_workdir(slug)

    fp = f"{swd}/singlefile.html"
    if not os.path.exists(fp):
        # if not on disk yet, ideally we should tail the logfile
        # but not sure if singlefile really displays progress
        # so maybe do an animated dotdotdot that polls
        return "pending"

    return send_file(fp, mimetype="text/html")


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

    workdir = slug_workdir(slug)

    if os.path.isdir(workdir):
        return redirect(url_for("page", slug=slug))

    os.makedirs(workdir)

    p = multiprocessing.Process(
        target=run,
        args=(
            workdir,
            (
                singlefile,
                f"--browser-executable-path={chrome}",
                f"--browser-args={chrome_args}",
                url,
                "singlefile.html",
            ),
        ),
    )
    p.start()

    return redirect(url_for("page", slug=slug))
