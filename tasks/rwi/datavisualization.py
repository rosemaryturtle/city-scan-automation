import os
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import pandas as pd

from utils.log_module import setup_logger
logger = setup_logger(__name__)

# ----------------------------------------------------------
# 1. CHOROPLETH MAP 
# ----------------------------------------------------------
def plot_choropleth_gdf(
    city_name: str,
    output_dir: str,
    gdf: gpd.GeoDataFrame,
    value_col: str,
    figsize=(16, 16),
    cmap="RdYlGn",
    drop_zeros=True,
):
    """
    Plot choropleth map from GeoDataFrame.
    """

    logger.info("Generating GeoDataFrame choropleth map…")

    if gdf is None or gdf.empty:
        logger.error("GeoDataFrame is empty or None.")
        return

    if value_col not in gdf.columns:
        logger.error(f"Column '{value_col}' not found in GeoDataFrame.")
        return

    plot_gdf = gdf.copy()

    # Clean values
    plot_gdf[value_col] = pd.to_numeric(plot_gdf[value_col], errors="coerce")
    plot_gdf = plot_gdf.dropna(subset=[value_col])

    if drop_zeros:
        plot_gdf = plot_gdf[plot_gdf[value_col] > 0]

    if plot_gdf.empty:
        logger.error("No valid values to plot.")
        return

    fig, ax = plt.subplots(figsize=figsize)

    plot_gdf.plot(
        column=value_col,
        cmap=cmap,
        linewidth=0,
        ax=ax,
        legend=True,
        legend_kwds={
            "label": value_col,
            "shrink": 0.6
        },
        zorder=10
    )

    # Basemap
    try:
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.PositronNoLabels,
            crs=plot_gdf.crs,
            zorder=1
        )
    except Exception:
        logger.warning("Basemap failed to load; continuing without background.")

    ax.set_title(f"{city_name} – {value_col}")
    ax.axis("off")

    # Save
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    out_path = os.path.join(
        img_dir,
        f"{city_name}_{value_col}_choropleth_map.png"
    )

    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Choropleth saved to: {out_path}")

# ----------------------------------------------------------
# 2. HISTOGRAM
# ----------------------------------------------------------

def plot_histogram_gdf(
    city_name: str,
    output_dir: str,
    gdf: gpd.GeoDataFrame,
    value_col: str,
    figsize=(16, 8),
    bins=50,
    color="tab:red",
    drop_zeros=True
):
    """
    Plot histogram of GeoDataFrame column values.
    """

    logger.info("Generating GeoDataFrame histogram…")

    if gdf is None or gdf.empty:
        logger.error("GeoDataFrame is empty or None.")
        return

    if value_col not in gdf.columns:
        logger.error(f"Column '{value_col}' not found.")
        return

    values = pd.to_numeric(gdf[value_col], errors="coerce")
    values = values.dropna()

    if drop_zeros:
        values = values[values > 0]

    if values.empty:
        logger.error("No valid values for histogram.")
        return

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(values, bins=bins, color=color, alpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.5)

    ax.set_title(f"{city_name} – {value_col} Distribution")
    ax.set_xlabel("")
    ax.set_ylabel("")

    # Save
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    out_path = os.path.join(
        img_dir,
        f"{city_name}_{value_col}_histogram.png"
    )

    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Histogram saved to: {out_path}")

# ----------------------------------------------------------
# 3. RUN ALL VISUALIZATIONS
# ----------------------------------------------------------

def run_viz_gdf(
    city_name: str,
    output_dir: str,
    gdf: gpd.GeoDataFrame,
    value_col: str,
    choropleth_kwargs=None,
    histogram_kwargs=None
):
    """
    Run all GeoDataFrame visualizations for a given city.
    """

    logger.info("Running GeoDataFrame visualization suite…")

    choropleth_kwargs = choropleth_kwargs or {}
    histogram_kwargs = histogram_kwargs or {}

    plot_choropleth_gdf(
        city_name=city_name,
        output_dir=output_dir,
        gdf=gdf,
        value_col=value_col,
        **choropleth_kwargs
    )

    plot_histogram_gdf(
        city_name=city_name,
        output_dir=output_dir,
        gdf=gdf,
        value_col=value_col,
        **histogram_kwargs
    )

    logger.info("All GeoDataFrame visualizations completed.")
