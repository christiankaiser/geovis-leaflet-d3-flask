# Application de géovisualisation avec Leaflet, d3 et Flask

Cette application illustre comment combiner PostGIS, Flask avec Leaflet et d3.

Le fond de carte est stocké dans la base de données PostGIS, puis converti automatiquement en TopoJson et puis envoyé au navigateur pour être chargé dans une couche d3 de Leaflet.


## Faire tourner l'application

Pour faire tourner l'application, il faut avoir installé les modules Python dans `requirements.txt` (possible de les installer avec `pip -f requirements.txt`, si possible à l'intérieur d'un Virtual Environement).

Il faut également avoir installé [TopoJson](https://github.com/topojson/topojson), dont notamment l'outil `geo2topo`.

Par la suite, il suffit de lancer `python app/app.py` depuis l'intérieur de ce dossier. Si tout se passe bien, l'application peut être visualisé à l'URL [http://localhost:5000](http://localhost:5000).


## TODO

- Implémenter la mise en classe par Jenks dans le serveur Flask, et mettre les limites de classes en cache. Ceci éviterait de faire la mise en classe dans le navigateur.

- Ajouter une légende digne de ce nom

- Ajouter une information sur les géométries en passant par dessus avec la souris, ou en tapant dessus

- Faire un graphique à côté qui interagit avec la carte


