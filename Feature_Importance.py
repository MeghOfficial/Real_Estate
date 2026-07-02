import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table

# ------------------------------------------------------------
# 1. Load data and train model (same as before)
# ------------------------------------------------------------
df = pd.read_csv('data/gandhinagar_property_apartments_recommender_ready.csv')

numerical = [
    'area_sqft', 'bathrooms', 'bedrooms', 'balconies',
    'current_floor', 'total_floors'
]
categorical = [
    'mapped_area', 'facing', 'property_status',
    'area_type', 'property_age', 'property_type'
]

X = df.drop(columns=['price_inr_in_lakhs'])
y = df['price_inr_in_lakhs']
y_transformed = np.log(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_transformed, test_size=0.2, random_state=42
)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical),
        ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), categorical)
    ]
)

ridge_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', Ridge(alpha=10))
])
ridge_pipeline.fit(X_train, y_train)

# ------------------------------------------------------------
# 2. Feature importance (percentage impact)
# ------------------------------------------------------------
feature_names = ridge_pipeline.named_steps['preprocessor'].get_feature_names_out()
coefficients = ridge_pipeline.named_steps['model'].coef_

importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Coefficient': coefficients
})
importance_df['Importance'] = importance_df['Coefficient'].abs()
importance_df = importance_df.sort_values('Importance', ascending=False)

scaler = ridge_pipeline.named_steps['preprocessor'].named_transformers_['num']
std_dict = dict(zip(numerical, scaler.scale_))

def get_percentage_impact(row):
    coef = row['Coefficient']
    feature = row['Feature']
    if feature in std_dict:
        return (np.exp(coef / std_dict[feature]) - 1) * 100
    else:
        return (np.exp(coef) - 1) * 100

importance_df['Percentage_Impact'] = importance_df.apply(get_percentage_impact, axis=1)
importance_df['Percentage_Impact'] = importance_df['Percentage_Impact'].round(2)

# Keep only top 20 for display
top_features = importance_df.head(20)[['Feature', 'Coefficient', 'Percentage_Impact']].reset_index(drop=True)

# ------------------------------------------------------------
# 3. Prepare possible values for dropdowns (from training data)
# ------------------------------------------------------------
cat_options = {}
for col in categorical:
    cat_options[col] = sorted(X_train[col].dropna().unique().tolist())

# ------------------------------------------------------------
# 4. Build Dash app
# ------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Property Price Simulator"

