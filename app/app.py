from flask import Flask, request, render_template, jsonify, send_from_directory
import psycopg2 as db
import json
import tempfile
import os
from subprocess import call
import shutil


conn = db.connect("dbname='geovis_leaflet_d3_flask'")

layer_config = {
  'communes': ('vec200_communes_2015', 'bfsnr AS gid, gemname AS name', 'geom'),
  'cantons': ('vec200_cantons_2015', 'kantonsnr AS gid', 'geom'),
  'districts': ('vec200_districts_2015', 'gid', 'geom'),
  'lacs': ('vec200_lakes', 'seenr AS gid, seename AS name', 'geom')
}

app = Flask(__name__)


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/geom/<int:srid>/<layer>.<format>')
def geom(layer, srid, format):
  l = layer_config.get(layer, None)
  if l is None:
    return jsonify({'status':'error', 'msg': 'Layer not found'})
  if format == 'topojson':
    return get_topojson(layer, srid)
  else:
    return jsonify(get_layer(l, srid))


def get_layer(layer_params, srid):
  c = conn.cursor()
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
  return c.fetchall()[0][0]


def get_topojson(layer, srid):
  # create a temporary folder where we write all the GeoJSON files
  tmpd = tempfile.mkdtemp()
  topofile = '%s_%i.topo.json' % (layer, srid)
  topopath = os.path.join(tmpd, topofile)
  for k in layer_config.keys():
    v = layer_config[k]
    f = open(os.path.join(tmpd, '%s.geojson'%k), 'w')
    f.write(json.dumps(get_layer(v, srid)))
    f.close()
  geojsons = ' '.join(['%s=%s.geojson' % (k,os.path.join(tmpd,k)) for k in layer_config.keys()])
  cmd = 'geo2topo %s | toposimplify -p 1e-5 -f | topoquantize 1e5 > %s' % (geojsons, topopath)
  call(cmd, shell=True)
  return send_from_directory(tmpd, topofile)


@app.route('/data/<layer>_<year>.tsv')
def data(layer, year):
  with open('/Users/ck/Documents/src/geovis-leaflet-d3-flask/data/pop-fem-2034-2015.tsv') as f:
    return f.read()


if __name__ == '__main__':
  app.run(debug=True)

