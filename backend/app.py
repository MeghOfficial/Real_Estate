from pathlib import Path
from typing import Annotated
import base64
import io
import json

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, model_validator
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "model_full_data.pkl"

app = FastAPI(title="Real Estate Price Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_LOCATIONS = {
    "Sargasan", "Kudasan", "Gift City", "Randesan", "Vavol", "Raysan", "Koba", "Kalol",
    "Pethapur", "Randheja", "Khoraj", "Uvarsad", "Chiloda", "SP Ring Road", "Sector 22",
    "Adalaj", "Gandhinagar Taluka", "Kolavada", "Sector 26", "Karai", "Sector 29",
    "SG Highway", "Dahegam", "Other", "Sector 8", "Sector 6", "Sector 11", "Sughad",
    "Valad", "Ambapur", "Sector 19", "Sector 28", "Sector 24", "Sector 21",
}

ALLOWED_AVAILABILITY = {"Ready_to_Move", "Under_Construction"}


class PredictRequest(BaseModel):
    Area: Annotated[float, Field(..., ge=200, le=10000)]
    Bathrooms: Annotated[float, Field(..., ge=1, le=6)]
    Balconies: Annotated[float, Field(..., ge=0, le=4)]
    Current_Floor: Annotated[float, Field(..., ge=0, le=50)]
    Total_Floors: Annotated[float, Field(..., ge=0, le=50)]
    Furnishing_Status: str
    Mapped_Area: str
    Facing: str
    Property_Age: str
    Bedrooms: Annotated[float, Field(..., ge=1, le=6)]
    Area_Type: str
    Property_Status: str

    @model_validator(mode="after")
    def validate_floor_order(self):
        if self.Current_Floor > self.Total_Floors:
            raise ValueError("Floor Number cannot be greater than Total Floors in Building.")
        if self.Mapped_Area not in ALLOWED_LOCATIONS:
            raise ValueError("Please select a valid Location.")
        if not self.Area_Type:
            raise ValueError("Please select an Area Measurement Type.")
        if self.Property_Status not in ALLOWED_AVAILABILITY:
            raise ValueError("Please select Availability.")
        return self


class PriceRange(BaseModel):
    lower: float
    upper: float


class PredictResponse(BaseModel):
    predicted_price_lakhs: float
    price_range_95_ci: PriceRange
    model_confidence: int
    price_per_sqft: float
    market_segment: str


def _load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at: {MODEL_PATH}")

    return joblib.load(MODEL_PATH)


try:
    model = _load_model()
    print("Model loaded successfully")
except Exception as e:
    print(f" {e}")
    raise


AREA_COORDS = {
    "Mapped_Area": [
        "Sargasan", "Kudasan", "Gift City", "Randesan", "Vavol", "Raysan", "Koba", "Kalol",
        "Pethapur", "Randheja", "Khoraj", "Uvarsad", "Chiloda", "SP Ring Road", "Sector 22",
        "Adalaj", "Gandhinagar Taluka", "Kolavada", "Sector 26", "Karai", "SG Highway",
        "Dahegam", "Sughad", "Valad", "Ambapur", "Sector 19", "Sector 28", "Sector 24",
        "Sector 21", "Sector 8", "Sector 6", "Sector 11", "Other",
    ],
    "Latitude": [
        23.185, 23.183, 23.166, 23.173, 23.225, 23.187, 23.145, 23.246,
        23.270, 23.298, 23.137, 23.220, 23.250, 23.120, 23.240,
        23.165, 23.216, 23.205, 23.250, 23.160, 23.080,
        23.170, 23.140, 23.290, 23.177, 23.230, 23.260, 23.245,
        23.235, 23.215, 23.205, 23.220, 23.216,
    ],
    "Longitude": [
        72.616, 72.631, 72.681, 72.646, 72.623, 72.661, 72.665, 72.497,
        72.676, 72.625, 72.579, 72.596, 72.730, 72.590, 72.670,
        72.582, 72.683, 72.590, 72.690, 72.710, 72.520,
        72.820, 72.610, 72.640, 72.592, 72.660, 72.700, 72.675,
        72.665, 72.650, 72.645, 72.655, 72.683,
    ],
}

AMENITY_COUNTS = {
    "lift": 122, "gym": 103, "clubhouse": 86, "parking": 79, "power backup": 66,
    "swimming pool": 60, "garden": 49, "security": 44, "playground": 14,
    "water supply": 12, "park": 8, "maintenance": 8, "rainwater harvesting": 6,
    "community hall": 6, "solar": 5, "electricity supply": 5, "yoga": 5,
    "home theater": 4, "cricket": 4, "badminton": 4, "air conditioning": 4,
    "indoor games": 3, "modular kitchen": 3, "table tennis": 3, "fire safety": 3,
    "library": 3, "gated community": 3, "gas": 2, "office": 2, "conference room": 2,
    "water body": 2, "shopping center": 2, "cctv": 2, "cafe": 2, "indoor play area": 2,
    "tennis": 2, "pic and drop facility": 1, "wardrobes": 1, "fans": 1,
    "water heater": 1, "power back-up": 1, "mini golf": 1, "squash": 1,
    "walking track": 1, "sky lounge": 1, "leisure zone": 1, "jogging track": 1,
    "temple": 1, "business center": 1, "sports facilities": 1, "rooftop": 1,
    "grocery": 1, "outdoor play area": 1, "banquet hall": 1, "24x7 water": 1,
    "carom": 1, "chess": 1, "24 hours water": 1,
}

