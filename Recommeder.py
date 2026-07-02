import dash
from dash import dcc, html, Input, Output, State, callback
import dash_table
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.metrics.pairwise import cosine_similarity

# ------------------------------
# 1. Load and preprocess data
# ------------------------------
df = pd.read_csv('data/gandhinagar_property_apartments_recommender_ready.csv')

# ---- Clean numeric columns ----
num_cols_raw = ['price_inr_in_lakhs', 'area_sqft', 'bedrooms', 'bathrooms', 
                'balconies', 'current_floor', 'total_floors']
for col in num_cols_raw:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df[col] = df[col].fillna(0)

# ---- Handle property_age ----
age_map = {
    'New': 0,
    '1-5 years': 3,
    '5-10 years': 7.5,
    '10-20 years': 15,
    'Unknown': 0
}
df['property_age_numeric'] = df['property_age'].map(age_map).fillna(0)

# ---- String columns ----
df['property_type'] = df['property_type'].fillna('unknown').str.lower()
df['property_status'] = df['property_status'].fillna('Unknown')
df['area_type'] = df['area_type'].fillna('Super Built-up')
df['furnishing_status'] = df['furnishing_status'].fillna('Unknown')
df['mapped_area'] = df['mapped_area'].fillna('Unknown')
df['facing'] = df['facing'].fillna('Unknown')
df['description'] = df['description'].fillna('No description available.')
df['property_url'] = df['property_url'].fillna('#')

df['bedrooms'] = df['bedrooms'].astype(int)
df = df.dropna(subset=['price_inr_in_lakhs', 'area_sqft', 'bedrooms'])

# ---- Add floor_category (for display only, not used in similarity) ----
def get_floor_category(row):
    current = row.get('current_floor', np.nan)
    total = row.get('total_floors', np.nan)
    if pd.isna(current) or pd.isna(total) or total == 0:
        return 'Any Floor'
    ratio = current / total
    if ratio <= 0.25:
        return 'Lower Floor'
    elif ratio <= 0.5:
        return 'Mid Floor'
    elif ratio <= 0.75:
        return 'Higher Floor'
    else:
        return 'Top Floor'

df['floor_category'] = df.apply(get_floor_category, axis=1)

# ------------------------------
# 2. Build weighted similarity matrix (YOUR CODE)
# ------------------------------
numeric_features = [
    'price_inr_in_lakhs',
    'area_sqft',
    'bedrooms',
    'bathrooms',
    'balconies',
    'current_floor',
    'total_floors'
]

categorical_features = [
    'mapped_area',
    'property_age',
    'property_type',
    'furnishing_status',
    'facing',
    'area_type'
]

# Numeric part: MinMaxScaler + weights
scaler = MinMaxScaler()
num_matrix = scaler.fit_transform(df[numeric_features])

num_weights = {
    'price_inr_in_lakhs': 0.15,
    'area_sqft': 0.15,
    'bedrooms': 0.12,
    'bathrooms': 0.05,
    'balconies': 0.03,
    'current_floor': 0.01,
    'total_floors': 0.01
}
for i, col in enumerate(numeric_features):
    num_matrix[:, i] *= num_weights[col]

# Categorical part: OneHotEncoder + weights per category
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
cat_matrix = encoder.fit_transform(df[categorical_features])

cat_weights = {
    'mapped_area': 0.20,
    'area_type': 0.10,
    'property_age': 0.05,
    'property_type': 0.10,
    'furnishing_status': 0.02,
    'facing': 0.01
}

start = 0
for feature in categorical_features:
    n_cols = len(encoder.categories_[categorical_features.index(feature)])
    cat_matrix[:, start:start+n_cols] *= (cat_weights[feature] / n_cols)
    start += n_cols

# Combine and compute similarity matrix
X = np.hstack([num_matrix, cat_matrix])
similarity_matrix = cosine_similarity(X)

