var M = {
  bbox: [485000, 75000, 834000, 296000],
  data: {}, dataSeries: []
};

// Définition de la carte en SVG avec le cadre notamment
function main(){
  M.map = L.map('mapdiv').setView([46.9, 7.9], 8);

  d3.queue()
    .defer(
      d3.json,
      "geom/4326/communes.topojson"
    )
    .defer(
      d3.tsv,
      "data/popfem2034_2015.tsv",
      function(d){
        M.data[d.id] = d;
        M.dataSeries.push(parseFloat(d.p_fem_singl_2034))
      }
    )
    .await(drawMap);


  // Fonction pour adapter la carte à la fenêtre
  var mapResize = function(){
    d3.select('#mapdiv')
      .style('height', '100vh');
  };
  // Adapter la carte à la fenêtre
  mapResize();
  // Lancer le redimensionnement lors d'un changement de la taille de la fenêtre:
  window.onresize = mapResize;
  
}


function drawMap(error, data){
  if (error) throw error;

  M.data_geom = data;

  // À ce stade, nous avons les données:
  // le TopoJSON dans la variable data,
  // le fichier TSV dans M.data respectivement juste la série de valeurs
  // dans M.dataSeries.

  // Mise en classe de la carte avec Jenks.
  // Nous commençons par créer la mise en classe. On ne doit pas refaire
  // la mise en classe à chaque fois qu'on dessine la carte, alors
  // on peut la calculer avant de créer la couche d3.
  M.brew = new classyBrew();
  M.brew.setSeries(M.dataSeries);
  M.brew.setNumClasses(6);
  M.brew.setColorCode('PuBu');
  M.breaks = M.brew.classify('jenks');

  // Définir la fonction qui permet de traduire les valeurs
  // de la variable à cartographier en codes couleurs.
  // Ceci peut également se faire avant de dessiner la carte,
  // puisque ça ne change pas plus tard.
  M.color = d3.scaleThreshold()
    .domain(M.breaks.slice(1,6))
    .range(M.brew.getColors());

  // Créer la couche d3. On y passe la fonction qui permet de
  // dessiner la couche (donc les instructions pour d3)
  M.communesOverlay = L.d3SvgOverlay(function(sel, proj){

    var features = sel.selectAll('path')
      .data(topojson.feature(data, data.objects.communes).features);

    features
      .enter()
      .append('path')
      .attr('stroke','white')
      .attr('stroke-width', 0)
      .attr('fill', function(d){
        return M.data[d.properties.gid] ?
          M.color(M.data[d.properties.gid].p_fem_singl_2034) :
          '#eee'; // Code couleur pour les données manquantes. 
      })
      .attr('fill-opacity', 1)
      .attr('d', proj.pathFromGeojson);

    // Ici on définit l'épaisseur des contours en fonction de l'échelle.
    // Pour les petites échelles, on ne fait pas de contour, et pour les
    // grandes échelles, un contour de 0.3 points.
    features
      .attr('stroke-width', (proj.scale <= 1 ? 0 : (0.3 / proj.scale)));

  });

  // Ajouter la couche d3 à la carte Leaflet
  M.communesOverlay.addTo(M.map);



  // Ajouter les limites des cantons comme nouvelle couche Leaflet
  M.cantonsOverlay = L.d3SvgOverlay(function(sel, proj){
    var features = sel.selectAll('path')
      .data(topojson.feature(data, data.objects.cantons).features);

    features
      .enter()
      .append('path')
      .attr('stroke','white')
      .attr('stroke-width', 0.6)
      .attr('fill', 'none')
      .attr('d', proj.pathFromGeojson);

    features
      .attr('stroke-width', 0.6 / proj.scale);
  }).addTo(M.map);


  // Ajouter les lacs
  M.lacsOverlay = L.d3SvgOverlay(function(sel, proj){
    var features = sel.selectAll('path')
      .data(topojson.feature(data, data.objects.lacs).features);

    features
      .enter()
      .append('path')
      .attr('class', 'lacs')
      .attr('d', proj.pathFromGeojson);

  }).addTo(M.map);
}