NEARBY_COUNTS = {
    "hospital": 228, "school": 190, "metro": 115, "mall": 93, "temple": 93,
    "highway": 89, "market": 51, "gift city": 29, "office": 20, "clinic": 15,
    "university": 12, "railway": 11, "road": 10, "randheja railway station": 6,
    "airport": 5, "garden": 5, "bus": 5, "gandhinagar": 4, "atm": 4,
    "key religious sites": 4, "shop": 4, "bank": 4, "gym": 4, "college": 4,
    "pdpu road": 3, "cinema": 3, "reliance circle": 2, "kalol": 2, "several": 2,
    "hotel": 2, "pethapur": 2, "club": 2, "park": 2, "key healthcare centers": 2,
    "mahatma mandir": 2, "petrol pump": 2, "riverfront": 2, "health focus clinic": 2,
    "key connectivity points": 1, "cuty pulse cinema": 1, "swaminarayan kanyashala": 1,
    "clubhouse": 1, "sanjari park": 1, "railways": 1, "bus depots": 1,
    "key healthcare facilities": 1, "shoppers plaza": 1, "nh147": 1,
    "multiple religious sites": 1, "adalaj petrol pump": 1, "daiict": 1,
    "rickshaw stand": 1, "sbi bank": 1, "city bus stand": 1, "science city circle": 1,
    "vavol pundrasan road": 1, "urjanagar 1 area": 1, "sargasan cross road": 1,
    "d' mart": 1, "infocity area": 1, "national institute of design road": 1,
    "kh road": 1, "rever": 1, "healthcare": 1, "key medical facilities": 1,
    "connectivity hubs": 1, "religious site": 1, "bus port": 1, "health clinics": 1,
    "city": 1, "sikshapatri road": 1, "vaishnodevi circle": 1, "nh 48 connectivity": 1,
    "hotels": 1, "gardens": 1, "health facilities": 1, "medical clinics": 1,
    "vavol": 1, "vavol uvarsad road": 1, "vadsar airforce station": 1,
    "arvind mills campus": 1, "fuel": 1, "pdpu university": 1,
    "gandhinagar railway station": 1, "petrolpump": 1, "parking": 1,
    "transport hubs": 1, "theatre": 1, "bus station": 1,
    "alampur shardha recidency": 1, "chiloda road": 1, "main bus stand": 1,
    "including shree maha": 1, "transportation": 1, "aloha hills resort": 1,
    "ahmedabad": 1, "key connectivity routes": 1, "banking facilities": 1,
    "d-mart": 1, "capital railway station": 1,
}

MARKET_SEGMENT_RULES = {
    2: {
        "affordable": "Below Rs. 50 L",
        "premium": "Rs. 50 L - Rs. 69 L",
        "luxury": "Above Rs. 69 L",
        "affordable_max": 50e5,
        "premium_max": 69e5,
    },
    3: {
        "affordable": "Below Rs. 79.45 L",
        "premium": "Rs. 79.45 L - Rs. 120 L",
        "luxury": "Above Rs. 120 L",
        "affordable_max": 79.45e5,
        "premium_max": 120e5,
    },
    4: {
        "affordable": "Below Rs. 165 L",
        "premium": "Rs. 165 L - Rs. 250 L",
        "luxury": "Above Rs. 250 L",
        "affordable_max": 165e5,
        "premium_max": 250e5,
    },
}


def _analytics_group_df() -> pd.DataFrame:
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)

    df_coords = pd.DataFrame(AREA_COORDS)
    new_df = df.merge(df_coords, on="Mapped_Area", how="inner")
    new_df["Price_inr"] = new_df["Price"] * 100000
    new_df["Price_per_SqFt"] = new_df["Price_inr"] / new_df["Area"]

    group_df = new_df.groupby("Mapped_Area").agg({
        "Price": "mean",
        "Area": "mean",
        "Price_per_SqFt": "mean",
        "Latitude": "first",
        "Longitude": "first",
    }).reset_index()

    return group_df.dropna(subset=["Latitude", "Longitude"])


def _analytics_metrics() -> dict:
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    price_per_sqft = df["Price"] * 100000 / df["Area"]

    return {
        "average_price": round(float(df["Price"].mean()), 2),
        "median_price": round(float(df["Price"].median()), 2),
        "total_property": int(len(df)),
        "unique_locations": int(df["Mapped_Area"].nunique()),
        "average_price_per_sqft": round(float(price_per_sqft.mean()), 0),
        "median_price_per_sqft": round(float(price_per_sqft.median()), 0),
        "ready_to_move_percentage": round(float((df["Property_Status"] == "Ready_to_Move").mean() * 100), 2),
    }


def _area_comparison_summary() -> list[dict]:
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    df["price_inr"] = df["Price"] * 100000
    df["price_per_sqft"] = df["price_inr"] / df["Area"]

    area_summary = df.groupby("Mapped_Area").agg(
        avg_price_lakhs=("Price", "mean"),
        avg_price_per_sqft=("price_per_sqft", "mean"),
        avg_area=("Area", "mean"),
        count=("Price", "count"),
    ).round(2).reset_index()

    area_summary = area_summary.sort_values("Mapped_Area")

    return [
        {
            "mapped_area": str(row["Mapped_Area"]),
            "avg_price_lakhs": float(row["avg_price_lakhs"]),
            "avg_price_per_sqft": float(row["avg_price_per_sqft"]),
            "avg_area": float(row["avg_area"]),
            "count": int(row["count"]),
        }
        for _, row in area_summary.iterrows()
    ]


