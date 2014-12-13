var clat = 24.886436490787712;
var clng = -70.2685546875;
var polygon = [
  {
    lat:25.774252,
    lng:-80.190262
  },
  {
    lat:18.466465,
    lng:-66.118292
  },
  {
    lat:32.321384,
    lng:-64.75737
  },
  {
    lat:25.774252,
    lng:-80.190262
  }
];

function initialize(clat, clng, polygon) {
  var mapOptions = {
    center: new google.maps.LatLng(clat, clng),
    mapTypeId: google.maps.MapTypeId.TERRAIN,
    zoom: 5
  };
  
  var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
  // Define the LatLng coordinates for the polygon's path.
  var triangleCoords = [];
  
  polygon.forEach(function(entry){
    triangleCoords.push(new google.maps.LatLng(entry.lat, entry.lng));
  });

  // Construct the polygon.
  bermudaTriangle = new google.maps.Polygon({
    paths: triangleCoords,
    strokeColor: '#FF0000',
    strokeOpacity: 0.8,
    strokeWeight: 2,
    fillColor: '#FF0000',
    fillOpacity: 0.35
  });

  bermudaTriangle.setMap(map);
}
