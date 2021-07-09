import asyncio
import flask
try:
    import upnpc_py
except ModuleNotFoundError:
    pass
try:
    import ujson as json
except ModuleNotFoundError:
    import json
import time
import os
from flask.json import JSONEncoder
import leaflet_backend


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            return json.dumps(obj)
        except TypeError:
            return JSONEncoder.default(self, obj)


lb = leaflet_backend.LeafBackend()
try:
    pm = upnpc_py.port_manager()
    pm.mapport(port=5000)
    print(f"http://{pm.upnp.externalipaddress()}:5000")
except NameError:
    pass
app = flask.Flask(__name__, static_url_path='', template_folder='./leaflet_overlay')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.json_encoder = CustomJSONEncoder


@app.route('/leaflet_overlay/<path:path>')
async def leaflet(path):
    return flask.send_from_directory('leaflet_overlay', path)


@app.route("/values")
async def values():
    kwargs = flask.request.args
    result = lb.values(kwargs)
    return flask.jsonify(result)

@app.route("/overlay")
async def overlay():
    kwargs = flask.request.args
    result = lb.overlay(kwargs)
    return flask.jsonify(result)


@app.route('/images/<path:path>')
async def images(path):
    lb.images(path)
    return flask.send_from_directory("images", path)


@app.route('/templates/<path:path>')
async def templates(path):
    return flask.send_from_directory('templates', path)


@app.route("/")
async def index():
    render = flask.render_template('mobile.html', years=lb.merra.years_unique)
    return render

@app.errorhandler(Exception)
def handle_error(e):
    if hasattr(e, "code"):
        if e.code == 404:
            return flask.render_template('mobile.html'), e.code
        elif e.code == 400:
            return flask.jsonify({"result":False, "code":e.code})
    flask.abort(500)




if __name__ == "__main__":
    app.run(host='0.0.0.0')