def _recommendation_data() -> dict:
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_recommender_ready.csv"
    df = pd.read_csv(data_path).reset_index(names="id")

    numeric_columns = [
        "price_inr_in_lakhs", "area_sqft", "bedrooms", "bathrooms",
        "balconies", "current_floor", "total_floors",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["property_type"] = df["property_type"].fillna("unknown").astype(str).str.lower()
    df["property_status"] = df["property_status"].fillna("Unknown")
    df["area_type"] = df["area_type"].fillna("Super Built-up")
    df["furnishing_status"] = df["furnishing_status"].fillna("Unknown")
    df["mapped_area"] = df["mapped_area"].fillna("Unknown")
    df["facing"] = df["facing"].fillna("Unknown")
    df["property_age"] = df["property_age"].fillna("Unknown")
    df["description"] = df["description"].fillna("No description available.")
    df["property_url"] = df["property_url"].fillna("#")
    df = df.dropna(subset=["price_inr_in_lakhs", "area_sqft", "bedrooms"])

    def clean_option(value):
        if pd.isna(value):
            return "Unknown"
        return str(value).replace("_", " ").strip()

    def floor_category(current, total):
        if pd.isna(current) or pd.isna(total) or total == 0:
            return "Any Floor"
        ratio = current / total
        if ratio <= 0.25:
            return "Lower Floor"
        if ratio <= 0.5:
            return "Mid Floor"
        if ratio <= 0.75:
            return "Higher Floor"
        return "Top Floor"

    properties = []
    for _, row in df.iterrows():
        price = float(row["price_inr_in_lakhs"]) if pd.notna(row["price_inr_in_lakhs"]) else 0
        area = float(row["area_sqft"]) if pd.notna(row["area_sqft"]) else 0
        current_floor = float(row["current_floor"]) if pd.notna(row["current_floor"]) else 0
        total_floors = float(row["total_floors"]) if pd.notna(row["total_floors"]) else 0
        properties.append({
            "id": int(row["id"]),
            "location": clean_option(row["location"]),
            "locality": clean_option(row["mapped_area"]),
            "price_lakhs": round(price, 2),
            "area_sqft": round(area, 0),
            "bedrooms": int(row["bedrooms"]) if pd.notna(row["bedrooms"]) else 0,
            "bathrooms": int(row["bathrooms"]) if pd.notna(row["bathrooms"]) else 0,
            "balconies": int(row["balconies"]) if pd.notna(row["balconies"]) else 0,
            "current_floor": int(current_floor),
            "total_floors": int(total_floors),
            "furnishing_status": clean_option(row["furnishing_status"]),
            "facing": clean_option(row["facing"]),
            "property_age": clean_option(row["property_age"]),
            "property_type": clean_option(row["property_type"]),
            "area_type": clean_option(row["area_type"]),
            "property_status": clean_option(row["property_status"]),
            "floor_category": floor_category(current_floor, total_floors),
            "description": str(row["description"]),
            "property_url": str(row["property_url"]),
            "price_per_sqft": round((price * 100000 / area), 0) if area else 0,
        })

    def options(column):
        values = [clean_option(value) for value in df[column].dropna().unique()]
        return sorted(values, key=lambda value: value.lower())

    prices = [item["price_lakhs"] for item in properties]
    areas = [item["area_sqft"] for item in properties]
    return {
        "properties": properties,
        "meta": {
            "price_min": min(prices) if prices else 0,
            "price_max": max(prices) if prices else 0,
            "area_min": min(areas) if areas else 0,
            "area_max": max(areas) if areas else 0,
            "locations": [area for area, _ in df["mapped_area"].value_counts().items()],
            "bedrooms": sorted({item["bedrooms"] for item in properties if item["bedrooms"]}),
            "bathrooms": sorted({item["bathrooms"] for item in properties if item["bathrooms"]}),
            "balconies": sorted({item["balconies"] for item in properties if item["balconies"]}),
            "property_status": options("property_status"),
            "area_type": options("area_type"),
            "property_age": options("property_age"),
            "furnishing_status": options("furnishing_status"),
        },
    }


def _amenities_summary() -> list[dict]:
    return [
        {"name": name.title(), "count": count}
        for name, count in sorted(AMENITY_COUNTS.items(), key=lambda item: item[1], reverse=True)
    ]


def _amenities_wordcloud_image() -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from wordcloud import WordCloud
    except Exception:
        return None

    log_freq = {word: np.log1p(count) for word, count in AMENITY_COUNTS.items()}
    bg_color = "#1e1e2f"

    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color=bg_color,
        colormap="viridis",
        max_words=80,
        relative_scaling=0.5,
        contour_width=1,
        contour_color="white",
        random_state=42,
    ).generate_from_frequencies(log_freq)

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("white")
        spine.set_linewidth(0.5)
    plt.title(
        "🏠 Amenities Word Cloud (balanced)",
        fontsize=20,
        fontweight="bold",
        color="white",
        pad=20,
        backgroundcolor=bg_color,
    )
    plt.tight_layout(pad=0)

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight", pad_inches=0, facecolor=bg_color)
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _nearby_wordcloud_image() -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from wordcloud import WordCloud
    except Exception:
        return None

    log_nearby_freq = {word: np.log1p(count) for word, count in NEARBY_COUNTS.items()}
    bg_color = "#1e1e2f"

    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color=bg_color,
        colormap="plasma",
        max_words=120,
        relative_scaling=0.5,
        contour_width=1,
        contour_color="white",
        random_state=42,
    ).generate_from_frequencies(log_nearby_freq)

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("white")
        spine.set_linewidth(0.5)
    plt.title(
        "📍 Nearby Facilities Word Cloud (balanced)",
        fontsize=20,
        fontweight="bold",
        color="white",
        pad=20,
        backgroundcolor=bg_color,
    )
    plt.tight_layout(pad=0)

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight", pad_inches=0, facecolor=bg_color)
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _analytics_map_figure(group_df: pd.DataFrame):
    fig = px.scatter_mapbox(
        group_df,
        lat="Latitude",
        lon="Longitude",
        size="Area",
        color="Price_per_SqFt",
        hover_name="Mapped_Area",
        hover_data={
            "Price": ":.1f",
            "Area": ":.0f",
            "Price_per_SqFt": ":.0f",
            "Latitude": False,
            "Longitude": False,
        },
        color_continuous_scale="Viridis",
        zoom=11,
        height=600,
        mapbox_style="carto-darkmatter",
        text="Mapped_Area",
        size_max=35,
    )

    fig.update_traces(
        marker=dict(opacity=0.8),
        textfont=dict(color="#bbbbbb", size=9),
    )
    fig.update_layout(
        mapbox=dict(center=dict(lat=23.20, lon=72.65)),
        margin=dict(l=0, r=92, t=0, b=24),
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        coloraxis_colorbar=dict(
            title=dict(text="Price / SqFt", font=dict(color="#d1d5db")),
            tickprefix="Rs. ",
            tickfont=dict(color="#d1d5db"),
            x=1.0,
            xanchor="left",
            y=0.5,
            yanchor="middle",
            len=0.86,
            thickness=18,
        ),
        font=dict(color="#e5e7eb"),
    )
    return fig


