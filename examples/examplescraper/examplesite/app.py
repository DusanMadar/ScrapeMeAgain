import random
import sys
import time

from flask import Flask, redirect, render_template, request, url_for

from examplescraper.config import Config


app = Flask(__name__)
timeouted_posts = []


@app.route("/posts/")
def post_list():
    page = int(request.args.get("page", 1))
    if page < 1:
        return redirect(url_for("post_list"))

    page_prev = page - 1
    page_next = page + 1
    page *= 10

    return render_template(
        "list.html",
        start=page - 9,
        stop=page,
        page_next=page_next,
        page_prev=page_prev,
    )


def simulate_response_delay(id):
    if (id % 10 == 0) and len(timeouted_posts) <= 2:
        if id not in timeouted_posts:
            timeouted_posts.append(id)
            time.sleep(
                random.randint(
                    Config.REQUEST_TIMEOUT, Config.REQUEST_TIMEOUT + 2
                )
            )


@app.route("/posts/<int:id>")
def post_detail(id):
    simulate_response_delay(id)
    return render_template("item.html", id=id, back=request.referrer)


if __name__ == "__main__":
    try:
        host = sys.argv[1]
    except IndexError:
        host = "localhost"

    # NOTE: `run` settings has to be in sync with the one in
    # `IntegrationTestCase._run_examplesite()`.
    app.run(host=host, port=9090, ssl_context="adhoc")
