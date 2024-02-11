import sys
import os
import json
import subprocess
import multiprocessing

chrome = '/Users/josh/webarchive/chrome/mac_arm-123.0.6291.0/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
singlefile = '/Users/josh/webarchive/node_modules/single-file-cli/single-file'

chrome_args = json.dumps([
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
])

multiprocessing.set_start_method("fork")
#multiprocessing.set_start_method("spawn")
#multiprocessing.set_executable(os.path.join(sys.exec_prefix, 'python'))

from flask import Flask, render_template, request

app = Flask(__name__)


def run(cmd: tuple[str]):
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # TODO we should be saving to sqlite here all the stdout, rc, and a wall time
    return proc.returncode


@app.route("/", methods=("GET", "POST"))
def home():
    if request.method == "GET":
        return render_template("home.html")

    url = request.form["url"]

    p = multiprocessing.Process(
        target=run,
        args=(
            (
                singlefile,
                f"--browser-executable-path={chrome}",
                f"--browser-args={chrome_args}",
                url,
            ),
        ),
    )
    p.start()
    return f"{p.pid}, {p.exitcode}"
