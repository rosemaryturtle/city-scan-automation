import os
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
import contextily as ctx
from matplotlib.colors import ListedColormap, BoundaryNorm

from utils.log_module import setup_logger
logger = setup_logger(__name__)

# ----------------------------------------------------------
# HELPER: load clipped raster from output_dir if needed
# ----------------------------------------------------------
def _load_clipped_raster(city_name, output_dir):
    raster_path = os.path.join(output_dir, "spatial", f"{city_name}_landslide.tif")

    if not os.path.exists(raster_path):
        logger.error(f"Raster not found for visualization: {raster_path}")
        return None, None

    with rasterio.open(raster_path) as src:
        arr = src.read()          # read ALL bands -> could return shape (1, H, W)
        meta = src.meta
    
    return arr, meta


# ----------------------------------------------------------
# 1. RASTER MAP (FIXED VERSION)
# ----------------------------------------------------------
def plot_rastermap(
    city_name: str,
    output_dir: str,
    clipped_image=None,
    clipped_meta=None,
    figsize=(16, 16),
    cmap="magma",
):
    """
    Plot landslide susceptability map using raster clipped to the AOI.
    Includes basemap (CartoDB Positron No Labels).
    """

    logger.info("Generating map…")

    # ----------------------------------
    # Load raster if not provided
    # ----------------------------------
    if clipped_image is None or clipped_meta is None:
        clipped_image, clipped_meta = _load_clipped_raster(city_name, output_dir)
        if clipped_image is None:
            return

    # ----------------------------------
    # FIX: Squeeze raster → always 2D
    # ----------------------------------
    data = clipped_image.squeeze().astype(float)

    # Clean nodata
    data[data <= 0] = np.nan

    # ----------------------------------
    # FIX: Compute raster bounds for correct placement on basemap
    # ----------------------------------
    transform = clipped_meta["transform"]
    height, width = data.shape

    x_min = transform[2]
    x_max = x_min + transform[0] * width
    y_max = transform[5]
    y_min = y_max + transform[4] * height  # Note: transform[4] is usually negative

    extent = [x_min, x_max, y_min, y_max]

    # ----------------------------------
    # Categorical settings
    # ----------------------------------
    categories = [1, 2, 3, 4, 5]
    labels = ["Very low", "Low", "Medium", "High", "Very high"]
    palette = ['#FCEFE2', '#F2C08C', '#E89251', '#D66136', '#993F2B']

    cmap = ListedColormap(palette)
    bounds = np.arange(0.5, 6.5, 1)  # boundaries for 1–5
    norm = BoundaryNorm(bounds, cmap.N)


    # ----------------------------------
    # Plot
    # ----------------------------------
    fig, ax = plt.subplots(figsize=figsize)

    raster_show = ax.imshow(
        data,
        cmap=cmap,
        norm=norm,
        extent=extent,
        origin="upper",
        interpolation="nearest",
        zorder=10
    )

    # Add basemap if possible
    try:
        ctx.add_basemap(
            ax,
            crs=clipped_meta["crs"],
            source=ctx.providers.CartoDB.PositronNoLabels, 
            zorder=1
        )
    except Exception:
        logger.warning("Basemap failed to load; continuing without background.")

    # Colorbar
    cbar = fig.colorbar(
        raster_show,
        ax=ax,
        fraction=0.036,
        pad=0.04,
        ticks=categories
    )

    cbar.ax.set_yticklabels(labels)
    cbar.set_label("landslide Susceptibility", rotation=90)


    ax.set_title(f"{city_name} – Landslide Susceptibility")
    ax.axis("off")

    # Save
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    out_path = os.path.join(img_dir, f"{city_name}_landslide_map.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Raster Plot saved to: {out_path}")

# ----------------------------------------------------------
# 2. HISTOGRAM
# ----------------------------------------------------------
def plot_histogram(
    city_name: str,
    output_dir: str,
    clipped_image=None,
    clipped_meta=None,
    figsize=(16, 8),
    color="tab:red"
):
    """
    Plot histogram of raster values.
    """

    logger.info("Generating histogram…")

    # Load raster if not provided
    if clipped_image is None:
        clipped_image, clipped_meta = _load_clipped_raster(city_name, output_dir)
        if clipped_image is None:
            return

    # Flatten raster values
    arr = clipped_image.astype(float).flatten()
    valid = arr[arr > 0]  # remove nodata

    if len(valid) == 0:
        logger.error("No valid raster values for histogram.")
        return

    # Plot
    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(valid, bins=50, color=color, alpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.5)

    # Clean labels
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(f"{city_name} – Landslide Susceptibility Distribution Histogram")

    # Save
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    out_path = os.path.join(img_dir, f"{city_name}_landslide_histogram.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Histogram saved to: {out_path}")


# ----------------------------------------------------------
# 3. RUN ALL VISUALIZATIONS
# ----------------------------------------------------------
def run_viz(
    city_name: str,
    output_dir: str,
    clipped_image=None,
    clipped_meta=None,
    choropleth_kwargs=None,
    histogram_kwargs=None
):
    """
    Run all visualization functions for a given city.
    """

    logger.info("Running visualization suite…")

    choropleth_kwargs = choropleth_kwargs or {}
    histogram_kwargs = histogram_kwargs or {}

    plot_rastermap(
        city_name=city_name,
        output_dir=output_dir,
        clipped_image=clipped_image,
        clipped_meta=clipped_meta,
        **choropleth_kwargs
    )

    plot_histogram(
        city_name=city_name,
        output_dir=output_dir,
        clipped_image=clipped_image,
        clipped_meta=clipped_meta,
        **histogram_kwargs
    )

    logger.info("All visualizations completed.")


if __name__ == "__main__":
    print("Run using run_viz() for a project workflow.")
