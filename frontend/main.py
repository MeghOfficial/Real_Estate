from flask import Flask, render_template, request, jsonify
import requests
import logging
import json
from pathlib import Path

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# Your FastAPI backend URL
API_BASE = "https://real-estate-1-l00c.onrender.com/"

GENERAL_ERROR_MSG = "Something went wrong. Please try again later."
BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_LOCATIONS = {
    "Sargasan", "Kudasan", "Gift City", "Randesan", "Vavol", "Raysan", "Koba", "Kalol",
    "Pethapur", "Randheja", "Khoraj", "Uvarsad", "Chiloda", "SP Ring Road", "Sector 22",
    "Adalaj", "Gandhinagar Taluka", "Kolavada", "Sector 26", "Karai", "Sector 29",
    "SG Highway", "Dahegam", "Other", "Sector 8", "Sector 6", "Sector 11", "Sughad",
    "Valad", "Ambapur", "Sector 19", "Sector 28", "Sector 24", "Sector 21",
}

ALLOWED_AVAILABILITY = {"Ready_to_Move", "Under_Construction"}

PREDICTION_LIMITS = {
    "Area": (200, 10000, "Property area must be between 200 and 10,000 sq ft."),
    "Bedrooms": (1, 6, "Bedrooms must be between 1 and 6."),
    "Bathrooms": (1, 6, "Bathrooms must be between 1 and 6."),
    "Balconies": (0, 4, "Balconies must be between 0 and 4."),
    "Current_Floor": (0, 50, "Floor Number must be between 0 and 50."),
    "Total_Floors": (0, 50, "Total Floors in Building must be between 0 and 50."),
}


def prediction_validation_error(payload):
    for field, (minimum, maximum, message) in PREDICTION_LIMITS.items():
        value = payload[field]
        if not (minimum <= value <= maximum):
            return message
    if payload["Current_Floor"] > payload["Total_Floors"]:
        return "Floor Number cannot be greater than Total Floors in Building."
    if payload["Mapped_Area"] not in ALLOWED_LOCATIONS:
        return "Please select a valid Location."
    if not payload["Area_Type"]:
        return "Please select an Area Measurement Type."
    if payload["Property_Status"] not in ALLOWED_AVAILABILITY:
        return "Please select Availability."
    return None


def model_unknown(value):
    if value == "Not Sure":
        return "Unknown"
    return value


@app.template_filter("format_lakh_price")
def format_lakh_price(value):
    value = float(value)
    if value >= 100:
        return f"{value / 100:,.2f} Cr"
    formatted = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{formatted} L"

# ------------------------------------------------------------
# Home page
# ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ------------------------------------------------------------
# Prediction page (GET shows form, POST sends to backend)
# ------------------------------------------------------------
@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if request.method == "POST":
        try:
            payload = {
                "Area": float(request.form.get("Area", 0)),
                "Bathrooms": float(request.form.get("Bathrooms", 0)),
                "Balconies": float(request.form.get("Balconies", 0)),
                "Current_Floor": float(request.form.get("Current_Floor", 0)),
                "Total_Floors": float(request.form.get("Total_Floors", 0)),
                "Furnishing_Status": model_unknown(request.form.get("Furnishing_Status")),
                "Mapped_Area": request.form.get("Mapped_Area"),
                "Facing": model_unknown(request.form.get("Facing")),
                "Property_Age": model_unknown(request.form.get("Property_Age")),
                "Bedrooms": float(request.form.get("Bedrooms", 0)),
                "Area_Type": request.form.get("Area_Type"),
                "Property_Status": request.form.get("Property_Status"),
            }
        except ValueError:
            return render_template(
                "prediction.html",
                prediction=None,
                form_data=request.form,
                error="Please enter valid numbers for area, bedrooms, bathrooms, balconies, and floors.",
            )

        validation_error = prediction_validation_error(payload)
        if validation_error:
            return render_template(
                "prediction.html",
                prediction=None,
                form_data=payload,
                error=validation_error,
            )

        try:
            resp = requests.post(f"{API_BASE}/predict", json=payload)
            resp.raise_for_status()
            prediction = resp.json()
            return render_template("prediction.html", prediction=prediction, form_data=payload)
        except requests.exceptions.RequestException as e:
            logging.error(e)
            return render_template("error.html", message=GENERAL_ERROR_MSG)
    # GET request: show empty form
    return render_template("prediction.html", prediction=None, form_data=None)

# ------------------------------------------------------------
# Analytics page – fetches area data from backend and shows map
# ------------------------------------------------------------

# ------------------------------------------------------------
# Recommendation page
# ------------------------------------------------------------
@app.route("/recommendations")
def recommendations():
    return render_template("recommendations.html")


@app.route("/recommendations/data")
def recommendations_data():
    try:
        resp = requests.get(f"{API_BASE}/recommendations/data")
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        logging.error(e)
        return jsonify({"error": GENERAL_ERROR_MSG, "properties": [], "meta": {}}), 502


