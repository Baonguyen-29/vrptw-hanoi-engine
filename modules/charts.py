"""Biểu đồ Plotly cho VRPTW"""
import pandas as pd                          
import plotly.graph_objects as go
import plotly.express as px
GREEN = "#10b981"
DARK_GREEN = "#047857"
LIGHT_GREEN = "#a7f3d0"
ORANGE = "#f59e0b"
RED = "#ef4444"
BLUE = "#3b82f6"
CFG = {"displayModeBar": False, "responsive": True}


def _w(fig, h=420):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=CFG, default_height=h)


def chart_before_after(kpi):
    b, a = kpi["before"], kpi["after"]
    m = [
        ("Quãng đường (km)", b["Tổng quãng đường (km)"], a["Tổng quãng đường (km)"]),
        ("Nhiên liệu (L)", b["Tổng nhiên liệu (L)"], a["Tổng nhiên liệu (L)"]),
        ("Chi phí (nghìn VND)", b["Chi phí nhiên liệu (VND)"] / 1000, a["Chi phí nhiên liệu (VND)"] / 1000),
        ("CO₂ (kg)", b["Phát thải CO₂ (kg)"], a["Phát thải CO₂ (kg)"]),
        ("Số xe", b["Số phương tiện sử dụng"], a["Số phương tiện sử dụng"]),
    ]
    fig = go.Figure(data=[
        go.Bar(name="Trước AI", x=[x[0] for x in m], y=[x[1] for x in m],
               marker_color=RED, text=[f"{x[1]:,.1f}" for x in m], textposition="outside"),
        go.Bar(name="Sau AI", x=[x[0] for x in m], y=[x[2] for x in m],
               marker_color=GREEN, text=[f"{x[2]:,.1f}" for x in m], textposition="outside"),
    ])
    fig.update_layout(barmode="group", title="So sánh trước & sau AI",
                      template="plotly_white", height=420,
                      legend=dict(orientation="h", y=-0.15))
    return _w(fig)


def chart_savings_pie(s):
    keys = ["Tổng quãng đường (km)", "Tổng nhiên liệu (L)",
            "Chi phí nhiên liệu (VND)", "Phát thải CO₂ (kg)"]
    fig = go.Figure(data=[go.Pie(
        labels=["Quãng đường", "Nhiên liệu", "Chi phí", "CO₂"],
        values=[s[k]["pct"] for k in keys], hole=0.55,
        marker=dict(colors=[GREEN, BLUE, ORANGE, DARK_GREEN]),
        textinfo="label+percent",
    )])
    fig.update_layout(title="Tỷ lệ giảm (%) sau tối ưu AI",
                      template="plotly_white", height=420,
                      annotations=[dict(text="AI<br>Savings", x=0.5, y=0.5,
                                        font_size=16, showarrow=False)])
    return _w(fig)


def chart_vehicle_efficiency(vs):
    df = vs[vs["used"] == "Có"].copy()
    if df.empty:
        return ""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["vehicle"], y=df["load_kg"], name="Thực tế (kg)",
                         marker_color=GREEN, text=df["load_kg"], textposition="outside"))
    fig.add_trace(go.Bar(x=df["vehicle"], y=df["capacity_kg"], name="Tối đa (kg)",
                         marker_color=LIGHT_GREEN))
    fig.update_layout(barmode="overlay", title="Hiệu suất sử dụng tải trọng",
                      template="plotly_white", height=420,
                      legend=dict(orientation="h", y=-0.2))
    return _w(fig)


def chart_area_distribution(area):
    if area.empty:
        return ""
    fig = go.Figure(data=[go.Bar(
        x=area["Area"], y=area["num_orders"], marker_color=GREEN,
        text=area["num_orders"], textposition="outside",
    )])
    fig.update_layout(title="Phân bố đơn hàng theo khu vực",
                      template="plotly_white", height=380)
    return _w(fig)


def chart_cost_co2_by_vehicle(vs):
    df = vs[vs["used"] == "Có"].copy()
    if df.empty:
        return ""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["vehicle"], y=df["cost_vnd"] / 1000,
                         name="Chi phí (nghìn VND)", marker_color=ORANGE))
    fig.add_trace(go.Scatter(x=df["vehicle"], y=df["co2_kg"], name="CO₂ (kg)",
                             mode="lines+markers",
                             marker=dict(size=10, color=DARK_GREEN), yaxis="y2"))
    fig.update_layout(title="Chi phí & CO₂ theo phương tiện",
                      template="plotly_white", height=420,
                      yaxis=dict(title="Chi phí (nghìn VND)"),
                      yaxis2=dict(title="CO₂ (kg)", overlaying="y", side="right"),
                      legend=dict(orientation="h", y=-0.2))
    return _w(fig)


