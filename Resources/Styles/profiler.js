'use strict'

var map = undefined;
var txMarker = undefined;
var rxMarker = undefined;

var defaultColour = [['0.0', 'rgb(255,255,255)'],
				    ['0.111111111111', 'rgb(255,255,204)'],
				    ['0.222222222222', 'rgb(0,255,255)'],
				    ['0.333333333333', 'rgb(0,191,255)'],
				    ['0.444444444444', 'rgb(135,206,250)'],
				    ['0.555555555556', 'rgb(191,255,0)'],
				    ['0.666666666667', 'rgb(255,255,0)'],
				    ['0.777777777778', 'rgb(255,153,51)'],
				    ['0.888888888889', 'rgb(129,0,0)'],
				    ['1.0', 'rgb(255,0,0)']];

$(document).ready(function() {    	 
	$("#loader").hide();
	
	$("#txlat").keyup(function(){
	    update();
	});
	$("#txlng").keyup(function(){
	    update();
	});
	$("#rxlat").keyup(function(){
	    update();
	});
	$("#rxlng").keyup(function(){
	    update();
	});
	
	$("#btnSubmit").click(function(){
		var txLat = $("#txlat").val();
		var txLng = $("#txlng").val();
		var rxLat = $("#rxlat").val();
		var rxLng = $("#rxlng").val();
		
/*
		Cookies.set('txlat', txLat, { expires: 3650, path: '' });
		Cookies.set('txlng', txLng, { expires: 3650, path: '' });
		Cookies.set('rxlat', rxLat, { expires: 3650, path: '' });
		Cookies.set('rxlng', rxLng, { expires: 3650, path: '' }); 
*/
		
		var getData = "?x1=" + txLng + "&y1=" + txLat  + "&x2=" + rxLng + "&y2=" + rxLat;
		console.log(getData);
		
	    $.ajax({
		    url: "/cgi-bin/srtm.py" + getData,
		    type: "GET",
		    beforeSend: function(){
                $("#loader").show();
            },
		    success: function(response){
                $("#loader").hide();
                console.log(response);
			    if ( (response != null) ) {
                	createProfile(response);
			    } else {
				    alert("Error: I'm sorry there was a problem generating the profile");
			    }
		    },
            error: function (error) {
	            console.log(error);
                $("#loader").hide();
			    alert("Error: I'm sorry there was a problem generating the profile");
            }	
		});
	});


	function createProfile(data) {
/*		var data = {
			"points":[{"xcoord":-1.847441,"ycoord":51.372611,"curheight":0,"trueheight":256},
{"xcoord":-1.847450,"ycoord":51.371779,"curheight":0,"trueheight":224},
{"xcoord":-1.847459,"ycoord":51.370948,"curheight":1,"trueheight":207},
{"xcoord":-1.847467,"ycoord":51.370116,"curheight":1,"trueheight":204},
{"xcoord":-1.847476,"ycoord":51.369284,"curheight":1,"trueheight":193},
{"xcoord":-1.847485,"ycoord":51.368452,"curheight":1,"trueheight":176},
{"xcoord":-1.847565,"ycoord":51.360967,"curheight":4,"trueheight":141},
{"xcoord":-1.847573,"ycoord":51.360135,"curheight":4,"trueheight":137},
{"xcoord":-1.847582,"ycoord":51.359303,"curheight":4,"trueheight":136},
{"xcoord":-1.847591,"ycoord":51.358472,"curheight":4,"trueheight":135},
{"xcoord":-1.847600,"ycoord":51.357640,"curheight":5,"trueheight":136},
{"xcoord":-1.850938,"ycoord":51.040750,"curheight":1,"trueheight":69},
{"xcoord":-1.850947,"ycoord":51.039918,"curheight":1,"trueheight":63},
{"xcoord":-1.850956,"ycoord":51.039086,"curheight":1,"trueheight":60},
{"xcoord":-1.850965,"ycoord":51.038254,"curheight":1,"trueheight":60},
{"xcoord":-1.850973,"ycoord":51.037423,"curheight":0,"trueheight":61}],
Output:{"dist":37.365,"surface":37.413,"ascent":15.468,"level":0.000,
"descent":21.945,"min":59,"max":256,"average":135,"minGr":-0.240,
"maxGr":0.343,"aveGr":0.005,"Time taken": 0.027}
};
*/		
		var x = [];
		var y = [];
		var z = [];
		
		var len = data.points.length;
		var startHeight = data.points[0].trueheight - data.points[0].curheight;
		var endHeight = data.points[len-1].trueheight - data.points[len-1].curheight;
		var difference = 0;
		var move = startHeight;
	
		difference = startHeight - endHeight;
		// if difference is positive, start is higher, if 
		// difference is negative, start is lower
		
		var slopeDiff = difference / len;
		
		var title = 'Point To Point Profile (' + data.points[0].ycoord + ' ' + data.points[0].xcoord + ' to ' + data.points[len-1].ycoord + ' ' + data.points[len-1].xcoord + ')';
		for (var i = 0; i < len; i++) {
			x.push(i);
			y.push(data.points[i].trueheight - data.points[i].curheight);
			z.push(move);
			if (difference < 0) { // need to add our difference
				move += -slopeDiff
			} else {
				move -= slopeDiff
			}
		}
		
		var trace = {
			x: x, 
			y: y, 
	  		type: 'scatter',
	  		mode: 'lines',
	  		line: {shape: 'spline'},
	  		fill: 'tozeroy'
		};
		var slope = {
			x: x, 
			y: z,
	  		type: 'scatter',
	  		mode: 'lines',
	  		line: {shape: 'spline'}
	  	};
		
		
		var layout = {
			title: title,
			showlegend: false,
			xaxis: {
				title: '<-- Distance: ' + data.output.dist + 'km -->',
			    showticklabels: false
	  		},
	  		yaxis: {
	  			title: 'Height (m)'
	  		}
		};
		
		var plotData = [trace, slope];
		Plotly.newPlot('profileDiv', plotData, layout);	
	}
	
	
	function update() {
		updateMarkers($("#txlat").val(), $("#txlng").val(), $("#rxlat").val(), $("#rxlng").val())
	}
});