def _expensive_areas_figure():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    df["price_inr"] = df["Price"] * 100000
    df["price_per_sqft"] = df["price_inr"] / df["Area"]

    area_avg = df.groupby("Mapped_Area")["price_per_sqft"].mean().reset_index()
    area_avg = area_avg.sort_values("price_per_sqft", ascending=False).head(10)

    fig = px.bar(
        area_avg,
        x="price_per_sqft",
        y="Mapped_Area",
        orientation="h",
        title="Top 10 Most Expensive Areas",
        labels={
            "price_per_sqft": "Average Price per sq.ft. (Rs.)",
            "Mapped_Area": "",
        },
        color="price_per_sqft",
        color_continuous_scale="Reds",
        text="price_per_sqft",
        height=500,
    )

    fig.update_traces(
        texttemplate="Rs. %{text:.0f}",
        textposition="outside",
        cliponaxis=False,
    )
    max_price_per_sqft = float(area_avg["price_per_sqft"].max())
    fig.update_layout(
        margin=dict(l=0, r=150, t=52, b=0),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title=dict(font=dict(color="#0f172a", size=20)),
        xaxis=dict(range=[0, max_price_per_sqft * 1.45]),
        yaxis=dict(autorange="reversed"),
        coloraxis_colorbar=dict(
            title=dict(text="Avg Rs./SqFt"),
        ),
    )
    return fig


def _affordable_areas_figure():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    df["price_inr"] = df["Price"] * 100000
    df["price_per_sqft"] = df["price_inr"] / df["Area"]

    area_avg = df.groupby("Mapped_Area")["price_per_sqft"].mean().reset_index()
    area_avg = area_avg.sort_values("price_per_sqft", ascending=True).head(10)

    fig = px.bar(
        area_avg,
        x="price_per_sqft",
        y="Mapped_Area",
        orientation="h",
        title="Top 10 Most Affordable Areas",
        labels={
            "price_per_sqft": "Average Price per sq.ft. (Rs.)",
            "Mapped_Area": "",
        },
        color="price_per_sqft",
        color_continuous_scale="Greens_r",
        text="price_per_sqft",
        height=500,
    )

    fig.update_traces(
        texttemplate="Rs. %{text:.0f}",
        textposition="outside",
        cliponaxis=False,
    )
    max_price_per_sqft = float(area_avg["price_per_sqft"].max())
    fig.update_layout(
        margin=dict(l=0, r=150, t=52, b=0),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title=dict(font=dict(color="#0f172a", size=20)),
        xaxis=dict(range=[0, max_price_per_sqft * 1.45]),
        coloraxis_colorbar=dict(
            title=dict(text="Avg Rs./SqFt"),
        ),
    )
    return fig


def _locality_market_share_figure():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)

    locality_counts = df["Mapped_Area"].value_counts().reset_index()
    locality_counts.columns = ["Locality", "Property_Count"]
    total_properties = int(len(df))
    locality_counts["Percentage"] = (locality_counts["Property_Count"] / total_properties) * 100

    top10 = locality_counts.head(10).copy()
    other_count = total_properties - int(top10["Property_Count"].sum())

    pie_labels = list(top10["Locality"]) + ["Other"]
    pie_values = list(top10["Property_Count"]) + [other_count]

    max_val = max(pie_values) if pie_values else 1
    norm_values = [value / max_val for value in pie_values]
    colors = px.colors.sample_colorscale(
        "Blues",
        samplepoints=norm_values,
        low=0.2,
        high=1.0,
        colortype="rgb",
    )

    fig = go.Figure(data=[go.Pie(
        labels=pie_labels,
        values=pie_values,
        textinfo="label+percent",
        insidetextorientation="radial",
        marker=dict(colors=colors),
        hole=0.4,
        sort=False,
    )])
    fig.update_layout(
        title="Property Distribution by Locality (Top 10 vs Others)",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title_font=dict(color="#0f172a", size=20),
        showlegend=False,
    )

    return fig


def _property_status_distribution_figure():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)

    status_counts = df["Property_Status"].value_counts().reset_index()
    status_counts.columns = ["Property_Status", "Count"]
    status_counts["Display_Status"] = status_counts["Property_Status"].astype(str).str.replace("_", " ").str.title()
    total = int(status_counts["Count"].sum())
    status_counts["Percentage"] = (status_counts["Count"] / total * 100).round(1)

    color_map = {
        "Ready To Move": "#2ecc71",
        "Under Construction": "#e74c3c",
    }

    fig = px.bar(
        status_counts,
        x="Display_Status",
        y="Count",
        text="Count",
        color="Display_Status",
        color_discrete_map=color_map,
        title="Property Status Distribution",
        labels={"Count": "Number of Properties", "Display_Status": ""},
        height=500,
        custom_data=["Percentage"],
    )
    fig.update_traces(
        texttemplate="%{text}<br>(%{customdata[0]:.1f}%)",
        textposition="outside",
        marker_line_width=1,
        marker_line_color="white",
        hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Percentage: %{customdata[0]:.1f}%<extra></extra>",
        cliponaxis=False,
    )
    max_count = float(status_counts["Count"].max()) if not status_counts.empty else 0
    fig.update_layout(
        height=500,
        showlegend=False,
        margin=dict(l=50, r=24, t=58, b=48),
        xaxis=dict(tickangle=0),
        yaxis=dict(gridcolor="lightgray", gridwidth=0.5, range=[0, max_count * 1.22 if max_count else 1]),
        plot_bgcolor="white",
        paper_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title=dict(font=dict(size=20, family="Arial", color="#2c3e50")),
    )

    return fig


