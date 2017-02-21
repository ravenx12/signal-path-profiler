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
	
	// Page has loaded now see if we have data in the URL
	if (/x1/.test(window.location.href)) {
		profileOnPageLoad();
	}
	
	$("#btnSubmit").click(function(){
		var txLat = $("#txlat").val();
		var txLng = $("#txlng").val();
		var rxLat = $("#rxlat").val();
		var rxLng = $("#rxlng").val();
		
/*
		Cookies.set('ptxlat', txLat, { expires: 3650, path: '' });
		Cookies.set('ptxlng', txLng, { expires: 3650, path: '' });
		Cookies.set('prxlat', rxLat, { expires: 3650, path: '' });
		Cookies.set('prxlng', rxLng, { expires: 3650, path: '' }); 
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
   			    history.pushState({}, null, "http://www.predtest.uk/profiler/profiler.html" + getData)

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

	// URL was pasted in to the browser so we're creating a saved url plot.
	// A. Don't use any of the values on the page, they're all in the URL
	// B. Don't save anything or update the basic page
	function profileOnPageLoad() {
		var txLat = getURLParameter("y1");
		var txLng = getURLParameter("x1");
		var rxLat = getURLParameter("y2");
		var rxLng = getURLParameter("x2");
		var getData = "?x1=" + txLng + "&y1=" + txLat  + "&x2=" + rxLng + "&y2=" + rxLat;
		
	    $.ajax({
		    url: "/cgi-bin/srtm.py" + getData,
		    type: "GET",
		    beforeSend: function(){
                $("#loader").show();
            },
		    success: function(response){
   			    history.pushState({}, null, "http://www.predtest.uk/profiler/profiler.html" + getData)

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
	}

	function createProfile(data) {		
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

function getURLParameter(name) {
  return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search) || [null, ''])[1].replace(/\+/g, '%20')) || null;
}
