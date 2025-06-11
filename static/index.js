function update_forms_values(latitude, longitude) {
    const form_latitude = document.getElementById("latitude");
    const form_longitude = document.getElementById("longitude");

    //removing client validation as it would lead to a lighter wieght client
    //+ it will get checked server side
    // latitude = Math.max(Math.min(latitude,90),-90);
    // longitude = Math.max(Math.min(longitude,180),-180);

    console.log("setting latitude and longitude:  {longitude: " + longitude + ",latitude: " + latitude + "}");

    form_latitude.setAttribute("value", latitude);
    form_longitude.setAttribute("value", longitude);
}

function geoFindMe() {

    function success(position) {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        update_forms_values(latitude, longitude)
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


const submit_button = document.getElementById("submit");
const my_location_lat = document.getElementById("latitude");
const my_location_long = document.getElementById("longitude");

submit_button.addEventListener("click", async (event) => {
    event.preventDefault();
    const request_form = new FormData();
    request_form.append("latitude", parseFloat(my_location_lat.value));
    request_form.append("longitude", parseFloat(my_location_long.value));
    //JSON.stringify({"latitude":parseFloat(my_location_lat.value), "longitude":parseFloat(my_location_long.value)});
    const response = await fetch('http://127.0.0.1:5000/',
        {
            method: "POST",
            body: request_form,
        }
    );
    const data = await response.json();
    console.log("received data:", data);
    sortData(data);
    addDownloadfileButton(data);
});


//download weatherData:
//function found on https://stackoverflow.com/questions/19721439/download-json-object-as-a-file-from-browser
//top comment by 'mlimper'
function downloadObjectAsJson(exportObj){
    exportName = "weather_data.json"
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportObj));
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", exportName);
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}


//view weatherData from file:
function loadAndDisplayFromFile(fileobj){

    const reader = new FileReader();

    reader.onload = function(e) {
        var jsonData2 = JSON.parse(e.target.result);
        sortData(jsonData2)
    };
    reader.onerror = function() {
        console.error('cannot read file:', fileobj.name);
    };
    reader.readAsText(fileobj);
}

const form_elem = document.getElementsByTagName("form").item(0)
function addfileButton(){
    var fileButton = document.createElement("input")
    fileButton.type = "file"
    fileButton.id = "loadFile"
    fileButton.name = "load data"
    fileButton.accept = ".json"

    fileButton.addEventListener("change", (event) => {
        event.preventDefault();
        loadAndDisplayFromFile(event.target.files[0])
        
    })

    form_elem.appendChild(fileButton)
}
addfileButton()

function addDownloadfileButton(download_weather_data){
    if (download_weather_data){
        var downfileButtonExist = document.getElementById("Download")
        if (downfileButtonExist){
            console.log("button does exist")
            downfileButtonExist.remove()
        }
        else{
            console.log("button does not exist")
        }
        
        var downfileButton = document.createElement("input")
        downfileButton.value = "Download"
        downfileButton.id = "Download"
        downfileButton.addEventListener("click", (event) => {
            event.preventDefault();
            downloadObjectAsJson(download_weather_data)
            })
        form_elem.appendChild(downfileButton)
    }
}

geoFindMe()


function remove_prev_data(){
    var content_div = document.getElementById("content");
    if (content_div){
        //alert("removing content div")
        content_div.remove()
    }
    var bodyelem = document.getElementsByTagName("body").item(0);
    var newdiv = document.createElement("div")
    newdiv.id = "content"
    bodyelem.append(newdiv)
    console.log("adding new div")
    console.log("still in funct")
}
function sortData(weatherData) {
    remove_prev_data()
    var content = document.getElementById("content");
    for (let dayCount = 0; dayCount < 8; dayCount++) {
        const day = weatherData[dayCount];

        if (!day) {
            console.warn(`No data found for day ${dayCount}`);
            continue;
        }

        const dayDiv = document.createElement("div");

        const { avg_temp, daily_avg_visibility, precipitation_sum, weather_desc } = day;

        dayDiv.className = `day-${dayCount}`;
        dayDiv.classList.add("day");
        dayDiv.innerHTML = `
            <div class="day-header">
            <h3>Day: ${dayCount}</h3>
            </div>
            <p>Avg Temp: ${avg_temp}°F</p>
            <p>Visibility: ${daily_avg_visibility} m</p>
            <p>Precipitation: ${precipitation_sum} mm</p>
            <p>Weather: ${weather_desc}</p>
        `;

        content.appendChild(dayDiv);
    }
}