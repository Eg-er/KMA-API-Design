import datetime as dt
import json
import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = "ihaterussia"

WEATHER_API_TOKEN = ""

app = Flask(__name__)


def get_weather(location: str, date: str):

    today = dt.date.today();
    request_date = dt.datetime.strptime(date,"%Y-%m-%d")
    endpoint = ""

    if request_date.date() < today:
        endpoint = "past-weather"
    else:
        endpoint = "weather"

    url_base_url = f"https://api.worldweatheronline.com/premium/v1/{endpoint}.ashx"

    request_params = {
        "key": WEATHER_API_TOKEN,
        "format": "json",
        "q": location,
        "date": date
    }

    url = f"{url_base_url}"

    response = requests.request("GET", url, params = request_params)

    return json.loads(response.text)

def create_query_parameter(key: str, value: str):
    return f"&{key}={value}"

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h1>Hey, its simple weather api</h1></p>"


@app.route(
    "/api/weather",
    methods=["POST"],
)
def weather_endpoint():
    cur_date = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    if not json_data.get("location") or not json_data.get("date") or not json_data.get("requester_name"):
        raise InvalidUsage("You should have 3 required fields in body of your request: requester_name, date, location", status_code=400)

    date = json_data.get("date")
    location = json_data.get("location")
    requester = json_data.get("requester_name")

    weather = get_weather(location, date)

    weather_info = weather["data"]

    if weather_info.get("error"):
        raise InvalidUsage(weather_info["error"][0]["msg"], status_code=400)

    if not weather_info.get("weather"):
        raise InvalidUsage("Invalid date, it should be greater or equal than today or the forecast for that date is not formed yet", status_code=400)

    weather_location = weather_info["request"][0]["query"]
    weather_forecast = weather_info["weather"][0]

    result = {
        "requester_name": requester,
        "timestamp": cur_date,
        "location": weather_location,
        "date": date,
        "weather": {
            "astronomy": weather_forecast["astronomy"],
            "mintemp_c": weather_forecast["mintempC"],
            "maxtemp_c": weather_forecast["maxtempC"],
            "avgtemp_c": weather_forecast["avgtempC"],
            "totalSnow_cm": weather_forecast["totalSnow_cm"],
            "sunHour": weather_forecast["sunHour"],
            "uvIndex": weather_forecast["uvIndex"],
            "avgtemp_c": weather_forecast["avgtempC"],
            "avgtemp_c": weather_forecast["avgtempC"],
        }
    }

    return result