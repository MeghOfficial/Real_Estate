import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# ============================================
# DASH APP INITIALIZATION
# ============================================

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Property Price Analyzer"

# ============================================
# COLOR MAPPING FOR IMPACT LEVELS
# ============================================

impact_colors = {
    "Very High": "#EF4444",  # Red
    "High": "#F97316",       # Orange
    "Moderate": "#EAB308",   # Yellow
    "Low": "#22C55E",        # Green
    "Very Low": "#3B82F6"    # Blue
}

impact_emojis = {
    "Very High": "🔴",
    "High": "🟠",
    "Moderate": "🟡",
    "Low": "🟢",
    "Very Low": "🔵"
}

# ============================================
# NUMERICAL FEATURES DATA (with short_name)
# ============================================

numerical_data = {
    'bedrooms': {
        'short_name': 'Bedrooms',
        'display_name': '🛏 Bedrooms Analysis',
        'impact': '+31.41%',
        'impact_level': 'Very High',
        'explanation': 'Properties with one additional bedroom are predicted to be **31.41% more expensive**, keeping all other features constant.',
        'current_value': 2,
        'current_price': 80,
        'new_value': 3,
        'new_price': 105.13,
        'increase': 25.13,
        'market_insight': 'Bedroom count is one of the strongest factors influencing property prices. Homes with more bedrooms generally appeal to a wider range of buyers, particularly families, resulting in stronger market demand and higher property values.',
        'buyer_insight': 'If you\'re choosing between similar properties, an additional bedroom can provide greater flexibility for growing families, guests, or a home office. Since bedroom count is a major price driver, paying a premium for an extra bedroom may offer better long-term value than spending more on minor features.',
        'seller_insight': 'If your property has additional bedrooms, make them a key highlight in your listing. Spacious and well-designed bedrooms attract more potential buyers and can help justify a higher asking price while improving the property\'s overall market appeal.'
    },
    'bathrooms': {
        'short_name': 'Bathrooms',
        'display_name': '🚿 Bathrooms Analysis',
        'impact': '+4.85%',
        'impact_level': 'Moderate',
        'explanation': 'Properties with one additional bathroom are predicted to be **4.85% more expensive**, keeping all other features constant.',
        'current_value': 2,
        'current_price': 80,
        'new_value': 3,
        'new_price': 83.88,
        'increase': 3.88,
        'market_insight': 'Bathrooms contribute to a property\'s market appeal by improving everyday comfort and functionality. While they can positively influence the estimated price, their overall impact is usually moderate, as buyers tend to place greater importance on location, property size, and bedroom count when assessing a property\'s value.',
        'buyer_insight': 'When comparing similar properties, an additional bathroom can improve daily convenience and comfort, particularly for larger families. Although it adds value, buyers should prioritize key factors such as location, property size, and bedroom count before paying a significant premium for extra bathrooms.',
        'seller_insight': 'A well-maintained or modern bathroom can make a property more attractive to potential buyers and enhance its overall presentation. Highlighting renovated bathrooms and quality fittings in your listing can increase buyer interest, even though bathrooms are generally a secondary factor in determining property value.'
    },
    'balconies': {
        'short_name': 'Balconies',
        'display_name': '🌇 Balconies Analysis',
        'impact': '+0.13%',
        'impact_level': 'Very Low',
        'explanation': 'Properties with one additional balcony are predicted to be **0.13% more expensive**, keeping all other features constant.',
        'current_value': 2,
        'current_price': 80,
        'new_value': 3,
        'new_price': 80.10,
        'increase': 0.10,
        'market_insight': 'Balconies enhance a property\'s lifestyle appeal by providing additional outdoor space and improving natural light and ventilation. While they can positively influence buyer interest, their overall impact on property value is usually low, as buyers generally place greater importance on location, property size, bedrooms, and bathrooms when evaluating a property.',
        'buyer_insight': 'A balcony can improve everyday living by offering space for relaxation, fresh air, or small outdoor activities. While it adds comfort and convenience, buyers should focus on major factors such as location, property size, and bedroom count before paying a significant premium for additional balconies.',
        'seller_insight': 'If your property has a well-designed balcony or an attractive view, showcase it in your listing with high-quality photos. Although balconies alone may not significantly increase property value, they can improve buyer interest and help your property stand out in a competitive market.'
    },
    'area_sqft': {
        'short_name': 'Area (sqft)',
        'display_name': '📐 Area (sqft) Analysis',
        'impact': '+0.02% per sqft',
        'impact_level': 'Very High',
        'explanation': 'Every additional square foot is associated with a **0.02% increase in predicted property price**, keeping all other features constant.',
        'current_value': 1200,
        'current_price': 80,
        'new_value': 1500,
        'new_price': 84.80,
        'increase': 4.80,
        'market_insight': 'Area is one of the most influential factors in property valuation. Larger properties generally command higher prices because they provide more usable living space and appeal to a broader range of buyers. As a result, property size is often one of the strongest drivers of market value.',
        'buyer_insight': 'When comparing similar properties, a larger area can offer greater comfort, flexibility, and future usability. While larger properties usually cost more, they often provide better long-term value for growing families and may have stronger resale potential.',
        'seller_insight': 'If your property offers a spacious layout, emphasize the usable living area in your listing. Buyers often use property size as one of the first comparison criteria, making it an important feature for attracting interest and supporting a competitive asking price.'
    },
    'total_floors': {
        'short_name': 'Total Floors',
        'display_name': '🏢 Total Floors Analysis',
        'impact': '+1.86%',
        'impact_level': 'Moderate',
        'explanation': 'Properties in buildings with one additional floor are predicted to be **1.86% more expensive**, keeping all other features constant.',
        'current_value': 10,
        'current_price': 80,
        'new_value': 11,
        'new_price': 81.49,
        'increase': 1.49,
        'market_insight': 'Buildings with more floors are often associated with larger residential developments that offer modern amenities, better infrastructure, and enhanced community facilities. As a result, properties in such developments may command higher prices, although their impact is generally smaller than key factors such as location, property size, and bedroom count.',
        'buyer_insight': 'When evaluating a property, consider the overall quality of the residential development rather than just the number of floors. Multi-storey buildings often provide amenities such as elevators, security, parking, and recreational facilities, which can improve convenience and long-term living experience.',
        'seller_insight': 'If your property is located in a well-maintained multi-storey residential complex, highlight features such as modern amenities, security, parking, and community facilities in your listing. Buyers often associate these developments with better lifestyle and convenience, which can increase buyer interest.'
    },
    'current_floor': {
        'short_name': 'Current Floor',
        'display_name': '🏢 Current Floor Analysis',
        'impact': '+0.24%',
        'impact_level': 'Low',
        'explanation': 'Properties located one floor higher are predicted to be **0.24% more expensive**, keeping all other features constant.',
        'current_value': 5,
        'current_price': 80,
        'new_value': 6,
        'new_price': 80.19,
        'increase': 0.19,
        'market_insight': 'The floor on which a property is located has a relatively small influence on its market value compared to major factors such as location, property size, and bedroom count. While higher floors may offer better views, privacy, and natural ventilation, buyers generally consider these as secondary factors when determining a property\'s overall value.',
        'buyer_insight': 'Choose the floor that best suits your lifestyle and daily needs rather than focusing solely on its impact on price. Higher floors often provide better views and reduced noise, while lower floors may offer easier access, making the right choice dependent on your personal preferences and convenience.',
        'seller_insight': 'If your property is located on a desirable floor, emphasize advantages such as scenic views, natural light, ventilation, or convenient accessibility in your listing. While floor level alone may not significantly increase the property\'s value, highlighting these benefits can improve buyer interest and help differentiate your property from similar listings.'
    }
}