# Recommendation function
def get_similar_properties(property_idx, top_n=5):
    sim_scores = list(enumerate(similarity_matrix[property_idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    similar_indices = [i for i, score in sim_scores[1:top_n+1]]
    return similar_indices

# ------------------------------
# 3. Global min/max for sliders
# ------------------------------
GLOBAL_MIN_PRICE = 7
GLOBAL_MAX_PRICE = 500
GLOBAL_MIN_AREA = 210
GLOBAL_MAX_AREA = 9000

# ------------------------------
# 4. Dash app (unchanged from your original)
# ------------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# ---- Dropdown options ----
location_counts = df['mapped_area'].value_counts()
location_options = [{'label': loc, 'value': loc} for loc in location_counts.index]

# ---- Layout ----
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# ---- Page renderer ----
@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname is None or pathname == '/':
        return render_search_page()
    elif pathname.startswith('/property/'):
        try:
            idx = int(pathname.split('/')[-1])
        except:
            return html.Div("Invalid property ID.")
        return render_detail_page(idx)
    else:
        return html.Div("Page not found")

# ---- Helper function for location-specific stats ----
def get_location_stats(location):
    loc_df = df[df['mapped_area'] == location]
    if loc_df.empty:
        return {
            'price_min': GLOBAL_MIN_PRICE,
            'price_max': GLOBAL_MAX_PRICE,
            'area_min': GLOBAL_MIN_AREA,
            'area_max': GLOBAL_MAX_AREA,
            'bedrooms': [],
            'statuses': [],
            'bathrooms': [],
            'balconies': []
        }
    return {
        'price_min': int(loc_df['price_inr_in_lakhs'].min()),
        'price_max': int(loc_df['price_inr_in_lakhs'].max()),
        'area_min': int(loc_df['area_sqft'].min()),
        'area_max': int(loc_df['area_sqft'].max()),
        'bedrooms': sorted(loc_df['bedrooms'].unique()),
        'statuses': sorted(loc_df['property_status'].unique()),
        'bathrooms': sorted(loc_df['bathrooms'].unique()),
        'balconies': sorted(loc_df['balconies'].unique())
    }

# ---- Search page ----
def render_search_page():
    return html.Div([
        html.H1("🏠 Real Estate Property Finder", style={'textAlign': 'center'}),
        html.Hr(),

        # Location
        html.Div([
            html.Label("📍 Location (required)", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='location-dropdown',
                options=location_options,
                value='Gift City',
                placeholder="Select location",
                style={'width': '300px', 'margin': 'auto'}
            ),
        ], style={'textAlign': 'center', 'margin': '10px'}),

        # Budget slider
        html.Div([
            html.Label("💰 Budget (Lakhs)", style={'fontWeight': 'bold'}),
            dcc.RangeSlider(
                id='budget-slider',
                min=GLOBAL_MIN_PRICE,
                max=GLOBAL_MAX_PRICE,
                step=1,
                value=[GLOBAL_MIN_PRICE, GLOBAL_MAX_PRICE],
                marks={i: str(i) for i in range(50, 501, 50)}
            ),
        ], style={'padding': '10px', 'width': '80%', 'margin': 'auto'}),
        dcc.Loading(
            id="loading-price",
            type="default",
            children=dcc.Graph(id='price-histogram', style={'height': '250px'})
        ),

        # Bedrooms
        html.Div([
            html.Label("🛏️ Bedrooms:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Checklist(
                id='bedroom-checklist',
                options=[],  # will be set by callback
                value=[],
                inline=True
            ),
        ], style={'margin': '10px', 'textAlign': 'center'}),

        # Construction Status
        html.Div([
            html.Label("🔑 Construction Status:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.RadioItems(
                id='status-radio',
                options=[],  # will be set by callback
                value=None,
                inline=True
            ),
        ], style={'margin': '10px', 'textAlign': 'center'}),

        # Toggle Advanced
        html.Div([
            html.Button("🔧 Show Advanced Filters", id='toggle-advanced', n_clicks=0,
                        style={'margin': '10px', 'padding': '8px 20px'})
        ], style={'textAlign': 'center'}),

        # Advanced filters (hidden by default)
        html.Div(id='advanced-filters', style={'display': 'none'}, children=[
            # Area slider
            html.Div([
                html.Label("📐 Area (sqft)", style={'fontWeight': 'bold'}),
                dcc.RangeSlider(
                    id='area-slider',
                    min=GLOBAL_MIN_AREA,
                    max=GLOBAL_MAX_AREA,
                    step=10,
                    value=[GLOBAL_MIN_AREA, GLOBAL_MAX_AREA],
                    marks={i: str(i) for i in range(1000, 9001, 1000)}
                ),
            ], style={'padding': '10px', 'width': '80%', 'margin': 'auto'}),
            dcc.Loading(
                id="loading-area",
                type="default",
                children=dcc.Graph(id='area-histogram', style={'height': '250px'})
            ),

            # Area Type
            html.Div([
                html.Label("🏷️ Area Type:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.RadioItems(
                    id='area-type-radio',
                    options=[
                        {'label': 'Any', 'value': ''},
                        {'label': 'Super Built-up', 'value': 'Super Built-up'},
                        {'label': 'Carpet', 'value': 'Carpet'},
                        {'label': 'Built-up', 'value': 'Built-up'}
                    ],
                    value='',
                    inline=True
                ),
            ], style={'margin': '10px', 'textAlign': 'center'}),

            # Bathrooms
            html.Div([
                html.Label("🚽 Bathrooms:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Checklist(
                    id='bathrooms-checklist',
                    options=[],  # will be set by callback
                    value=[],
                    inline=True
                ),
            ], style={'margin': '10px', 'textAlign': 'center'}),

            # Balconies
            html.Div([
                html.Label("🪟 Balconies:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Checklist(
                    id='balconies-checklist',
                    options=[],  # will be set by callback
                    value=[],
                    inline=True
                ),
            ], style={'margin': '10px', 'textAlign': 'center'}),

            # Property Age
            html.Div([
                html.Label("📅 Property Age:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Checklist(
                    id='age-checklist',
                    options=[
                        {'label': 'New', 'value': 'New'},
                        {'label': '1-5 years', 'value': '1-5 years'},
                        {'label': '5-10 years', 'value': '5-10 years'},
                        {'label': '10-20 years', 'value': '10-20 years'}
                    ],
                    value=[],
                    inline=True
                ),
            ], style={'margin': '10px', 'textAlign': 'center'}),

            # Furnishing
            html.Div([
                html.Label("🛋️ Furnishing:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.RadioItems(
                    id='furnishing-radio',
                    options=[
                        {'label': 'Any', 'value': ''},
                        {'label': 'Unfurnished', 'value': 'unfurnished'},
                        {'label': 'Semi-furnished', 'value': 'semi-furnished'},
                        {'label': 'Furnished', 'value': 'furnished'}
                    ],
                    value='',
                    inline=True
                ),
            ], style={'margin': '10px', 'textAlign': 'center'}),
        ]),

        html.Div(id='property-cards', style={'margin': '20px'}),
    ])

# ---- Detail page ----
def render_detail_page(property_index):
    if property_index not in df.index:
        return html.Div("Property not found.")
    prop = df.loc[property_index]

    details = html.Div([
        html.H2(f"📍 {prop['mapped_area']} – {prop['bedrooms']} BHK", style={'marginBottom': '20px'}),
        html.Div([
            html.P(f"💰 Price: ₹{prop['price_inr_in_lakhs']:.1f} Lakhs"),
            html.P(f"📐 Area: {prop['area_sqft']} sqft • {prop['area_type']}"),
            html.P(f"🛏️ Bedrooms: {prop['bedrooms']}"),
            html.P(f"🚽 Bathrooms: {prop['bathrooms']}"),
            html.P(f"🪟 Balconies: {prop['balconies']}"),
            html.P(f"🔑 Property Status: {prop['property_status']}"),
            html.P(f"📅 Property Age: {prop['property_age']}"),
            html.P(f"🛋️ Furnishing: {prop['furnishing_status']}"),
            html.P(f"🧭 Facing: {prop['facing']}"),
            html.P(f"🏢 Current Floor: {prop['current_floor']}"),
            html.P(f"📊 Total Floors: {prop['total_floors']}"),
            html.P(f"🏷️ Floor Category: {prop.get('floor_category', 'N/A')}"),
            html.P(f"📝 Description: {prop['description']}"),
            html.P(["🔗 Link: ", html.A(prop['property_url'], href=prop['property_url'], target='_blank')]),
        ], style={'fontSize': '16px', 'lineHeight': '1.8'}),
        html.Hr(),
        html.H3("🔗 Top 5 Similar Properties"),
        build_similar_table(property_index),
        html.Br(),
        html.A("← Back to Search", href='/', style={'fontSize': '18px'})
    ])
    return details

def build_similar_table(property_index):
    similar_indices = get_similar_properties(property_index, top_n=5)
    similar_df = df.loc[similar_indices].copy()
    sim_scores = [similarity_matrix[property_index][i] for i in similar_indices]
    similar_df['Similarity'] = np.round(sim_scores, 4)

    display_cols = ['mapped_area', 'price_inr_in_lakhs', 'area_sqft', 'bedrooms',
                    'property_status', 'property_url', 'Similarity']
    display_cols = [c for c in display_cols if c in similar_df.columns]

    table_data = []
    for _, row in similar_df.iterrows():
        row_dict = row[display_cols].to_dict()
        url = row_dict.get('property_url', '#')
        row_dict['property_url'] = f'[{url}]({url})' if url != '#' else '[No URL](#)'
        table_data.append(row_dict)

    column_defs = [
        {'id': 'mapped_area', 'name': 'Area'},
        {'id': 'price_inr_in_lakhs', 'name': 'Price (Lakhs)'},
        {'id': 'area_sqft', 'name': 'Sqft'},
        {'id': 'bedrooms', 'name': 'Beds'},
        {'id': 'property_status', 'name': 'Status'},
        {'id': 'property_url', 'name': 'URL', 'presentation': 'markdown'},
        {'id': 'Similarity', 'name': 'Similarity Score'},
    ]
    column_defs = [c for c in column_defs if c['id'] in display_cols]

    return dash_table.DataTable(
        columns=column_defs,
        data=table_data,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
        style_header={'backgroundColor': 'lightblue', 'fontWeight': 'bold'},
        markdown_options={'html': True}
    )

# ------------------------------
# Callback: Update filters dynamically based on location
# ------------------------------
@callback(
    Output('budget-slider', 'min'),
    Output('budget-slider', 'max'),
    Output('budget-slider', 'value'),
    Output('budget-slider', 'marks'),
    Output('area-slider', 'min'),
    Output('area-slider', 'max'),
    Output('area-slider', 'value'),
    Output('area-slider', 'marks'),
    Output('bedroom-checklist', 'options'),
    Output('bedroom-checklist', 'value'),
    Output('status-radio', 'options'),
    Output('status-radio', 'value'),
    Output('bathrooms-checklist', 'options'),
    Output('bathrooms-checklist', 'value'),
    Output('balconies-checklist', 'options'),
    Output('balconies-checklist', 'value'),
    Input('location-dropdown', 'value')
)
def update_filters(location):
    if not location:
        stats = {
            'price_min': GLOBAL_MIN_PRICE,
            'price_max': GLOBAL_MAX_PRICE,
            'area_min': GLOBAL_MIN_AREA,
            'area_max': GLOBAL_MAX_AREA,
            'bedrooms': [],
            'statuses': [],
            'bathrooms': [],
            'balconies': []
        }
    else:
        stats = get_location_stats(location)

    # Budget slider
    price_min = stats['price_min']
    price_max = stats['price_max']
    budget_value = [price_min, price_max]
    if price_max - price_min > 100:
        step = 50
    else:
        step = 20
    marks = {i: str(i) for i in range(int(price_min // step * step), price_max + 1, step)}
    marks[price_min] = str(price_min)
    marks[price_max] = str(price_max)

    # Area slider
    area_min = stats['area_min']
    area_max = stats['area_max']
    area_value = [area_min, area_max]
    area_step = 500 if (area_max - area_min) > 1000 else 200
    area_marks = {i: str(i) for i in range(int(area_min // area_step * area_step), area_max + 1, area_step)}
    area_marks[area_min] = str(area_min)
    area_marks[area_max] = str(area_max)

    # Bedrooms
    bedroom_options = [{'label': f"{b} BHK", 'value': b} for b in stats['bedrooms']]
    bedroom_value = []

    # Status
    status_options = [{'label': s.replace('_', ' '), 'value': s} for s in stats['statuses']]
    status_value = None

    # Bathrooms
    bathroom_options = [{'label': str(b), 'value': b} for b in stats['bathrooms']]
    bathroom_value = []

    # Balconies
    balcony_options = [{'label': str(b), 'value': b} for b in stats['balconies']]
    balcony_value = []

    return (
        price_min, price_max, budget_value, marks,
        area_min, area_max, area_value, area_marks,
        bedroom_options, bedroom_value,
        status_options, status_value,
        bathroom_options, bathroom_value,
        balcony_options, balcony_value
    )

# ---- Toggle advanced filters ----
@callback(
    Output('advanced-filters', 'style'),
    Input('toggle-advanced', 'n_clicks')
)
def toggle_advanced(n_clicks):
    if n_clicks is None or n_clicks % 2 == 0:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

# ---- Main update callback ----
@callback(
    Output('price-histogram', 'figure'),
    Output('area-histogram', 'figure'),
    Output('property-cards', 'children'),
    Input('location-dropdown', 'value'),
    Input('budget-slider', 'value'),
    Input('area-slider', 'value'),
    Input('bedroom-checklist', 'value'),
    Input('status-radio', 'value'),
    Input('area-type-radio', 'value'),
    Input('bathrooms-checklist', 'value'),
    Input('balconies-checklist', 'value'),
    Input('age-checklist', 'value'),
    Input('furnishing-radio', 'value'),
    prevent_initial_call=False
)
def update_search(location, budget_range, area_range, bedrooms, status,
                  area_type, bathrooms, balconies, ages, furnishing):
    # Defaults
    if budget_range is None:
        budget_range = [GLOBAL_MIN_PRICE, GLOBAL_MAX_PRICE]
    if area_range is None:
        area_range = [GLOBAL_MIN_AREA, GLOBAL_MAX_AREA]

    low_price, high_price = budget_range
    low_area, high_area = area_range

    mask = pd.Series(True, index=df.index)

    if not location:
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Select a location", height=250)
        empty_cards = html.Div("Please select a location.", style={'textAlign': 'center'})
        return empty_fig, empty_fig, empty_cards

    mask &= (df['mapped_area'] == location)
    mask &= (df['price_inr_in_lakhs'] >= low_price) & (df['price_inr_in_lakhs'] <= high_price)
    mask &= (df['area_sqft'] >= low_area) & (df['area_sqft'] <= high_area)

    if bedrooms:
        mask &= (df['bedrooms'].isin(bedrooms))
    if status:
        mask &= (df['property_status'] == status)
    if area_type:
        mask &= (df['area_type'] == area_type)
    if bathrooms:
        mask &= (df['bathrooms'].isin(bathrooms))
    if balconies:
        mask &= (df['balconies'].isin(balconies))
    if ages:
        mask &= (df['property_age'].isin(ages) | (df['property_age'] == 'Unknown'))
    if furnishing:
        mask &= (df['furnishing_status'] == furnishing)

    filtered = df.loc[mask]

    # ---- Price histogram ----
    prices = df['price_inr_in_lakhs']
    price_bins = np.histogram_bin_edges(prices, bins='auto')
    price_bins = np.concatenate([[GLOBAL_MIN_PRICE], price_bins[price_bins > GLOBAL_MIN_PRICE]])
    price_bins = np.concatenate([price_bins[price_bins < GLOBAL_MAX_PRICE], [GLOBAL_MAX_PRICE]])

    fig_price = go.Figure()
    fig_price.add_trace(go.Histogram(
        x=prices,
        xbins=dict(start=price_bins[0], end=price_bins[-1], size=price_bins[1]-price_bins[0]),
        marker_color='skyblue',
        opacity=0.6,
        name='All Properties'
    ))
    fig_price.add_vrect(x0=low_price, x1=high_price, fillcolor='red', opacity=0.15, layer='below', line_width=0)
    fig_price.add_vline(x=low_price, line_dash='dash', line_color='red', line_width=2)
    fig_price.add_vline(x=high_price, line_dash='dash', line_color='red', line_width=2)
    fig_price.add_annotation(x=low_price, y=1, xref='x', yref='paper', text=f"Min: {low_price}L",
                             showarrow=False, font=dict(color='red', size=12), bgcolor='white', bordercolor='red', borderwidth=1)
    fig_price.add_annotation(x=high_price, y=1, xref='x', yref='paper', text=f"Max: {high_price}L",
                             showarrow=False, font=dict(color='red', size=12), bgcolor='white', bordercolor='red', borderwidth=1)
    fig_price.update_layout(title='Price Distribution', xaxis_title='Price (Lakhs)', yaxis_title='Count',
                            bargap=0.05, xaxis=dict(range=[GLOBAL_MIN_PRICE, GLOBAL_MAX_PRICE]),
                            height=250, margin=dict(l=40, r=40, t=50, b=40))

    # ---- Area histogram ----
    areas = df['area_sqft']
    area_bins = np.histogram_bin_edges(areas, bins='auto')
    area_bins = np.concatenate([[GLOBAL_MIN_AREA], area_bins[area_bins > GLOBAL_MIN_AREA]])
    area_bins = np.concatenate([area_bins[area_bins < GLOBAL_MAX_AREA], [GLOBAL_MAX_AREA]])

    fig_area = go.Figure()
    fig_area.add_trace(go.Histogram(
        x=areas,
        xbins=dict(start=area_bins[0], end=area_bins[-1], size=area_bins[1]-area_bins[0]),
        marker_color='lightgreen',
        opacity=0.6,
        name='All Properties'
    ))
    fig_area.add_vrect(x0=low_area, x1=high_area, fillcolor='red', opacity=0.15, layer='below', line_width=0)
    fig_area.add_vline(x=low_area, line_dash='dash', line_color='red', line_width=2)
    fig_area.add_vline(x=high_area, line_dash='dash', line_color='red', line_width=2)
    fig_area.add_annotation(x=low_area, y=1, xref='x', yref='paper', text=f"Min: {low_area} sqft",
                            showarrow=False, font=dict(color='red', size=12), bgcolor='white', bordercolor='red', borderwidth=1)
    fig_area.add_annotation(x=high_area, y=1, xref='x', yref='paper', text=f"Max: {high_area} sqft",
                            showarrow=False, font=dict(color='red', size=12), bgcolor='white', bordercolor='red', borderwidth=1)
    fig_area.update_layout(title='Area Distribution', xaxis_title='Area (sqft)', yaxis_title='Count',
                           bargap=0.05, xaxis=dict(range=[GLOBAL_MIN_AREA, GLOBAL_MAX_AREA]),
                           height=250, margin=dict(l=40, r=40, t=50, b=40))

    # ---- Property cards ----
    if filtered.empty:
        cards = html.Div("😕 No properties match your filters.", style={'textAlign': 'center', 'fontSize': '18px'})
    else:
        cards = []
        for idx, row in filtered.iterrows():
            card = html.Div([
                html.H4(f"{row['mapped_area']} – {row['bedrooms']} BHK", style={'margin': '5px 0'}),
                html.P(f"💰 ₹{row['price_inr_in_lakhs']:.1f} Lakhs", style={'fontWeight': 'bold'}),
                html.P(f"📐 {row['area_sqft']} sqft • {row['area_type']}"),
                dcc.Link("View More Details", href=f"/property/{idx}",
                         style={'display': 'inline-block', 'marginTop': '10px', 'padding': '6px 12px',
                                'backgroundColor': '#007bff', 'color': 'white', 'textDecoration': 'none',
                                'borderRadius': '4px'})
            ], style={'padding': '15px'})
            cards.append(html.Div(card, style={
                'border': '1px solid #ccc', 'borderRadius': '8px', 'margin': '10px',
                'padding': '5px', 'width': '280px', 'display': 'inline-block',
                'verticalAlign': 'top', 'backgroundColor': '#f9f9f9',
                'boxShadow': '2px 2px 8px rgba(0,0,0,0.1)'
            }))
        cards = html.Div(cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})

    return fig_price, fig_area, cards

# ------------------------------
# 5. Run
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True, dev_tools_hot_reload=False, port=5555)