@app.route("/insights")
def insights():
    return render_template("insights.html")


@app.route("/insights/data")
def insights_data():
    try:
        resp = requests.get(f"{API_BASE}/insights/data", timeout=4)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        logging.error(e)
        try:
            data_path = BASE_DIR / "backend" / "insights_data.json"
            with data_path.open("r", encoding="utf-8") as file:
                return jsonify(json.load(file))
        except OSError as file_error:
            logging.error(file_error)
            return jsonify({"error": GENERAL_ERROR_MSG, "numerical": {}, "categorical": {}}), 502


@app.route("/data/localities")
def localities():
    try:
        resp = requests.get(f"{API_BASE}/data/localities")
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        logging.error(e)
        return jsonify({"error": GENERAL_ERROR_MSG, "localities": []}), 502


@app.route("/figures/price-area")
def price_area_figure():
    try:
        resp = requests.get(f"{API_BASE}/figures/price-area")
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        logging.error(e)
        return jsonify({"error": GENERAL_ERROR_MSG}), 502


@app.route("/figures/bhk-distribution")
def bhk_distribution_figure():
    locality = request.args.get("locality", "All")
    try:
        resp = requests.get(
            f"{API_BASE}/figures/bhk-distribution",
            params={"locality": locality},
            timeout=10,
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        logging.error(e)
        return jsonify({"error": GENERAL_ERROR_MSG}), 502


@app.route("/analytics")
def analytics():
    try:
        resp = requests.get(f"{API_BASE}/analytics/map")
        resp.raise_for_status()
        analytics_data = resp.json()
        map_figure = analytics_data.get("figure")
        expensive_areas_figure = analytics_data.get("expensive_areas_figure")
        affordable_areas_figure = analytics_data.get("affordable_areas_figure")
        locality_market_share_figure = analytics_data.get("locality_market_share_figure")
        property_status_distribution_figure = analytics_data.get("property_status_distribution_figure")
        market_segment_figures = analytics_data.get("market_segment_figures")
        market_segment_summary = analytics_data.get("market_segment_summary", [])
        bhk_price_figure = analytics_data.get("bhk_price_figure")
        bhk_distribution_figures = analytics_data.get("bhk_distribution_figures")
        property_age_price_figures = analytics_data.get("property_age_price_figures")
        area_price_scatter_figure = analytics_data.get("area_price_scatter_figure")
        market_pricing_figure = analytics_data.get("market_pricing_figure")
        market_pricing_samples = analytics_data.get("market_pricing_samples", [])
        metrics = analytics_data.get("metrics", {})
        area_comparison = analytics_data.get("area_comparison", [])
        amenities = analytics_data.get("amenities", [])
        amenities_wordcloud_image = analytics_data.get("amenities_wordcloud_image")
        nearby_wordcloud_image = analytics_data.get("nearby_wordcloud_image")
        return render_template(
            "analytics.html",
            map_figure=map_figure,
            expensive_areas_figure=expensive_areas_figure,
            affordable_areas_figure=affordable_areas_figure,
            locality_market_share_figure=locality_market_share_figure,
            property_status_distribution_figure=property_status_distribution_figure,
            market_segment_figures=market_segment_figures,
            market_segment_summary=market_segment_summary,
            bhk_price_figure=bhk_price_figure,
            bhk_distribution_figures=bhk_distribution_figures,
            property_age_price_figures=property_age_price_figures,
            area_price_scatter_figure=area_price_scatter_figure,
            market_pricing_figure=market_pricing_figure,
            market_pricing_samples=market_pricing_samples,
            metrics=metrics,
            area_comparison=area_comparison,
            amenities=amenities,
            amenities_wordcloud_image=amenities_wordcloud_image,
            nearby_wordcloud_image=nearby_wordcloud_image,
        )
    except requests.exceptions.RequestException as e:
        logging.error(e)
        # If the backend is unreachable, render the analytics page with
        # an empty dataset and an error flag so the template can show a
        # friendly message instead of a separate error page.
        return render_template(
            "analytics.html",
            map_figure=None,
            expensive_areas_figure=None,
            affordable_areas_figure=None,
            locality_market_share_figure=None,
            property_status_distribution_figure=None,
            market_segment_figures=None,
            market_segment_summary=[],
            bhk_price_figure=None,
            bhk_distribution_figures=None,
            property_age_price_figures=None,
            area_price_scatter_figure=None,
            market_pricing_figure=None,
            market_pricing_samples=[],
            metrics={},
            area_comparison=[],
            amenities=[],
            amenities_wordcloud_image=None,
            nearby_wordcloud_image=None,
            error=True,
            message=GENERAL_ERROR_MSG,
        )


# ------------------------------------------------------------
# About & Contact (simple placeholders)
# ------------------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")  # optional, you can create a simple template

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