# ============================================
# CATEGORICAL FEATURES DATA (with short_name, examples, insights)
# ============================================

categorical_data = {
    'mapped_area': {
        'short_name': 'Mapped Area',
        'display_name': '📍 Mapped Area Analysis',
        'baseline': 'Adalaj',
        'baseline_price': 80,
        'values': {
            'Gift City': {'impact': '+63.38%', 'price': 130.70, 'change': 50.70},
            'Sector 22': {'impact': '+24.32%', 'price': 99.46, 'change': 19.46},
            'Raysan': {'impact': '+18.16%', 'price': 94.53, 'change': 14.53},
            'Sector 6': {'impact': '+17.67%', 'price': 94.14, 'change': 14.14},
            'Sector 19': {'impact': '+9.90%', 'price': 87.92, 'change': 7.92},
            'Koba': {'impact': '+8.49%', 'price': 86.79, 'change': 6.79},
            'Sector 11': {'impact': '+8.20%', 'price': 86.56, 'change': 6.56},
            'Kudasan': {'impact': '+7.96%', 'price': 86.37, 'change': 6.37},
            'Sargasan': {'impact': '+3.86%', 'price': 83.09, 'change': 3.09},
            'Uvarsad': {'impact': '+3.64%', 'price': 82.91, 'change': 2.91},
            'Sector 8': {'impact': '+2.47%', 'price': 81.98, 'change': 1.98},
            'Randesan': {'impact': '+2.06%', 'price': 81.65, 'change': 1.65},
            'Sughad': {'impact': '+1.84%', 'price': 81.47, 'change': 1.47},
            'Sector 28': {'impact': '+0.55%', 'price': 80.44, 'change': 0.44},
            'Valad': {'impact': '-0.55%', 'price': 79.56, 'change': -0.44},
            'SG Highway': {'impact': '-0.78%', 'price': 79.38, 'change': -0.62},
            'Other': {'impact': '-1.32%', 'price': 78.94, 'change': -1.06},
            'Gandhinagar Taluka': {'impact': '-2.30%', 'price': 78.16, 'change': -1.84},
            'Dahegam': {'impact': '-2.95%', 'price': 77.64, 'change': -2.36},
            'Sector 26': {'impact': '-3.43%', 'price': 77.26, 'change': -2.74},
            'Karai': {'impact': '-5.21%', 'price': 75.83, 'change': -4.17},
            'Khoraj': {'impact': '-5.85%', 'price': 75.32, 'change': -4.68},
            'SP Ring Road': {'impact': '-6.52%', 'price': 74.78, 'change': -5.22},
            'Sector 24': {'impact': '-6.60%', 'price': 74.72, 'change': -5.28},
            'Vavol': {'impact': '-8.17%', 'price': 73.46, 'change': -6.54},
            'Kolavada': {'impact': '-10.85%', 'price': 71.32, 'change': -8.68},
            'Chiloda': {'impact': '-11.23%', 'price': 71.02, 'change': -8.98},
            'Randheja': {'impact': '-14.05%', 'price': 68.76, 'change': -11.24},
            'Pethapur': {'impact': '-16.63%', 'price': 66.70, 'change': -13.30},
            'Kalol': {'impact': '-35.80%', 'price': 51.36, 'change': -28.64}
        },
        'explanation': 'Area premiums are measured relative to the reference area used by the model\'s One-Hot Encoding. In this model, **Adalaj** is the baseline area. Therefore, all location impacts should be interpreted as differences compared with Adalaj while keeping all other property characteristics constant.',
        'examples': [
            {'from': 'Adalaj', 'to': 'Gift City', 'price': 130.70, 'change': 50.70},
            {'from': 'Adalaj', 'to': 'Kalol', 'price': 51.36, 'change': -28.64}
        ],
        'insights': {
            'market': 'Location is one of the strongest factors influencing property prices. Areas with better infrastructure, connectivity, employment opportunities, and future development potential generally command higher prices. In this model, locations such as Gift City receive a significant price premium, while areas like Kalol tend to have lower property prices compared with the baseline location.',
            'buyer': 'When choosing a property, consider not only the current price but also the area\'s long-term growth potential. Premium locations may require a higher investment but often offer better infrastructure, amenities, and resale opportunities, whereas more affordable locations can provide better value for budget-conscious buyers.',
            'seller': 'If your property is located in a high-demand area, highlight nearby infrastructure, schools, business hubs, transportation, and future development projects in your listing. A property\'s location is one of the first factors buyers evaluate and can significantly influence both buyer interest and the achievable selling price.'
        },
        'note': 'Area premiums are measured relative to the reference area used by the model\'s One-Hot Encoding. In this model, **Adalaj** is the baseline area. Therefore, all location impacts should be interpreted as differences compared with Adalaj while keeping all other property characteristics constant.'
    },
    'area_type': {
        'short_name': 'Area Type',
        'display_name': '📏 Area Type Analysis',
        'baseline': 'Built-up',
        'baseline_price': 80,
        'values': {
            'Carpet': {'impact': '+1.28%', 'price': 81.02, 'change': 1.02},
            'Super Built-up': {'impact': '-2.06%', 'price': 78.35, 'change': -1.65}
        },
        'explanation': 'Area Type describes how the property\'s area is measured. Compared to **Built-up Area** (the baseline), properties listed using **Carpet Area** are predicted to be **1.28% more expensive**, while properties listed using **Super Built-up Area** are predicted to be **2.06% less expensive**, keeping all other features constant.',
        'examples': [
            {'area_sqft': 1500, 'type': 'Carpet', 'price': 81.02},
            {'area_sqft': 1500, 'type': 'Built-up (Baseline)', 'price': 80.00},
            {'area_sqft': 1500, 'type': 'Super Built-up', 'price': 78.35}
        ],
        'insights': {
            'market': 'Area Type helps explain how a property\'s reported area is measured and should always be interpreted together with the property\'s area (sqft). While Area Type has only a modest direct influence on price, understanding whether the reported size represents Carpet Area, Built-up Area, or Super Built-up Area is essential for making fair comparisons between similar properties.',
            'buyer': 'When comparing properties with the same advertised area, always check the Area Type. A 1,500 sqft Carpet Area property provides more usable living space than a 1,500 sqft Super Built-up Area property, making Area Type an important factor when evaluating the true value of a property.',
            'seller': 'Clearly mention both the property\'s area (sqft) and Area Type in your listing. Transparent area measurements help buyers compare properties more accurately, build trust, and reduce confusion during the buying process.'
        },
        'note': 'These percentages are measured relative to the baseline area type used by the model\'s One-Hot Encoding. The impact is relatively small and should not be interpreted as a major driver of property value.'
    },
    'property_status': {
        'short_name': 'Property Status',
        'display_name': '🏗️ Property Status Analysis',
        'baseline': 'Ready to Move',
        'baseline_price': 80,
        'values': {
            'Under Construction': {'impact': '-1.01%', 'price': 79.19, 'change': -0.81}
        },
        'explanation': 'Property Status indicates whether a property is ready for occupancy or still under construction. Compared to **Ready to Move** properties (the baseline category), **Under Construction** properties are predicted to be **1.01% less expensive**, keeping all other features constant.',
        'examples': [
            {'status': 'Ready to Move (Baseline)', 'price': 80.00},
            {'status': 'Under Construction', 'price': 79.19}
        ],
        'insights': {
            'market': 'Property status has a relatively small influence on property prices compared with major factors such as location, property size, and bedroom count. While ready-to-move and under-construction properties may differ slightly in price, buyers generally prioritize the property\'s location, size, and overall value when making purchasing decisions.',
            'buyer': 'Choose a property\'s status based on your needs rather than price alone. Ready-to-move properties offer immediate possession, while under-construction properties may provide flexible payment plans and the potential for future appreciation. Consider factors such as possession timeline, builder reputation, and project completion before making a decision.',
            'seller': 'Clearly communicate your property\'s current status and expected possession timeline in the listing. Buyers appreciate transparency, and providing accurate information about construction progress or move-in readiness can increase buyer confidence and improve the property\'s market appeal.'
        },
        'note': 'These percentages are measured relative to the baseline property status used by the model\'s One-Hot Encoding (**Ready to Move**). The impact is relatively small and should not be interpreted as a major driver of property value.'
    },
    'property_age': {
        'short_name': 'Property Age',
        'display_name': '📅 Property Age Analysis',
        'baseline': '1-5 Years',
        'baseline_price': 80,
        'values': {
            'New': {'impact': '-5.69%', 'price': 75.45, 'change': -4.55},
            '5-10 Years': {'impact': '-4.91%', 'price': 76.07, 'change': -3.93},
            '10-20 Years': {'impact': '-3.87%', 'price': 76.90, 'change': -3.10},
            'Unknown': {'impact': '-2.99%', 'price': 77.61, 'change': -2.39}
        },
        'explanation': 'Property Age represents how old the property is. Compared to **1–5 Years** properties (the baseline category), **New** properties are predicted to be **5.69% less expensive**, **5–10 Years** properties are **4.91% less expensive**, **10–20 Years** properties are **3.87% less expensive**, and properties with **Unknown** age are **2.99% less expensive**, while keeping all other features such as location, area, bedrooms, and bathrooms constant.',
        'examples': [
            {'age': 'New', 'price': 75.45},
            {'age': '1-5 Years (Baseline)', 'price': 80.00},
            {'age': '5-10 Years', 'price': 76.07},
            {'age': '10-20 Years', 'price': 76.90},
            {'age': 'Unknown', 'price': 77.61}
        ],
        'insights': {
            'market': 'Property age has a relatively small influence on property prices compared with major factors such as location, property size, and bedroom count. In this model, properties aged **1–5 years** receive the highest estimated prices, while **New** properties show a slightly lower estimated value than the baseline. This pattern reflects the relationships learned from the available dataset and should not be interpreted as a general real estate market trend.',
            'buyer': 'Property age should be considered alongside factors such as location, construction quality, and maintenance rather than price alone. Newer properties may offer modern designs and lower maintenance costs, while slightly older homes can provide better value depending on their condition and location.',
            'seller': 'Highlight the property\'s condition, renovations, and maintenance history instead of focusing only on its age. Buyers often value a well-maintained home more than its construction year, especially when it is located in a desirable area and offers good living space.'
        },
        'note': 'These percentages are measured relative to the baseline property age (**1–5 Years**) used by the model\'s One-Hot Encoding. They represent the effect of **property age alone**, assuming all other property characteristics remain unchanged.'
    },
    'furnishing_status': {
        'short_name': 'Furnishing Status',
        'display_name': '🪑 Furnishing Status Analysis',
        'baseline': 'Semi-Furnished',
        'baseline_price': 80,
        'values': {
            'Furnished': {'impact': '+4.00%', 'price': 83.20, 'change': 3.20},
            'Unfurnished': {'impact': '-2.67%', 'price': 77.86, 'change': -2.14}
        },
        'explanation': 'Furnishing Status indicates whether a property is **Furnished, Semi-Furnished, or Unfurnished**. Compared to **Semi-Furnished** properties (the baseline category), **Furnished** properties are predicted to be **4.00% more expensive**, while **Unfurnished** properties are predicted to be **2.67% less expensive**, keeping all other features such as location, area, bedrooms, and bathrooms constant.',
        'examples': [
            {'status': 'Furnished', 'price': 83.20},
            {'status': 'Semi-Furnished (Baseline)', 'price': 80.00},
            {'status': 'Unfurnished', 'price': 77.86}
        ],
        'insights': {
            'market': 'Furnishing status has a modest influence on property prices. Fully furnished properties generally command a small price premium because they offer greater convenience and are ready for immediate occupancy. However, furnishing status has a much smaller impact on property value than major factors such as location, property size, and bedroom count.',
            'buyer': 'Choose the furnishing status based on your lifestyle and budget. Fully furnished properties can save time and setup costs, while unfurnished homes offer greater flexibility to personalize the interiors according to your preferences.',
            'seller': 'If your property is fully furnished, showcase the quality and condition of the furniture with clear photos and detailed descriptions. Well-presented furnishings can increase buyer interest and justify a modest price premium, especially for buyers seeking a move-in-ready home.'
        },
        'note': 'These percentages are measured relative to the baseline furnishing status (**Semi-Furnished**) used by the model\'s One-Hot Encoding. They represent the effect of **furnishing status alone**, assuming all other property characteristics remain unchanged.'
    },
    'facing': {
        'short_name': 'Facing Direction',
        'display_name': '🧭 Facing Direction Analysis',
        'baseline': 'East',
        'baseline_price': 80,
        'values': {
            'North': {'impact': '+1.79%', 'price': 81.43, 'change': 1.43},
            'South-West': {'impact': '+1.26%', 'price': 81.01, 'change': 1.01},
            'West': {'impact': '+1.19%', 'price': 80.95, 'change': 0.95},
            'North-West': {'impact': '+0.20%', 'price': 80.16, 'change': 0.16},
            'Other': {'impact': '-1.09%', 'price': 79.13, 'change': -0.87},
            'North-East': {'impact': '-1.94%', 'price': 78.45, 'change': -1.55},
            'South': {'impact': '-2.13%', 'price': 78.30, 'change': -1.70},
            'South-East': {'impact': '-2.34%', 'price': 78.13, 'change': -1.87}
        },
        'explanation': 'Facing Direction represents the direction a property\'s main entrance or front side faces. Compared to **East-facing** properties (the baseline category), **North-facing** properties are predicted to be **1.79% more expensive**, while **South-East-facing** properties are predicted to be **2.34% less expensive**, keeping all other features such as location, area, bedrooms, and bathrooms constant.',
        'examples': [
            {'direction': 'North', 'price': 81.43},
            {'direction': 'South-West', 'price': 81.01},
            {'direction': 'West', 'price': 80.95},
            {'direction': 'North-West', 'price': 80.16},
            {'direction': 'East (Baseline)', 'price': 80.00},
            {'direction': 'Other', 'price': 79.13},
            {'direction': 'North-East', 'price': 78.45},
            {'direction': 'South', 'price': 78.30},
            {'direction': 'South-East', 'price': 78.13}
        ],
        'insights': {
            'market': 'Facing direction has only a minor influence on property prices compared with major factors such as location, property size, and bedroom count. While certain facing directions may receive a small price premium or discount based on buyer preferences, their overall impact on a property\'s market value is relatively limited.',
            'buyer': 'Choose a property\'s facing direction based on your personal preferences, climate, natural lighting, and ventilation rather than price alone. While some buyers may prefer specific directions, the overall quality, location, and layout of the property usually have a much greater influence on long-term satisfaction and value.',
            'seller': 'If your property\'s facing direction is considered desirable in your local market, mention it in the listing as an additional selling point. However, focus primarily on highlighting stronger value drivers such as location, property size, layout, and amenities, as these have a much greater influence on buyer decisions.'
        },
        'note': 'These percentages are measured relative to the baseline facing direction (**East**) used by the model\'s One-Hot Encoding. They represent the effect of **facing direction alone**, assuming all other property characteristics remain unchanged.'
    }
}

