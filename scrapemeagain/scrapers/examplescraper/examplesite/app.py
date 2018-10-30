from flask import Flask, render_template, request


app = Flask(__name__)


@app.route("/posts/")
def post_list():
    page = int(request.args.get("page", 0))
    page_prev = page - 1
    page_next = page + 1
    page *= 10

    return render_template(
        "list.html",
        start=0 + page,
        stop=10 + page,
        page_next=page_next,
        page_prev=page_prev,
    )


@app.route("/posts/<id>")
def post_detail(id):
    return render_template("item.html", id=id, back=request.referrer)


if __name__ == "__main__":
    # TODO the IP below is for my local docker bridge. Add a function which
    # can get it dynamically.
    app.run(host="172.17.0.1", port=9090)