def _market_segment_figures():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    df["Bedrooms"] = df["Bedrooms"].astype(int)
    df["Price_inr"] = df["Price"] * 100000

    def segment(row):
        bhk = row["Bedrooms"]
        price = row["Price_inr"]
        rule = MARKET_SEGMENT_RULES.get(bhk)
        if rule:
            if price < rule["affordable_max"]:
                return "Affordable"
            if price <= rule["premium_max"]:
                return "Premium"
            return "Luxury"
        return None

    df["Segment"] = df.apply(segment, axis=1)
    df = df[df["Bedrooms"].isin([2, 3, 4])].dropna(subset=["Segment"])

    segment_order = ["Affordable", "Premium", "Luxury"]
    colors = {
        "Affordable": "#2ecc71",
        "Premium": "#f39c12",
        "Luxury": "#e74c3c",
    }

    def build_figure(data: pd.DataFrame, title_suffix: str):
        counts = data["Segment"].value_counts().reindex(segment_order).fillna(0)

        fig = make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "domain"}, {"type": "xy"}]],
            horizontal_spacing=0.12,
        )

        fig.add_trace(
            go.Pie(
                labels=segment_order,
                values=counts.values,
                marker=dict(colors=[colors[name] for name in segment_order]),
                hole=0.35,
                textinfo="label+percent",
                sort=False,
            ),
            row=1,
            col=1,
        )

        for segment_name in segment_order:
            segment_data = data[data["Segment"] == segment_name]
            fig.add_trace(
                go.Box(
                    x=[segment_name] * len(segment_data),
                    y=segment_data["Price"],
                    name=segment_name,
                    marker_color=colors[segment_name],
                    boxpoints=False,
                    showlegend=False,
                ),
                row=1,
                col=2,
            )

        fig.update_layout(
            height=500,
            margin=dict(l=42, r=32, t=42, b=48),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(color="#334155"),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        )
        fig.update_xaxes(
            title_text="Price Segment",
            showline=True,
            linecolor="#94a3b8",
            linewidth=1,
            showgrid=True,
            gridcolor="#e2e8f0",
            mirror=True,
            row=1,
            col=2,
        )
        fig.update_yaxes(
            title_text="Price (Rs. Lakhs)",
            tickprefix="Rs. ",
            showline=True,
            linecolor="#94a3b8",
            linewidth=1,
            showgrid=True,
            gridcolor="#e2e8f0",
            zeroline=True,
            zerolinecolor="#cbd5e1",
            mirror=True,
            row=1,
            col=2,
        )
        return fig

    figures = {
        "all": build_figure(df, "All BHKs Combined"),
        "2": build_figure(df[df["Bedrooms"] == 2], "2 BHK Only"),
        "3": build_figure(df[df["Bedrooms"] == 3], "3 BHK Only"),
        "4": build_figure(df[df["Bedrooms"] == 4], "4 BHK Only"),
    }

    return {key: json.loads(pio.to_json(fig)) for key, fig in figures.items()}


def _market_segment_summary() -> list[dict]:
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    df["Bedrooms"] = df["Bedrooms"].astype(int)
    df["Price_inr"] = df["Price"] * 100000
    summary = []

    for bhk, rule in MARKET_SEGMENT_RULES.items():
        bhk_df = df[df["Bedrooms"] == bhk]
        affordable_count = int((bhk_df["Price_inr"] < rule["affordable_max"]).sum())
        premium_count = int(
            (
                (bhk_df["Price_inr"] >= rule["affordable_max"])
                & (bhk_df["Price_inr"] <= rule["premium_max"])
            ).sum()
        )
        luxury_count = int((bhk_df["Price_inr"] > rule["premium_max"]).sum())

        summary.append({
            "bhk": int(bhk),
            "affordable_rule": rule["affordable"],
            "premium_rule": rule["premium"],
            "luxury_rule": rule["luxury"],
            "affordable_count": affordable_count,
            "premium_count": premium_count,
            "luxury_count": luxury_count,
            "total_count": affordable_count + premium_count + luxury_count,
        })

    return summary