# ============================================
# CARD GENERATION FUNCTIONS
# ============================================

def create_numerical_card(feature_key):
    """Create a card for numerical features with color-coded impact levels"""
    data = numerical_data[feature_key]
    impact_level = data['impact_level']
    color = impact_colors[impact_level]
    emoji = impact_emojis[impact_level]
    
    return dbc.Card([
        dbc.CardHeader(html.H4(data['display_name'], className="mb-0")),
        dbc.CardBody([
            # Impact Section
            html.Div([
                html.H6("📈 Impact", className="text-muted"),
                html.H2(data['impact'], className="fw-bold", style={"color": color}),
                html.P([
                    html.Span(emoji, style={"fontSize": "1.2rem"}),
                    html.Span(f" Impact Level: {impact_level}", 
                             style={"color": color, "fontWeight": "bold"})
                ], className="mt-1")
            ], className="mb-3"),
            
            # Explanation
            html.Div([
                html.H6("📝 Explanation", className="text-muted"),
                html.P(dcc.Markdown(data['explanation']), className="mb-0")
            ], className="mb-3"),
            
            # Example Scenario
            html.Div([
                html.H6("💰 Example Scenario", className="text-muted"),
                dbc.Alert([
                    html.P([
                        html.Strong("Current Property:"),
                        html.Br(),
                        f"• {data['current_value']} {feature_key.replace('_', ' ').capitalize()}",
                        html.Br(),
                        f"• Price: ₹{data['current_price']} Lakhs"
                    ]),
                    html.Hr(),
                    html.P([
                        html.Strong("After Adding 1:"),
                        html.Br(),
                        f"• {data['new_value']} {feature_key.replace('_', ' ').capitalize()}",
                        html.Br(),
                        f"• Estimated Price: ₹{data['new_price']:.2f} Lakhs"
                    ]),
                    html.H5([
                        html.Strong("Estimated Increase:"),
                        f" +₹{data['increase']:.2f} Lakhs"
                    ], className="text-success")
                ], color="light", className="mb-0")
            ], className="mb-3"),
            
            # Business Insights
            html.Div([
                html.H6("🎯 Business Insight", className="text-muted"),
                
                # Market Insight
                html.Div([
                    html.H6("📊 Market Insight", className="text-secondary"),
                    html.P(data['market_insight'], className="mb-2")
                ], className="mb-2"),
                
                # Buyer Insight
                html.Div([
                    html.H6("🛒 Buyer Insight", className="text-secondary"),
                    html.P(data['buyer_insight'], className="mb-2")
                ], className="mb-2"),
                
                # Seller Insight
                html.Div([
                    html.H6("🏠 Seller Insight", className="text-secondary"),
                    html.P(data['seller_insight'], className="mb-0")
                ])
            ], className="mb-3"),
            
            # Important Note
            html.Div([
                html.H6("⚠ Important Note", className="text-muted"),
                html.P(
                    "This does not mean every property will increase by exactly the stated percentage. "
                    "The estimate comes from the machine learning model and assumes all other factors "
                    "remain unchanged. The impact shown represents the average relationship learned "
                    "from the training data.",
                    className="mb-0",
                    style={"fontSize": "0.9rem", "color": "#6c757d"}
                )
            ])
        ])
    ], className="mb-4 shadow-sm")