def chart_route_timeline(routes, top_n=8):
    if routes.empty:
        return ""
    counts = routes.groupby("vehicle").size().sort_values(ascending=False)
    top = counts.head(top_n).index.tolist()
    df = routes[routes["vehicle"].isin(top)].copy()
    df["dt"] = pd.to_datetime(df["arrival_time"], format="%H:%M", errors="coerce")
    df = df.dropna(subset=["dt"])
    df["min"] = df["dt"].dt.hour * 60 + df["dt"].dt.minute
    fig = px.scatter(df, x="min", y="vehicle", color="vehicle",
                     hover_data=["from", "to", "distance_km", "arrival_time"],
                     title=f"Timeline tuyến đường {len(top)} xe tiêu biểu")
    fig.update_layout(template="plotly_white", height=420, showlegend=False)
    return _w(fig)


def chart_route_map(routes, orders):
    if routes.empty or orders.empty:
        return ""
    coord = orders.set_index("Order_ID")[["Latitude", "Longitude"]].to_dict("index")
    d_lat, d_lon = 21.038, 105.79
    fig = go.Figure()
    colors = px.colors.qualitative.Set2
    for i, (veh, grp) in enumerate(routes.groupby("vehicle")):
        lats, lons, texts = [d_lat], [d_lon], [f"DEPOT-{veh}"]
        for _, row in grp.iterrows():
            if row["to"] in coord:
                lats.append(coord[row["to"]]["Latitude"])
                lons.append(coord[row["to"]]["Longitude"])
                texts.append(f"{row['to']}<br>{row['arrival_time']}<br>{row['distance_km']} km")
        lats.append(d_lat)
        lons.append(d_lon)
        texts.append(f"DEPOT-{veh}")
        fig.add_trace(go.Scattermapbox(
            lat=lats, lon=lons, mode="lines+markers",
            marker=dict(size=7, color=colors[i % len(colors)]),
            line=dict(width=1.5, color=colors[i % len(colors)]),
            text=texts, hoverinfo="text", name=veh,
        ))
    fig.update_layout(
        mapbox=dict(style="open-street-map", zoom=11,
                    center=dict(lat=d_lat, lon=d_lon)),
        title="Bản đồ tuyến giao hàng tối ưu",
        height=550, margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(orientation="h", y=-0.05),
    )
    return _w(fig, 550)


def chart_cost_breakdown_pie(bd):
    if not bd:
        return ""
    fig = go.Figure(data=[go.Pie(
        labels=["Xe máy", "Xe tải"],
        values=[bd["fuel_moto"], bd["fuel_truck"]], hole=0.5,
        marker=dict(colors=[GREEN, ORANGE]),
        textinfo="label+percent+value",
    )])
    fig.update_layout(title="Cơ cấu chi phí nhiên liệu",
                      template="plotly_white", height=380)
    return _w(fig)


def chart_co2_by_type(bd):
    if not bd:
        return ""
    fig = go.Figure(data=[go.Bar(
        x=["Xe máy", "Xe tải nhỏ"],
        y=[bd["co2_moto"], bd["co2_truck"]],
        marker_color=[GREEN, ORANGE],
        text=[f"{bd['co2_moto']:.2f} kg", f"{bd['co2_truck']:.2f} kg"],
        textposition="outside",
    )])
    fig.update_layout(title="Phát thải CO₂ theo loại phương tiện",
                      yaxis_title="kg CO₂",
                      template="plotly_white", height=380)
    return _w(fig)


def chart_npv_sensitivity(npv):
    rates = list(npv.keys())
    values = [v / 1_000_000 for v in npv.values()]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[f"{r}%" for r in rates], y=values,
        mode="lines+markers+text",
        marker=dict(size=14, color=GREEN),
        line=dict(width=3, color=DARK_GREEN),
        text=[f"{v:.0f} tr" for v in values], textposition="top center",
    ))
    fig.update_layout(title="NPV theo tỷ lệ chiết khấu (triệu VND)",
                      xaxis_title="Tỷ lệ chiết khấu", yaxis_title="NPV (triệu VND)",
                      template="plotly_white", height=380)
    return _w(fig)