def _bhk_price_figure():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    # Prepare BHK categories and convert price to Crore for nicer labels
    df = df.dropna(subset=["Bedrooms", "Price"]).copy()
    df["Bedrooms"] = df["Bedrooms"].astype(int)
    df["BHK"] = df["Bedrooms"].apply(lambda x: f"{int(x)} BHK" if x < 4 else "4+ BHK")
    df["Price_Lakhs"] = df["Price"]  # Price already in lakhs

    order = ["1 BHK", "2 BHK", "3 BHK", "4+ BHK"]

    # Mean figure
    mean_df = df.groupby("BHK", as_index=False)["Price_Lakhs"].mean()
    mean_df["BHK"] = pd.Categorical(mean_df["BHK"], categories=order, ordered=True)
    mean_df = mean_df.sort_values("BHK")

    fig_mean = px.bar(
        mean_df,
        x="BHK",
        y="Price_Lakhs",
        text="Price_Lakhs",
        color="Price_Lakhs",
        color_continuous_scale="Blues",
        title="Average Property Price by BHK Type",
        labels={"Price_Lakhs": "Price (₹ Lakhs)", "BHK": "BHK Type"},
        height=450,
    )
    fig_mean.update_traces(texttemplate='₹%{text:.0f}L', textposition='outside', marker_line_width=0)
    max_price = float(mean_df["Price_Lakhs"].max()) if not mean_df.empty else 0
    fig_mean.update_layout(
        yaxis=dict(
            tickprefix='₹',
            tickformat='.0f',
            title='Price (₹ Lakhs)',
            range=[0, max_price * 1.18 if max_price else 1],
            gridcolor="#e2e8f0",
            showgrid=True,
        ),
        xaxis=dict(
            title='BHK Type',
            categoryorder='array',
            categoryarray=order,
            gridcolor="#f1f5f9",
            showgrid=True,
        ),
        margin=dict(l=50, r=32, t=52, b=48),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title=dict(font=dict(color="#0f172a", size=20), x=0.05, xanchor='left'),
        coloraxis_showscale=False,
    )

    # Median figure
    median_df = df.groupby("BHK", as_index=False)["Price_Lakhs"].median()
    median_df["BHK"] = pd.Categorical(median_df["BHK"], categories=order, ordered=True)
    median_df = median_df.sort_values("BHK")

    fig_median = px.bar(
        median_df,
        x="BHK",
        y="Price_Lakhs",
        text="Price_Lakhs",
        color="Price_Lakhs",
        color_continuous_scale="Blues",
        title="Average Property Price by BHK Type",
        labels={"Price_Lakhs": "Price (₹ Lakhs)", "BHK": "BHK Type"},
        height=450,
    )
    fig_median.update_traces(texttemplate='₹%{text:.0f}L', textposition='outside', marker_line_width=0)
    max_price_m = float(median_df["Price_Lakhs"].max()) if not median_df.empty else 0
    fig_median.update_layout(
        yaxis=dict(
            tickprefix='₹',
            tickformat='.0f',
            title='Price (₹ Lakhs)',
            range=[0, max_price_m * 1.18 if max_price_m else 1],
            gridcolor="#e2e8f0",
            showgrid=True,
        ),
        xaxis=dict(
            title='BHK Type',
            categoryorder='array',
            categoryarray=order,
            gridcolor="#f1f5f9",
            showgrid=True,
        ),
        margin=dict(l=50, r=32, t=52, b=48),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title=dict(font=dict(color="#0f172a", size=20), x=0.05, xanchor='left'),
        coloraxis_showscale=False,
    )

    return {
        "mean": json.loads(pio.to_json(fig_mean)),
        "median": json.loads(pio.to_json(fig_median)),
    }


def _property_age_price_figures():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    age_order = ["New", "1-5 years", "5-10 years", "10-20 years"]
    df_age = df[df["Property_Age"].isin(age_order)].copy()
    df_age["BHK_category"] = df_age["Bedrooms"].apply(
        lambda value: f"{int(value)} BHK" if value < 4 else "4+ BHK"
    )

    def build_figure(filtered_df: pd.DataFrame, bhk_filter: str):
        summary_age = filtered_df.groupby("Property_Age", as_index=False).agg(
            avg_price_lakhs=("Price", "mean"),
            count=("Price", "count"),
        )
        summary_age["Property_Age"] = pd.Categorical(
            summary_age["Property_Age"],
            categories=age_order,
            ordered=True,
        )
        summary_age = summary_age.sort_values("Property_Age")

        fig = px.bar(
            summary_age,
            x="Property_Age",
            y="avg_price_lakhs",
            color="avg_price_lakhs",
            color_continuous_scale="YlOrRd",
            title="Average Property Price by Property Age",
            labels={
                "avg_price_lakhs": "Price (₹ Lakhs)",
                "Property_Age": "Property Age",
            },
            height=500,
        )

        max_price = float(summary_age["avg_price_lakhs"].max()) if not summary_age.empty else 0
        fig.update_traces(
            text=None,
            textposition=None,
            marker_line_width=0,
        )
        fig.update_layout(
            yaxis=dict(
                tickformat=",.0f",
                title="Price (₹ Lakhs)",
                range=[0, max_price * 1.18 if max_price else 1],
                gridcolor="#e2e8f0",
                showgrid=True,
            ),
            xaxis=dict(
                categoryorder="array",
                categoryarray=age_order,
                title="Property Age",
                gridcolor="#f1f5f9",
                showgrid=True,
            ),
            margin=dict(l=54, r=82, t=56, b=52),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(color="#334155"),
            title=dict(font=dict(color="#0f172a", size=20), x=0.05, xanchor='left'),
            showlegend=False,
            coloraxis_showscale=False,
            uniformtext_minsize=10,
        )
        return fig

    bhk_options = ["All"] + sorted(df_age["BHK_category"].dropna().unique())
    figures = {}
    for bhk_filter in bhk_options:
        filtered_df = df_age if bhk_filter == "All" else df_age[df_age["BHK_category"] == bhk_filter]
        figures[bhk_filter] = json.loads(pio.to_json(build_figure(filtered_df, bhk_filter)))

    return figures