def create_categorical_card(feature_key):
    """Create a card for categorical features with table, examples, and insights"""
    data = categorical_data[feature_key]
    
    # Build table rows
    table_rows = []
    for name, values in data['values'].items():
        is_baseline = name == data['baseline']
        impact_value = values['impact']
        color = "green" if '+' in impact_value else "red" if '-' in impact_value else "black"
        
        table_rows.append(
            html.Tr([
                html.Td(
                    f"**{name}**" if is_baseline else name,
                    style={"fontWeight": "bold"} if is_baseline else {}
                ),
                html.Td(
                    impact_value,
                    style={"color": color, "fontWeight": "bold"}
                ),
                html.Td(f"₹{values['price']:.2f} Lakhs")
            ])
        )
    
    # Build examples section based on feature type
    examples_content = []
    examples = data.get('examples', [])
    if examples:
        # Check the first example to determine structure
        first_example = examples[0]
        if 'from' in first_example:  # mapped_area style (from-to)
            for ex in examples:
                examples_content.append(
                    html.Div([
                        html.P([
                            html.Strong("Current Property:"),
                            f" Area – {ex['from']}",
                            html.Br(),
                            f"Price – ₹{data['baseline_price']} Lakhs"
                        ]),
                        html.P([
                            html.Strong("Move To:"),
                            f" {ex['to']}",
                            html.Br(),
                            html.Strong("Result:"),
                            f" Estimated New Price – ₹{ex['price']:.2f} Lakhs",
                            html.Br(),
                            html.Strong("Change:"),
                            f" {ex['change']:+.2f} Lakhs" if ex['change'] >= 0 else f" {ex['change']:.2f} Lakhs"
                        ]),
                        html.Hr() if ex != examples[-1] else None
                    ])
                )
        elif 'area_sqft' in first_example:  # area_type style
            examples_content.append(
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Area Sqft"),
                        html.Th("Area Type"),
                        html.Th("Estimated Price")
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(ex['area_sqft']),
                            html.Td(ex['type']),
                            html.Td(f"₹{ex['price']:.2f} Lakhs")
                        ]) for ex in examples
                    ])
                ], bordered=True, striped=True, hover=True, size="sm")
            )
        else:  # generic style (status, age, direction)
            # Build a table with two columns: Category and Estimated Price
            examples_content.append(
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Category"),
                        html.Th("Estimated Price")
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(ex.get('status') or ex.get('age') or ex.get('direction', '')),
                            html.Td(f"₹{ex['price']:.2f} Lakhs")
                        ]) for ex in examples
                    ])
                ], bordered=True, striped=True, hover=True, size="sm")
            )
    
    # Build insights
    insights = data.get('insights', {})
    insights_html = []
    if insights:
        if 'market' in insights:
            insights_html.append(
                html.Div([
                    html.H6("📊 Market Insight", className="text-secondary"),
                    html.P(insights['market'], className="mb-2")
                ], className="mb-2")
            )
        if 'buyer' in insights:
            insights_html.append(
                html.Div([
                    html.H6("🛒 Buyer Insight", className="text-secondary"),
                    html.P(insights['buyer'], className="mb-2")
                ], className="mb-2")
            )
        if 'seller' in insights:
            insights_html.append(
                html.Div([
                    html.H6("🏠 Seller Insight", className="text-secondary"),
                    html.P(insights['seller'], className="mb-0")
                ])
            )
    
    return dbc.Card([
        dbc.CardHeader(html.H4(data['display_name'], className="mb-0")),
        dbc.CardBody([
            # Impact Table
            html.Div([
                html.H6("📊 Price Impact by Category", className="text-muted"),
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Category"),
                        html.Th("Price Impact"),
                        html.Th("Estimated Price (Base: ₹80 Lakhs)")
                    ])),
                    html.Tbody(table_rows)
                ], bordered=True, striped=True, hover=True, className="mb-2"),
                html.P(f"**Baseline:** {data['baseline']} (0.00%)", className="text-muted")
            ], className="mb-3"),
            
            # Explanation
            html.Div([
                html.H6("📝 Explanation", className="text-muted"),
                html.P(dcc.Markdown(data['explanation']), className="mb-0")
            ], className="mb-3"),
            
            # Examples
            html.Div([
                html.H6("💰 Examples", className="text-muted"),
                dbc.Alert(examples_content, color="light", className="mb-0")
            ], className="mb-3"),
            
            # Business Insights
            html.Div([
                html.H6("🎯 Business Insight", className="text-muted"),
                *insights_html
            ], className="mb-3"),
            
            # Important Note
            html.Div([
                html.H6("⚠ Important Note", className="text-muted"),
                html.P(dcc.Markdown(data['note']), className="mb-0", style={"fontSize": "0.9rem"})
            ])
        ])
    ], className="mb-4 shadow-sm")

