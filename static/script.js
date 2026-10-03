function getWeather() {

    const city =
        document.getElementById("cityInput")
        .value
        .trim();


    if (city === "") {

        alert("Please enter a city name.");

        return;
    }


    fetch(
        `/weather?city=${encodeURIComponent(city)}`
    )

    .then(response => response.json())

    .then(data => {

        if (data.error) {

            alert(data.error);

            return;
        }


        // --------------------------------
        // CURRENT WEATHER
        // --------------------------------

        document.getElementById("location")
            .innerText =
            `${data.city}, ${data.country}`;


        document.getElementById("temperature")
            .innerText =
            `${Math.round(data.temperature)}°C`;


        document.getElementById("condition")
            .innerText =
            data.description;


        document.getElementById("humidity")
            .innerText =
            `${data.humidity}%`;


        document.getElementById("wind")
            .innerText =
            `${(data.wind * 3.6).toFixed(1)} km/h`;


        document.getElementById("rain")
            .innerText =
            `${data.rain.toFixed(1)} mm`;


        // --------------------------------
        // CURRENT ICON
        // --------------------------------

        updateWeatherIcon(
            data.description
        );


        // --------------------------------
        // HOURLY FORECAST
        // --------------------------------

        displayHourlyForecast(
            data.hourly
        );


        // --------------------------------
        // DAILY FORECAST
        // --------------------------------

        displayDailyForecast(
            data.daily
        );


        // --------------------------------
        // HIGH / LOW
        // --------------------------------

        if (data.daily.length > 0) {

            document.getElementById("high")
                .innerText =
                `${Math.round(data.daily[0].max)}°C`;


            document.getElementById("low")
                .innerText =
                `${Math.round(data.daily[0].min)}°C`;

        }

    })

    .catch(error => {

        console.error(error);

        alert(
            "Something went wrong. Please try again."
        );

    });

}


// ==========================================
// ENTER KEY
// ==========================================

function handleEnter(event) {

    if (event.key === "Enter") {

        getWeather();

    }

}


// ==========================================
// HOURLY FORECAST
// ==========================================

function displayHourlyForecast(hourly) {

    const container =
        document.getElementById(
            "hourlyContainer"
        );


    container.innerHTML = "";


    hourly.forEach(hour => {

        const item =
            document.createElement("div");


        item.className =
            "forecast-item";


        const time =
            new Date(hour.time * 1000);


        const formattedTime =
            time.toLocaleTimeString(
                [],
                {
                    hour: "numeric",
                    minute: "2-digit"
                }
            );


        const icon =
            getWeatherEmoji(
                hour.description
            );


        item.innerHTML = `

            <span>
                ${formattedTime}
            </span>

            <span>
                ${icon}
            </span>

            <strong>
                ${Math.round(hour.temperature)}°
            </strong>

        `;


        container.appendChild(item);

    });

}


// ==========================================
// DAILY FORECAST
// ==========================================

function displayDailyForecast(daily) {

    const container =
        document.getElementById(
            "dailyContainer"
        );


    container.innerHTML = "";


    daily.forEach((day, index) => {

        const item =
            document.createElement("div");


        item.className =
            "day";


        const date =
            new Date(day.date * 1000);


        let dayName;


        if (index === 0) {

            dayName = "Today";

        } else {

            dayName =
                date.toLocaleDateString(
                    [],
                    {
                        weekday: "short"
                    }
                );

        }


        const icon =
            getWeatherEmoji(
                day.description
            );


        item.innerHTML = `

            <span>
                ${dayName}
            </span>

            <span>
                ${icon}
            </span>

            <span>
                ${Math.round(day.max)}°
                /
                ${Math.round(day.min)}°
            </span>

        `;


        container.appendChild(item);

    });

}


// ==========================================
// WEATHER EMOJI
// ==========================================

function getWeatherEmoji(description) {

    description = description.toLowerCase();

    if (description.includes("thunderstorm")) {
        return "⛈️";
    }

    if (description.includes("drizzle")) {
        return "🌦️";
    }

    if (description.includes("rain")) {
        return "🌧️";
    }

    if (description.includes("snow")) {
        return "❄️";
    }

    if (description.includes("mist") ||
        description.includes("fog") ||
        description.includes("haze")) {
        return "🌫️";
    }

    if (description.includes("cloud")) {
        return "☁️";
    }

    if (description.includes("clear")) {
        return "☀️";
    }

    return "🌤️";
}

// ==========================================
// CURRENT WEATHER ICON
// ==========================================

function updateWeatherIcon(description) {

    const icon =
        document.getElementById(
            "weatherIcon"
        );


    icon.innerText =
        getWeatherEmoji(description);

}