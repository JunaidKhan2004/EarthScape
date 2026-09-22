from flask import Blueprint, render_template, request, jsonify

from app.weather.service import get_weather, geocode_city, KARACHI_LAT, KARACHI_LON, KARACHI_LABEL
from app.predictions.models import list_approved_for_public

public_bp = Blueprint("public", __name__, url_prefix="/")


@public_bp.route("/")
def index():
    weather = get_weather(KARACHI_LAT, KARACHI_LON, KARACHI_LABEL)
    predictions = list_approved_for_public()
    return render_template("public/index.html", weather=weather, predictions=predictions)


@public_bp.route("/api/public-weather")
def api_public_weather():
    """Looks up weather by city name (?city=) or raw coordinates (?lat=&lon=&label=)."""
    city = request.args.get("city", "").strip()
    lat_param = request.args.get("lat")
    lon_param = request.args.get("lon")

    if city:
        place = geocode_city(city)
        if place is None:
            return jsonify({"error": f'Could not find "{city}".'}), 404
        weather = get_weather(place["lat"], place["lon"], place["label"])
        return jsonify(weather)

    if lat_param and lon_param:
        try:
            lat = float(lat_param)
            lon = float(lon_param)
        except ValueError:
            return jsonify({"error": "Invalid coordinates."}), 400
        label = request.args.get("label", "Your location")
        weather = get_weather(lat, lon, label)
        return jsonify(weather)

    weather = get_weather(KARACHI_LAT, KARACHI_LON, KARACHI_LABEL)
    return jsonify(weather)
