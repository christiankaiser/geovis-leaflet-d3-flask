from flask import Flask, request, render_template, jsonify, send_from_directory
import psycopg2 as db
import json
import os
from subprocess import call


conn = db.connect("dbname='geovis_leaflet_d3_flask'")

layer_config = {
  'communes': ('vec200_communes_2015', 'bfsnr AS gid, gemname AS name', 'geom'),
  'cantons': ('vec200_cantons_2015', 'kantonsnr AS gid', 'geom'),
  'districts': ('vec200_districts_2015', 'gid', 'geom'),
  'lacs': ('vec200_lakes', 'seenr AS gid, seename AS name', 'geom')
}

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(base_dir, 'cache')

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(base_dir,'static'), 'favicon.ico')


@app.route('/geom/<int:srid>/<layer>.<format>')
def geom(layer, srid, format):
  reload = False if request.args.get('reload', None) is None else True
  if format == 'topojson':
    return get_topojson(layer, srid, reload)
  return get_layer(layer, srid, reload)


def get_layer(layer, srid, reload=False):
  filename = '%s_%i.geojson' % (layer, srid)
  cache_layer(layer, srid, force=reload)
  return send_from_directory(cache_dir, filename)


def cache_layer(layer, srid, force=False):
  filename = '%s_%i.geojson' % (layer, srid)
  filepath = os.path.join(cache_dir, filename)
  if os.path.exists(filepath) and force is False: return
  c = conn.cursor()
  layer_params = layer_config.get(layer, None)
  if layer_params is None: return
  l = { 'table': layer_params[0], 'props': layer_params[1], 'geom': layer_params[2], 'srid': srid}
  sql = """SELECT json_build_object('type', 'FeatureCollection', 'features', F.feats)
         FROM (
           SELECT array_to_json(array_agg(row_to_json(G))) AS feats FROM (
             SELECT
               P.properties, 
               ST_AsGeojson(ST_Transform(G.%(geom)s, %(srid)i))::json AS geometry 
             FROM 
               (
                 SELECT gid, row_to_json(L) AS properties 
                 FROM (SELECT %(props)s FROM %(table)s) L) P 
                 JOIN (SELECT %(props)s, %(geom)s FROM %(table)s) G ON P.gid = G.gid
               ) G
         ) F""" % l
  c.execute(sql)
  res = c.fetchall()[0][0]
  with open(filepath, 'w') as f: f.write(json.dumps(res))


def get_topojson(layer, srid, reload=False):
  topofile = '%s_%i.topo.json' % (layer, srid)
  topopath = os.path.join(cache_dir, topofile)
  if not os.path.exists(topopath) or reload:
    for k in layer_config.keys():
      cache_layer(k, srid, reload)
    geojsons = ' '.join([
      '%s=%s_%i.geojson' % (k, os.path.join(cache_dir,k), srid) 
      for k in layer_config.keys()
    ])
    cmd = 'geo2topo %s | toposimplify -p 1e-5 -f | topoquantize 1e5 > %s' % (geojsons, topopath)
    call(cmd, shell=True)
  return send_from_directory(cache_dir, topofile)


@app.route('/data/<layer>_<year>.tsv')
def data(layer, year):
  with open(os.path.join(base_dir, 'data', 'pop-fem-2034-2015.tsv')) as f:
    return f.read()

@app.route('/cache/expire')
def expire_cache():
  for root, dirs, files in os.walk(cache_dir):
    for f in files:
      if f.startswith('.') is False:
        os.unlink(os.path.join(root, f))
  return jsonify({'status': 'cached expired'})


if __name__ == '__main__':
  app.run(debug=True)

