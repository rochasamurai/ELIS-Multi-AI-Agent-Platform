"""
ELIS GitHub A2A server — entrypoint.

Usage (development / smoke-test only):

    /opt/elis/a2a/venv/bin/python -m elis.a2a.github

Binds to 127.0.0.1:9503.  Never binds to 0.0.0.0.
Not a production service — no service install performed here.
"""

from elis.a2a.github.server import run

if __name__ == "__main__":
    run(host="127.0.0.1", port=9503)
