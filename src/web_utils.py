from flask import render_template

def message_log(messages: list[str]):
    print(messages)
    return render_template("message_log.html", messages=messages)
