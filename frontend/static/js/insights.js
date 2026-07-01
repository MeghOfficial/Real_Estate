const impactColors = {
    "Very High": "#dc2626",
    "High": "#ea580c",
    "Moderate": "#ca8a04",
    "Low": "#16a34a",
    "Very Low": "#2563eb",
};

const importanceSymbols = {
    "Very High": "🔴",
    "High": "🟠",
    "Moderate": "🟡",
    "Low": "🟢",
    "Very Low": "🔵",
};

const state = {
    data: { numerical: {}, categorical: {} },
};

const predictionFeatureLabels = {
    area_sqft: "Property Area (sq ft)",
    bedrooms: "Bedrooms",
    bathrooms: "Bathrooms",
    balconies: "Balconies",
    current_floor: "Floor Number",
    total_floors: "Total Floors in Building",
    furnishing_status: "Furnishing",
    mapped_area: "Location",
    facing: "Property Facing",
    property_age: "Age of Property",
    area_type: "Area Measurement Type",
    property_status: "Availability",
};

const els = {
    category: document.getElementById("categoryDropdown"),
    feature: document.getElementById("featureDropdown"),
    card: document.getElementById("insightCard"),
    message: document.getElementById("message"),
};

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;",
    }[char]));
}

function markdown(value) {
    return escapeHtml(value)
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
}

function featureLabel(key, fallback = "") {
    return predictionFeatureLabels[key] || fallback || key;
}

function moneyLakhs(value) {
    return `Rs. ${Number(value || 0).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })} Lakhs`;
}

function signedMoney(value) {
    const number = Number(value || 0);
    const sign = number > 0 ? "+" : "";
    return `${sign}${moneyLakhs(number)}`;
}

function impactClass(value) {
    return String(value || "").includes("-") ? "negative" : "positive";
}

function impactNumber(value) {
    return Number(String(value || "0").replace("%", ""));
}

function section(title, body, extraClass = "") {
    return `
        <section class="section-box ${extraClass}">
            <h3>${escapeHtml(title)}</h3>
            ${body}
        </section>
    `;
}

function renderFeatureOptions() {
    const category = els.category.value;
    const features = state.data[category] || {};
    const options = Object.entries(features).map(([key, item]) => {
        // prefer display_name (may contain emoji) then short_name then fallback label
        const rawLabel = item.display_name || item.short_name || featureLabel(key);
        // robustly strip any leading non-alphanumeric characters and whitespace for dropdown readability
        const stripped = String(rawLabel).replace(/^[^A-Za-z0-9]+/, "").trim();
        const label = stripped || rawLabel;
        return `<option value="${escapeHtml(key)}">${escapeHtml(label)}</option>`;
    });

    els.feature.innerHTML = options.join("");
    renderSelectedFeature();
}

function renderNumerical(key) {
    const data = state.data.numerical[key];
    if (!data) return "";
    const color = impactColors[data.impact_level] || "#2563eb";
    const rawTitle = data.display_name || data.short_name || featureLabel(key);
    const match = String(rawTitle).trim().match(/^([\u{1F300}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}])?\s*(.*)$/u);
    const featureSymbol = match && match[1] ? match[1] : "";
    const title = match && match[2] ? match[2] : rawTitle;
    const importanceSymbol = importanceSymbols[data.impact_level] || "";
    const importanceClass = `importance-${String(data.impact_level || "").toLowerCase().replace(/\s+/g, "-")}`;
    return `
        <div class="card-header">
            <h2><span class="feature-symbol">${escapeHtml(featureSymbol)}</span>${escapeHtml(title)}</h2>
            <div class="impact-card">
                <div class="impact-item">
                    <span class="impact-label">Impact:</span>
                    <strong class="impact-value" style="color:${color}">${escapeHtml(data.impact)}</strong>
                </div>
                <div class="impact-item">
                    <span class="impact-label">Importance:</span>
                    <strong class="impact-value ${escapeHtml(importanceClass)}">${escapeHtml(data.impact_level)}</strong>
                </div>
            </div>
        </div>
        <div class="content-grid">
            ${section("Explanation", `<p>${markdown(data.explanation)}</p>`)}
            ${section("Example Scenario", `
                <div class="scenario-grid">
                    <div class="stat-card">
                        <span>Current Property</span>
                        <strong>${escapeHtml(data.current_value)} ${escapeHtml(data.short_name)}</strong>
                        <p>${moneyLakhs(data.current_price)}</p>
                    </div>
                    <div class="stat-card">
                        <span>After Adding 1</span>
                        <strong>${escapeHtml(data.new_value)} ${escapeHtml(data.short_name)}</strong>
                        <p>${moneyLakhs(data.new_price)}</p>
                    </div>
                    <div class="stat-card">
                        <span>Estimated Increase</span>
                        <strong class="positive">${signedMoney(data.increase)}</strong>
                    </div>
                </div>
            `)}
            ${section("Business Insight", `
                <div class="insight-grid">
                    <div class="mini-card">
                        <h4>Market Insight</h4>
                        <p>${escapeHtml(data.market_insight)}</p>
                    </div>
                    <div class="mini-card">
                        <h4>Buyer Insight</h4>
                        <p>${escapeHtml(data.buyer_insight)}</p>
                    </div>
                    <div class="mini-card">
                        <h4>Seller Insight</h4>
                        <p>${escapeHtml(data.seller_insight)}</p>
                    </div>
                </div>
            `)}
            ${section("Important Note", `
                <p>This does not mean every property will increase by exactly the stated percentage. The estimate comes from the machine learning model and assumes all other factors remain unchanged. The impact shown represents the average relationship learned from the training data.</p>
            `, "note")}
        </div>
    `;
}