def _area_price_scatter_figure():
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    df = df.dropna(
        subset=[
            "Area",
            "Price",
            "Bedrooms",
            "Mapped_Area",
            "Furnishing_Status",
            "Facing",
            "Property_Status",
        ]
    )
    df["Bedrooms"] = df["Bedrooms"].astype(int)
    df = df[df["Bedrooms"].between(1, 6)]
    df["Bedrooms"] = df["Bedrooms"].astype(str)

    fig = px.scatter(
        df,
        x="Area",
        y="Price",
        color="Bedrooms",
        title="Price vs. Area by Bedroom Count",
        labels={
            "Area": "Area (sq ft)",
            "Price": "Price (Rs. in lakhs)",
            "Bedrooms": "Bedrooms",
        },
        hover_data=["Mapped_Area", "Furnishing_Status", "Facing", "Property_Status"],
        opacity=0.8,
        height=520,
        category_orders={"Bedrooms": ["1", "2", "3", "4", "5", "6"]},
    )

    # Ensure a clean layout for embedding and enable grid lines similar to BHK chart
    max_area = float(df["Area"].max()) if not df.empty else 0
    max_price = float(df["Price"].max()) if not df.empty else 0

    fig.update_layout(
        height=620,
        margin=dict(l=40, r=24, t=56, b=120),
        title_x=0.02,
        title_xanchor='left',
        xaxis_title="Area (sq ft)",
        yaxis_title="Price (Rs. in lakhs)",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title=dict(font=dict(color="#0f172a", size=20), x=0.02, xanchor='left'),
        xaxis=dict(
            showline=True,
            linecolor="#94a3b8",
            linewidth=1,
            showgrid=True,
            gridcolor="#e2e8f0",
            zeroline=False,
            range=[0, max_area * 1.02],
            automargin=True,
            title_standoff=24,
        ),
        yaxis=dict(
            showline=True,
            linecolor="#94a3b8",
            linewidth=1,
            showgrid=True,
            gridcolor="#e2e8f0",
            zeroline=False,
            range=[0, max_price * 1.08],
            automargin=True,
            title_standoff=24,
        ),
    )

    return fig


def _bhk_distribution_figure(locality: str = "All"):
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["Bedrooms"]).copy()
    df["Bedrooms"] = df["Bedrooms"].astype(int)
    df["BHK"] = df["Bedrooms"].apply(lambda x: f"{int(x)} BHK" if x < 4 else "4+ BHK")

    if locality and locality != "All":
        df = df[df["Mapped_Area"] == locality]

    order = ["1 BHK", "2 BHK", "3 BHK", "4+ BHK"]
    bhk_counts = df["BHK"].value_counts().reindex(order, fill_value=0).reset_index()
    bhk_counts.columns = ["BHK", "count"]

    fig = px.pie(
        bhk_counts,
        values="count",
        names="BHK",
        color="BHK",
        color_discrete_sequence=px.colors.sequential.Greens_r,
        hole=0.3,
        height=480,
    )
    fig.update_traces(textposition='inside', textinfo='percent+label', textfont=dict(color='white', size=12))
    fig.update_layout(margin=dict(l=12, r=12, t=20, b=12), title=None)
    return fig


