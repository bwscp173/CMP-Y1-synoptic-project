function update_forms_values(latitude,longitude){
    const form_latitude = document.getElementById("latitude");
    const form_longitude = document.getElementById("longitude");

    //removing client validation as it would lead to a lighter wieght client
    //+ it will get checked server side
    // latitude = Math.max(Math.min(latitude,90),-90);
    // longitude = Math.max(Math.min(longitude,180),-180);

    console.log("setting latitude and longitude:  {longitude: "+longitude+",latitude: "+latitude+"}");

    form_latitude.setAttribute("value",latitude);
    form_longitude.setAttribute("value",longitude);
}

function geoFindMe() {

    function success(position) {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        update_forms_values(latitude,longitude)
    }

    function error() {
        console.error("Unable to retrieve your location");
    }

    if (!navigator.geolocation) {
        console.error("Geolocation is not supported by your browser");
    } else {
        navigator.geolocation.getCurrentPosition(success, error);
    }
}

geoFindMe()