# ============================================
# APP LAYOUT
# ============================================

app.layout = dbc.Container([
    html.H1("🏠 Property Price Analyzer", className="text-center my-4"),
    html.P("Select a feature to analyze its impact on property prices", 
           className="text-center text-muted"),
    
    html.Hr(),
    
    # Dropdown Selection
    dbc.Row([
        dbc.Col([
            html.H5("Select Feature Category:"),
            dcc.Dropdown(
                id="category-dropdown",
                options=[
                    {"label": "📊 Numerical Features", "value": "numerical"},
                    {"label": "📍 Categorical Features", "value": "categorical"}
                ],
                value="numerical",
                clearable=False
            )
        ], width=6),
        dbc.Col([
            html.H5("Select Feature:"),
            dcc.Dropdown(
                id="feature-dropdown",
                options=[],
                value=None,
                clearable=False
            )
        ], width=6)
    ], className="mb-4"),
    
    html.Hr(),
    
    # Card Container
    dbc.Row([
        dbc.Col([
            html.Div(id="feature-card-container")
        ], width=12)
    ])
], fluid=True, className="px-4")

# ============================================
# CALLBACKS
# ============================================

@app.callback(
    Output("feature-dropdown", "options"),
    Output("feature-dropdown", "value"),
    Output("feature-card-container", "children"),
    Input("category-dropdown", "value"),
    Input("feature-dropdown", "value")
)
def update_all(category, feature):
    """Combined callback that handles all updates"""
    
    feature_options = []
    feature_value = None
    card_content = html.P("Please select a feature to analyze", className="text-center")
    
    if category == "numerical":
        # Use short_name for dropdown display
        feature_options = [
            {"label": data['short_name'], "value": key}
            for key, data in numerical_data.items()
        ]
        feature_value = feature if feature and feature in numerical_data else "bedrooms"
        
        if feature_value in numerical_data:
            card_content = create_numerical_card(feature_value)
        else:
            card_content = html.P("Feature not found", className="text-center text-danger")
            
    else:  # categorical
        feature_options = [
            {"label": data['short_name'], "value": key}
            for key, data in categorical_data.items()
        ]
        feature_value = feature if feature and feature in categorical_data else "mapped_area"
        
        if feature_value in categorical_data:
            card_content = create_categorical_card(feature_value)
        else:
            card_content = html.P("Feature not found", className="text-center text-danger")
    
    return feature_options, feature_value, card_content

# ============================================
# RUN THE APP
# ============================================

if __name__ == "__main__":
    app.run(debug=True, port=8050)