function renderValueTable(data, key) {
    const values = { ...(data.values || {}) };
    if (data.baseline && !values[data.baseline]) {
        values[data.baseline] = { impact: "0.00%" };
    }

    const filteredKeys = new Set();
    if (key === "property_age") filteredKeys.add("Unknown");
    if (key === "facing") filteredKeys.add("Other");

    const rows = Object.entries(values)
        .filter(([name]) => !filteredKeys.has(name))
        .sort(([, first], [, second]) => impactNumber(second.impact) - impactNumber(first.impact))
        .map(([name, values]) => `
            <tr>
                <td><strong>${escapeHtml(name)}</strong></td>
                <td class="${impactClass(values.impact)}">${escapeHtml(values.impact)}</td>
            </tr>
        `).join("");

    return `
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Price Impact</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderExamples(data, key) {
    const examples = (data.examples || []).filter((item) => {
        if (key === "property_age") return item.age !== "Unknown";
        if (key === "facing") return item.direction !== "Other";
        return true;
    });
    if (!examples.length) return "<p>No examples available.</p>";

    if ("from" in examples[0]) {
        return `<div class="example-grid">${examples.map((item) => `
            <div class="stat-card">
                <span>${escapeHtml(item.from)} to ${escapeHtml(item.to)}</span>
                <strong>${moneyLakhs(item.price)}</strong>
                <p class="${Number(item.change) >= 0 ? "positive" : "negative"}">${signedMoney(item.change)}</p>
            </div>
        `).join("")}</div>`;
    }

    const rows = examples.map((item) => {
        const label = item.type || item.status || item.age || item.direction || "";
        const area = item.area_sqft ? `<td>${escapeHtml(item.area_sqft)}</td>` : "";
        return `
            <tr>
                ${area}
                <td>${escapeHtml(label)}</td>
                <td>${moneyLakhs(item.price)}</td>
            </tr>
        `;
    }).join("");

    const hasArea = "area_sqft" in examples[0];
    return `
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        ${hasArea ? "<th>Area Sqft</th>" : ""}
                        <th>Category</th>
                        <th>Estimated Price</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderCategorical(key) {
    const data = state.data.categorical[key];
    if (!data) return "";
    // extract leading symbol (emoji) and stripped title for header, show symbol only in note
    const rawTitle = data.display_name || data.short_name || featureLabel(key);
    const match = String(rawTitle).trim().match(/^([\u{1F300}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}])?\s*(.*)$/u);
    const featureSymbol = match && match[1] ? match[1] : "";
    const title = match && match[2] ? match[2] : rawTitle;

    const importanceSymbol = importanceSymbols[data.importance || data.importance_level] || importanceSymbols[data.importance || data.importance_level] || "";
    const importanceValue = data.importance || data.importance_level || "Low";
    const importanceClass = `importance-${String(importanceValue).toLowerCase().replace(/\s+/g, "-")}`;

    return `
        <div class="card-header">
            <h2><span class="feature-symbol">${escapeHtml(featureSymbol)}</span>${escapeHtml(title)}</h2>
            <div class="impact-card">
                <div class="impact-item">
                    <span class="impact-label">Reference Category:</span>
                    <strong class="impact-value">${escapeHtml(data.baseline)}</strong>
                </div>
                <div class="impact-item">
                    <span class="impact-label">Importance:</span>
                    <strong class="impact-value ${escapeHtml(importanceClass)}">${escapeHtml(importanceValue)}</strong>
                </div>
            </div>
        </div>
        <div class="content-grid">
            ${section("Price Impact by Category", renderValueTable(data, key))}
            ${section("Explanation", `<p>${markdown(data.explanation)}</p>`)}
            ${section("Examples", renderExamples(data, key))}
            ${section("Business Insight", `
                <div class="insight-grid">
                    <div class="mini-card">
                        <h4>Market Insight</h4>
                        <p>${escapeHtml(data.insights?.market || "")}</p>
                    </div>
                    <div class="mini-card">
                        <h4>Buyer Insight</h4>
                        <p>${escapeHtml(data.insights?.buyer || "")}</p>
                    </div>
                    <div class="mini-card">
                        <h4>Seller Insight</h4>
                        <p>${escapeHtml(data.insights?.seller || "")}</p>
                    </div>
                </div>
            `)}
            ${section("Important Note", `<p>${markdown(data.note || "")}</p>`, "note")}
        </div>
    `;
}

function renderSelectedFeature() {
    const category = els.category.value;
    const key = els.feature.value;
    els.message.style.display = "none";
    els.card.innerHTML = category === "numerical"
        ? renderNumerical(key)
        : renderCategorical(key);
}

async function init() {
    try {
        const response = await fetch("/insights/data");
        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || "Unable to load insights.");
        }

        state.data = data;
        renderFeatureOptions();
    } catch (error) {
        els.card.innerHTML = "";
        els.message.textContent = `${error.message} Start the backend service and refresh.`;
        els.message.style.display = "block";
    }
}

els.category.addEventListener("change", renderFeatureOptions);
els.feature.addEventListener("change", renderSelectedFeature);

init();
