function mapJS() {
    class ImageOverlay {
        constructor() {
            this.image = undefined;
            this.fromdate = '1980';
            this.todate = '2020';
        }
    }
    var mymap = L.map('map').setView([0, 0], 2);

    var overlay = new ImageOverlay();

    const addLayer = async (fname) => {
        if (mymap.hasLayer(overlay.image)) {
            mymap.removeLayer(overlay.image);
        }
        overlay.imageUrl = fname,
            overlay.imageBounds = [
                [-90.0, -180.0],
                [90.0, 180.0]
            ],
            overlay.image = L.imageOverlay(overlay.imageUrl, overlay.imageBounds).setOpacity(0.7);
        overlay.image.addTo(mymap);
    };

    const FetchValues = async (lat, lon, todate, fromdate, callback) => {
        let ValuesData = await fetch(`/values?lat=${lat}&lon=${lon}&fromdate=${fromdate}&todate=${todate}`);
        let ValuesDict = await ValuesData.json();
        return ValuesDict;
    }

    const OverlayStatus = async (fromdate, todate, callback) => {
        let ValuesData = await fetch(`/overlay?&fromdate=${fromdate}&todate=${todate}`);
        let ValuesDict = await ValuesData.json();
        return ValuesDict;
    }

    addLayer(`/images/mean_changes/${overlay.fromdate}_${overlay.todate}.jpg`);

    L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
            'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        id: 'mapbox/streets-v11',
        tileSize: 512,
        zoomOffset: -1
    }).addTo(mymap);

    var popup = L.popup();
    const onMapClick = async (e) => {
        popup.setLatLng(e.latlng);
        let jsonData = await FetchValues(e.latlng.lat, e.latlng.lng, overlay.todate, overlay.fromdate);
        if (jsonData.diff > 0) {
            popup.setContent(`Temperature change: +${jsonData.diff}`);
        } else {
            popup.setContent(`Temperature change: ${jsonData.diff}`);
        }
        popup.openOn(mymap);

    };

    mymap.on('click', onMapClick);

    var slider = document.getElementById('slider');

    noUiSlider.create(slider, {
        start: [1980, 2020],
        tooltips: [
            wNumb({
                decimals: 0
            }),
            wNumb({
                decimals: 0
            })
        ],
        pips: {
            mode: 'steps',
            density: 5,
            format: wNumb({
                decimals: 0,
                prefix: 'Year '
            })
        },
        connect: true,
        range: {
            'min': 1980,
            'max': 2020
        }
    });

    const CPopup = async () => {
        if (overlay.popup) {
            overlay.popup.remove();
        };
        let values = await mymap.getCenter();
        overlay.popup = L.popup({
                closeButton: false,
                autoClose: false,
                className: 'custom-popup',
                maxWidth: 1000
            })
            .setLatLng(values)
            .setContent('<p>Generating temperature layer. Please wait ~120 sec.</p>')
            .openOn(mymap)
            .on("remove", function() {});
    };

    const Layering = async (status) => {
        if (status) {
            addLayer(`/images/mean_changes/${overlay.fromdate}_${overlay.todate}.jpg`);
        } else {
            await CPopup();
            addLayer(`/images/mean_changes/${overlay.fromdate}_${overlay.todate}.jpg`);
        };
        overlay.image.on('load', function(handle) {
            if (overlay.popup) {
                overlay.popup.remove();
            };
        });
    };

    slider.noUiSlider.on('change', function(v, handle) {
        overlay.fromdate = Math.round(v[0]);
        overlay.todate = Math.round(v[1]);
        OverlayStatus(overlay.fromdate, overlay.todate).then(status => (Layering(status.result)));
    });
};