function updateMarkers(txlat, txlng, rxlat, rxlng) {
	txMarker.setPosition( new google.maps.LatLng( txlat, txlng ) );
	rxMarker.setPosition( new google.maps.LatLng( rxlat, rxlng ) );
}

function initMap() {	
	var uluru = {lat: 53, lng: -1};

/*
	var txlat = parseFloat(Cookies.get('txlat')) || 51.75;
	var txlng = parseFloat(Cookies.get('txlng')) || 0.47;
	var rxlat = parseFloat(Cookies.get('rxlat')) || 38.87;
	var rxlng = parseFloat(Cookies.get('rxlng')) || -77.02;
*/
	var txlat = 51.4917;
	var txlng = -0.0127;
	var rxlat = 52.4777;
	var rxlng = -1.8931;

	var tx = {lat: txlat, lng: txlng};
	var rx = {lat: rxlat, lng: rxlng};

	map = new google.maps.Map(document.getElementById('map'), {
	  zoom: 5,
	  center: uluru,
	  disableDefaultUI: true,
	  
	  scrollwheel: false,
	  
	  zoomControl: true,
	  mapTypeControl: true
	});
	
	var iconBase = 'https://maps.google.com/mapfiles/kml/shapes/';

	txMarker = new google.maps.Marker({
	  position: tx,
	  draggable:true,
	  icon: '../img/pins/TxPin.png',
	  map: map
	});
	
	rxMarker = new google.maps.Marker({
	  position: rx,
	  draggable:true,
	  icon: '../img/pins/RxPin.png',
	  map: map
	});
	
     var inittxlat = parseFloat(txlat).toFixed(4);
    var inittxlng = parseFloat(txlng).toFixed(4);
    document.getElementById("txlat").value = inittxlat;
    document.getElementById("txlng").value = inittxlng;
    var initrxlat = parseFloat(rxlat).toFixed(4);
    var initrxlng = parseFloat(rxlng).toFixed(4);
    document.getElementById("rxlat").value = initrxlat;
    document.getElementById("rxlng").value = initrxlng;

	google.maps.event.addListener(txMarker, 'dragend', function (event) {
	    document.getElementById("txlat").value = this.getPosition().lat().toFixed(4);
	    document.getElementById("txlng").value = this.getPosition().lng().toFixed(4);
	});
	google.maps.event.addListener(txMarker, 'drag', function (event) {
	    document.getElementById("txlat").value = this.getPosition().lat().toFixed(4);
	    document.getElementById("txlng").value = this.getPosition().lng().toFixed(4);
	});

	google.maps.event.addListener(rxMarker, 'dragend', function (event) {
	    document.getElementById("rxlat").value = this.getPosition().lat().toFixed(4);
	    document.getElementById("rxlng").value = this.getPosition().lng().toFixed(4);
	});
	google.maps.event.addListener(rxMarker, 'drag', function (event) {
	    document.getElementById("rxlat").value = this.getPosition().lat().toFixed(4);
	    document.getElementById("rxlng").value = this.getPosition().lng().toFixed(4);
	});	
}	