# Layout
app.layout = dbc.Container([
    html.H1("🏠 Property Price Simulator & Feature Importance", className="my-4 text-center"),

    dbc.Row([
        dbc.Col([
            html.H4("Feature Importance (Top 20)"),
            dash_table.DataTable(
                id='importance-table',
                columns=[
                    {"name": "Feature", "id": "Feature"},
                    {"name": "Coefficient", "id": "Coefficient"},
                    {"name": "% Impact on Price", "id": "Percentage_Impact"}
                ],
                data=top_features.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
                page_size=10
            )
        ], width=6),

        dbc.Col([
            html.H4("What‑If Simulator"),
            html.P("Adjust the sliders and dropdowns to see the estimated price."),
            # Sliders
            dbc.Row([
                dbc.Col([
                    html.Label("Area (sq ft)"),
                    dcc.Slider(
                        id='area-slider',
                        min=int(X_train['area_sqft'].min()),
                        max=int(X_train['area_sqft'].max()),
                        step=50,
                        value=int(X_train['area_sqft'].median()),
                        marks={int(X_train['area_sqft'].min()): str(int(X_train['area_sqft'].min())),
                               int(X_train['area_sqft'].median()): str(int(X_train['area_sqft'].median())),
                               int(X_train['area_sqft'].max()): str(int(X_train['area_sqft'].max()))}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Bedrooms"),
                    dcc.Slider(
                        id='bedrooms-slider',
                        min=int(X_train['bedrooms'].min()),
                        max=int(X_train['bedrooms'].max()),
                        step=1,
                        value=int(X_train['bedrooms'].median()),
                        marks={int(X_train['bedrooms'].min()): str(int(X_train['bedrooms'].min())),
                               int(X_train['bedrooms'].max()): str(int(X_train['bedrooms'].max()))}
                    )
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    html.Label("Bathrooms"),
                    dcc.Slider(
                        id='bathrooms-slider',
                        min=int(X_train['bathrooms'].min()),
                        max=int(X_train['bathrooms'].max()),
                        step=1,
                        value=int(X_train['bathrooms'].median()),
                        marks={int(X_train['bathrooms'].min()): str(int(X_train['bathrooms'].min())),
                               int(X_train['bathrooms'].max()): str(int(X_train['bathrooms'].max()))}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Balconies"),
                    dcc.Slider(
                        id='balconies-slider',
                        min=int(X_train['balconies'].min()),
                        max=int(X_train['balconies'].max()),
                        step=1,
                        value=int(X_train['balconies'].median()),
                        marks={int(X_train['balconies'].min()): str(int(X_train['balconies'].min())),
                               int(X_train['balconies'].max()): str(int(X_train['balconies'].max()))}
                    )
                ], width=6)
            ]),
            html.Hr(),
            html.Label("Categorical Features", className="font-weight-bold"),
            dbc.Row([
                dbc.Col([
                    html.Label("Facing"),
                    dcc.Dropdown(
                        id='facing-dropdown',
                        options=[{'label': v, 'value': v} for v in cat_options['facing']],
                        value=cat_options['facing'][0]
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Property Status"),
                    dcc.Dropdown(
                        id='status-dropdown',
                        options=[{'label': v, 'value': v} for v in cat_options['property_status']],
                        value=cat_options['property_status'][0]
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Area Type"),
                    dcc.Dropdown(
                        id='area-type-dropdown',
                        options=[{'label': v, 'value': v} for v in cat_options['area_type']],
                        value=cat_options['area_type'][0]
                    )
                ], width=4)
            ]),
            dbc.Row([
                dbc.Col([
                    html.Label("Property Age"),
                    dcc.Dropdown(
                        id='age-dropdown',
                        options=[{'label': v, 'value': v} for v in cat_options['property_age']],
                        value=cat_options['property_age'][0]
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Property Type"),
                    dcc.Dropdown(
                        id='type-dropdown',
                        options=[{'label': v, 'value': v} for v in cat_options['property_type']],
                        value=cat_options['property_type'][0]
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Mapped Area"),
                    dcc.Dropdown(
                        id='mapped-area-dropdown',
                        options=[{'label': v, 'value': v} for v in cat_options['mapped_area']],
                        value=cat_options['mapped_area'][0]
                    )
                ], width=4)
            ]),
            html.Hr(),
            # Output area
            dbc.Card([
                dbc.CardBody([
                    html.H5("Current Estimate", className="card-title"),
                    html.Div(id='prediction-output', style={'fontSize': '20px', 'fontWeight': 'bold'})
                ])
            ], color="light", className="mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.H5("🔄 What‑If Scenario", className="card-title"),
                    html.Div(id='whatif-output')
                ])
            ], color="info", className="mb-3")
        ], width=6)
    ])
], fluid=True)


# ------------------------------------------------------------
# 5. Helper function to predict
# ------------------------------------------------------------
def predict_price(area, bedrooms, bathrooms, balconies,
                  facing, status, area_type, age, prop_type, mapped_area):
    input_data = pd.DataFrame({
        'area_sqft': [area],
        'bedrooms': [bedrooms],
        'bathrooms': [bathrooms],
        'balconies': [balconies],
        'current_floor': [1],        # fixed – can add more sliders if needed
        'total_floors': [5],         # fixed
        'facing': [facing],
        'property_status': [status],
        'area_type': [area_type],
        'property_age': [age],
        'property_type': [prop_type],
        'mapped_area': [mapped_area]
    })
    log_pred = ridge_pipeline.predict(input_data)[0]
    return np.exp(log_pred)


# ------------------------------------------------------------
# 6. Callbacks
# ------------------------------------------------------------
@app.callback(
    [Output('prediction-output', 'children'),
     Output('whatif-output', 'children')],
    [Input('area-slider', 'value'),
     Input('bedrooms-slider', 'value'),
     Input('bathrooms-slider', 'value'),
     Input('balconies-slider', 'value'),
     Input('facing-dropdown', 'value'),
     Input('status-dropdown', 'value'),
     Input('area-type-dropdown', 'value'),
     Input('age-dropdown', 'value'),
     Input('type-dropdown', 'value'),
     Input('mapped-area-dropdown', 'value')]
)
def update_simulator(area, bedrooms, bathrooms, balconies,
                     facing, status, area_type, age, prop_type, mapped_area):
    # Current price
    current_price = predict_price(area, bedrooms, bathrooms, balconies,
                                  facing, status, area_type, age, prop_type, mapped_area)

    # What‑If: add 200 sqft, +1 bedroom, +1 bathroom, change status to "Ready to Move" if possible
    new_area = area + 200
    new_bedrooms = bedrooms + 1
    new_bathrooms = bathrooms + 1
    new_status = "Ready to Move"
    if new_status not in cat_options['property_status']:
        new_status = status  # fallback

    # Ensure new values don't exceed max (optional)
    new_area = min(new_area, X_train['area_sqft'].max())
    new_bedrooms = min(new_bedrooms, X_train['bedrooms'].max())
    new_bathrooms = min(new_bathrooms, X_train['bathrooms'].max())

    new_price = predict_price(new_area, new_bedrooms, new_bathrooms, balconies,
                              facing, new_status, area_type, age, prop_type, mapped_area)

    price_change = new_price - current_price

    # Format output
    current_str = f"₹ {current_price:,.2f} Lakhs"
    whatif_str = html.Div([
        html.P(f"Area: {area} → {new_area} sq ft (+200)"),
        html.P(f"Bedrooms: {bedrooms} → {new_bedrooms} (+1)"),
        html.P(f"Bathrooms: {bathrooms} → {new_bathrooms} (+1)"),
        html.P(f"Status: {status} → {new_status}"),
        html.Hr(),
        html.P(f"New Price: ₹ {new_price:,.2f} Lakhs", style={'fontWeight': 'bold'}),
        html.P(f"Change: + ₹ {price_change:,.2f} Lakhs", style={'color': 'green' if price_change > 0 else 'red'})
    ])

    return current_str, whatif_str


# ------------------------------------------------------------
# 7. Run the app
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True,port=5588)