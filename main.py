import eel
import json
import os

@eel.expose
def test(a):
    eel.getJSON({"data":a})

if __name__ == "__main__":
    eel.init(os.getcwd())
    eel.start("index.html", mode="edge")