@app.get("/figures/price-area", response_class=JSONResponse)
def get_price_area_figure():
    try:
        fig = _area_price_scatter_figure()
        return JSONResponse(content=json.loads(pio.to_json(fig)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/figures/bhk-distribution", response_class=JSONResponse)
def get_bhk_distribution(locality: str = "All"):
    try:
        fig = _bhk_distribution_figure(locality)
        return JSONResponse(content=json.loads(pio.to_json(fig)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/figures/bhk-price", response_class=JSONResponse)
def get_bhk_price_figure():
    try:
        return JSONResponse(content=_bhk_price_figure())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/localities", response_class=JSONResponse)
def get_localities():
    try:
        PROJECT_ROOT = BASE_DIR.parent
        data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv" 
        df = pd.read_csv(data_path)
        localities = sorted(df["Mapped_Area"].dropna().unique().tolist())
        return JSONResponse(content={"localities": localities})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _format_price_lakh(value: float) -> str:
    if value >= 100:
        return f"₹{value / 100:.2f}Cr"
    return f"₹{value:.0f}L"


def _market_pricing_analysis():
    if model is None:
        return None, []
    
    PROJECT_ROOT = BASE_DIR.parent
    data_path = PROJECT_ROOT / "data" / "gandhinagar_property_apartments_final.csv"

    df = pd.read_csv(data_path)
    feature_columns = [
        "Area",
        "Bathrooms",
        "Balconies",
        "Current_Floor",
        "Total_Floors",
        "Bedrooms",
        "Mapped_Area",
        "Property_Age",
        "Furnishing_Status",
        "Area_Type",
        "Property_Status",
        "Facing",
    ]
    df_eval = df.dropna(subset=feature_columns + ["Price"]).copy()
    if df_eval.empty:
        return None, []

    pred_log = model.predict(df_eval[feature_columns])
    df_eval["Predicted_Lakh"] = np.expm1(pred_log)
    df_eval["Deviation_Pct"] = (
        (df_eval["Price"] - df_eval["Predicted_Lakh"]) / df_eval["Predicted_Lakh"] * 100
    )

    def classify(dev: float) -> str:
        if dev < -10:
            return "Below Estimated Value"
        if dev > 10:
            return "Above Estimated Value"
        return "Near Estimated Value"

    df_eval["Valuation"] = df_eval["Deviation_Pct"].apply(classify)
    category_order = ["Below Estimated Value", "Near Estimated Value", "Above Estimated Value"]
    dist = df_eval["Valuation"].value_counts().reindex(category_order, fill_value=0)

    fig = go.Figure(data=[go.Pie(
        labels=dist.index,
        values=dist.values,
        hole=0.45,
        marker=dict(
            colors=["#1e88e5", "#ffb300", "#e53935"],
            line=dict(color="white", width=2),
        ),
        textinfo="label+percent",
        textposition="auto",
        textfont=dict(size=13, color="black"),
        pull=[0.05, 0, 0.05],
        sort=False,
    )])
    fig.update_layout(
        title=dict(
            text="Market Pricing Distribution",
            font=dict(size=22),
            x=0.0,
            xanchor="left",
        ),
        height=500,
        width=700,
        margin=dict(l=40, r=40, t=80, b=40),
        annotations=[dict(
            text=f"Total<br>{len(df_eval)}",
            x=0.5,
            y=0.5,
            font=dict(size=16, color="#2c3e50"),
            showarrow=False,
        )],
        showlegend=False,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#334155"),
    )

    sample_specs = [
        ("Below Estimated Value", "undervalued", "below"),
        ("Above Estimated Value", "overpriced", "above"),
        ("Near Estimated Value", "Fair value", "near"),
    ]
    samples = []
    for category, label, status in sample_specs:
        category_df = df_eval[df_eval["Valuation"] == category]
        if category_df.empty:
            continue
        sample_index = 0
        if category == "Below Estimated Value":
            sample_index = 1
        elif category == "Near Estimated Value":
            sample_index = 2
        if len(category_df) <= sample_index:
            sample_index = 0
        row = category_df.iloc[sample_index]
        abs_dev = abs(float(row["Deviation_Pct"]))
        badge = label if status == "near" else f"{abs_dev:.0f}% {label}"
        samples.append({
            "category": category,
            "status": status,
            "badge": badge,
            "headline": f"{int(row['Bedrooms'])}BHK · {row['Mapped_Area']} · {float(row['Area']):,.0f} sq ft",
            "listed": _format_price_lakh(float(row["Price"])),
            "predicted": _format_price_lakh(float(row["Predicted_Lakh"])),
        })

    return json.loads(pio.to_json(fig)), samples


@app.get("/")
def home():
    return {
        "message": "Real Estate API Running"
    }


@app.get("/health")
def health():
    return {
        "model_loaded": model is not None,
        "model_path": str(MODEL_PATH)
    }


@app.post("/predict", response_model=PredictResponse)
def predict_price(payload: PredictRequest):

    if model is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded."
        )

    try:
        row = pd.DataFrame([payload.model_dump()])

        pred_log = model.predict(row)[0]

        price_lakhs = float(np.expm1(pred_log))

        preprocessor = model.named_steps["preprocessor"]
        regressor = model.named_steps["regressor"]

        X_processed = preprocessor.transform(row)

        tree_preds = np.array([
            tree.predict(X_processed)[0]
            for tree in regressor.estimators_
        ])

        tree_prices = np.expm1(tree_preds)

        lower = np.percentile(tree_prices, 5)
        upper = np.percentile(tree_prices, 95)
        price_per_sqft = (
            price_lakhs * 100000
        ) / payload.Area

        if price_lakhs >= 150:
            segment = "Luxury"
        elif price_lakhs >= 80:
            segment = "Premium"
        else:
            segment = "Affordable"

        return PredictResponse(
            predicted_price_lakhs=round(price_lakhs, 2),
            price_range_95_ci=PriceRange(
                lower=round(lower, 2),
                upper=round(upper, 2),
            ),
            model_confidence=95,
            price_per_sqft=round(price_per_sqft),
            market_segment=segment,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.get("/analytics/areas")
def analytics_areas():

    try:
        group_df = _analytics_group_df()

        result = []
        for _, row in group_df.iterrows():
            result.append({
                "mapped_area": row["Mapped_Area"],
                "price_mean_lakhs": round(float(row["Price"]), 2),
                "area_mean_sqft": round(float(row["Area"]), 0),
                "price_per_sqft": round(float(row["Price_per_SqFt"]), 0),
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"])
            })

        return {"areas": result}

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.get("/recommendations/data")
def recommendations_data():
    try:
        return JSONResponse(content=_recommendation_data())
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.get("/insights/data")
def insights_data():
    try:
        data_path = BASE_DIR / "insights_data.json"
        with data_path.open("r", encoding="utf-8") as file:
            insights_payload = json.load(file)
        return JSONResponse(content=insights_payload)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Insights data file not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/analytics/map")
def analytics_map():
    try:
        group_df = _analytics_group_df()
        fig = _analytics_map_figure(group_df)
        expensive_areas_fig = _expensive_areas_figure()
        affordable_areas_fig = _affordable_areas_figure()
        locality_market_share_fig = _locality_market_share_figure()
        property_status_dist_fig = _property_status_distribution_figure()
        market_segment_figures = _market_segment_figures()
        bhk_price_fig = _bhk_price_figure()
        property_age_price_figures = _property_age_price_figures()
        area_price_scatter_fig = _area_price_scatter_figure()
        market_pricing_figure, market_pricing_samples = _market_pricing_analysis()
        localities = sorted(group_df["Mapped_Area"].dropna().unique().tolist())
        return JSONResponse(content={
            "figure": json.loads(pio.to_json(fig)),
            "expensive_areas_figure": json.loads(pio.to_json(expensive_areas_fig)),
            "affordable_areas_figure": json.loads(pio.to_json(affordable_areas_fig)),
            "locality_market_share_figure": json.loads(pio.to_json(locality_market_share_fig)),
            "property_status_distribution_figure": json.loads(pio.to_json(property_status_dist_fig)),
            "market_segment_figures": market_segment_figures,
            "market_segment_summary": _market_segment_summary(),
            "bhk_price_figure": bhk_price_fig,
            "bhk_distribution_figure": json.loads(pio.to_json(_bhk_distribution_figure())),
            "bhk_distribution_localities": ["All"] + localities,
            "property_age_price_figures": property_age_price_figures,
            "area_price_scatter_figure": json.loads(pio.to_json(area_price_scatter_fig)),
            "market_pricing_figure": market_pricing_figure,
            "market_pricing_samples": market_pricing_samples,
            "metrics": _analytics_metrics(),
            "area_comparison": _area_comparison_summary(),
            "amenities": _amenities_summary(),
            "amenities_wordcloud_image": _amenities_wordcloud_image(),
            "nearby_wordcloud_image": _nearby_wordcloud_image(),
        })

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )
