import os
import numpy as np
import pandas as pd
import rasterio
from utils.log_module import setup_logger

logger = setup_logger(__name__)

def compute_stats(
        city_name: str,
        output_dir: str,
        clipped_image=None,
        clipped_meta=None, 
        return_df: bool = False
    ):
    """
    Perform statistics on clipped population raster.

    Parameters
    ----------
    city_name : str
        City name used for locating the clipped raster file.
    output_dir : str
        Base output directory.
    clipped_image : np.ndarray, optional
        In-memory clipped raster array from datacollection().
    clipped_meta : dict, optional
        Raster metadata from datacollection().
    return_df : bool
        If True, return dataframe, default is False.

    Returns
    -------
    stats_df : pandas.DataFrame
        DataFrame containing min, p25, median, mean, p75, max, sum.
    """

    logger.info("Starting solar raster analysis…")

    # -----------------------------------------------------
    # 1. Load raster from disk if not provided
    # -----------------------------------------------------
    if clipped_image is None or clipped_meta is None:
        raster_path = os.path.join(output_dir, "spatial", f"{city_name}_solar.tif")

        if not os.path.exists(raster_path):
            logger.error(f"Clipped raster not found at: {raster_path}")
            return None

        logger.info(f"Loading clipped raster from disk: {raster_path}")

        try:
            with rasterio.open(raster_path) as src:
                clipped_image = src.read()
                clipped_meta = src.meta
        except Exception as e:
            logger.error(f"Failed to load raster: {e}")
            return None
    else:
        logger.info("Using in-memory raster from datacollection().")

    # -----------------------------------------------------
    # 2. Prepare raster data for statistics
    # -----------------------------------------------------
    # Convert to 1D and remove zeros/nodata
    arr = clipped_image.squeeze().astype(float)
    valid = arr[arr > 0]   # assume nodata = 0

    if valid.size == 0:
        logger.error("Raster contains no valid values. Cannot compute statistics.")
        return None

    # -----------------------------------------------------
    # 3. Compute statistics
    # -----------------------------------------------------
    stats = {
        "min": float(np.min(arr)),
        "p5": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "mean": float(np.mean(arr)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(np.max(arr)),
        "sum": float(np.sum(arr)), 
        "stdev": float(np.std(arr, ddof=0)), # population std dev
        "count": int(arr.size)
    }

    stats_df = pd.DataFrame([stats])
    logger.info("Raster statistics calculated successfully.")

    # -----------------------------------------------------
    # 4. Save output CSV
    # -----------------------------------------------------
    tabular_dir = os.path.join(output_dir, "tabular")
    os.makedirs(tabular_dir, exist_ok=True)

    output_path = os.path.join(tabular_dir, f"{city_name}_solar_stats.csv")

    try:
        stats_df.to_csv(output_path, index=False)
        logger.info(f"solar statistics saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving statistics CSV: {e}")

    if return_df:
        return stats_df

    return None




import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import rasterio
import yaml

from typing import Optional, Dict, Any
from utils.log_module import setup_logger

logger = setup_logger(__name__)


def plot_solar_seasonality(
    city_name: str,
    output_dir: str,
    render_dir: str, 
    font_dict: Dict[str, Any],
    clipped_image: Optional[np.ndarray] = None,
    clipped_meta: Optional[Dict[str, Any]] = None,
    favorable_threshold: float = 3.5,
    excellent_threshold: float = 4.5,
    return_df: bool = False
) -> Optional[pd.DataFrame]:
    """
    Plot seasonal availability of solar PV potential from a pre-clipped raster.

    The raster is assumed to:
    - Be spatially clipped upstream (no masking needed here)
    - Have 12 bands representing monthly PV yield (Jan–Dec)
    - Store values as daily PV energy yield (kWh/kWp)

    The function prioritizes in-memory inputs (from datacollection),
    and falls back to loading from disk if not provided.

    Outputs:
    - Static PNG plot
    - Interactive Plotly HTML plot
    - YAML file containing a short seasonality interpretation

    Parameters
    ----------
    city_name : str
        City name used for file naming.
    output_dir : str
        Base output directory where clipped raster is stored.
    render_dir : str
        Directory where resulting plots will be stored.
    font_dict : dict
        Plotly font configuration dictionary.
    clipped_image : np.ndarray, optional
        In-memory raster array of shape (bands, height, width).
    clipped_meta : dict, optional
        Raster metadata dictionary.
    favorable_threshold : float, optional
        Threshold for “Favorable Conditions” (default = 3.5 kWh/kWp).
    excellent_threshold : float, optional
        Threshold for “Excellent Conditions” (default = 4.5 kWh/kWp).
    return_df : bool
        If True, return dataframe, default is False.

    Returns
    -------
    pd.DataFrame or None
        DataFrame with monthly maximum PV values, or None if loading fails.
    """

    # -----------------------------------------------------
    # 1. Load raster from disk if not provided
    # -----------------------------------------------------
    if clipped_image is None or clipped_meta is None:
        raster_path = os.path.join(
            output_dir, "spatial", f"{city_name}_solar_monthly.tif"
        )

        if not os.path.exists(raster_path):
            logger.error(f"Clipped raster not found at: {raster_path}")
            return None

        logger.info(f"Loading clipped raster from disk: {raster_path}")

        try:
            with rasterio.open(raster_path) as src:
                clipped_image = src.read()
                clipped_meta = src.meta
        except Exception as e:
            logger.error(f"Failed to load raster: {e}")
            return None
    else:
        logger.info("Using in-memory raster from datacollection().")

    # -----------------------------------------------------
    # 2. Extract monthly maximum PV values
    # -----------------------------------------------------
    monthly_pv = {}
    nodata = clipped_meta.get("nodata")

    for band_idx in range(clipped_image.shape[0]):
        band_data = clipped_image[band_idx].astype("float32")

        if nodata is not None:
            band_data[band_data == nodata] = np.nan

        valid_data = band_data[~np.isnan(band_data)]

        monthly_pv[band_idx + 1] = (
            float(valid_data.max()) if valid_data.size > 0 else np.nan
        )

    df = (
        pd.DataFrame(list(monthly_pv.items()), columns=["month", "max"])
        .sort_values("month")
        .reset_index(drop=True)
    )


    # -----------------------------------------------------
    # 3. Seasonality interpretation
    # -----------------------------------------------------
    highest = df["max"].max()
    lowest = df["max"].min()

    ratio = highest / lowest if lowest and lowest > 0 else np.inf

    if ratio > 2.5:
        solar_text = (
            "Solar seasonality is high, but solar energy remains available "
            "throughout the year."
        )
    else:
        solar_text = (
            "Solar seasonality is low to moderate, with relatively consistent "
            "solar availability across months."
        )

    yaml_path = os.path.join(output_dir, "tabular", f"{city_name}_solar.yml")
    with open(yaml_path, "w") as f:
        yaml.dump({"solar_text": solar_text}, f)

    # -----------------------------------------------------
    # 4. Static Matplotlib plot (PNG)
    # -----------------------------------------------------
    plt.figure(figsize=(8, 8))
    plt.plot(df["month"], df["max"], marker="o")

    plt.axhline(favorable_threshold, linestyle="--", color="black")
    plt.text(1, favorable_threshold + 0.02, "Favorable Conditions", color="darkgrey")

    plt.axhline(excellent_threshold, linestyle="--", color="black")
    plt.text(1, excellent_threshold + 0.02, "Excellent Conditions", color="darkgrey")

    plt.xlabel("Month")
    plt.ylabel("Daily PV energy yield (kWh/kWp)")
    plt.title("Seasonal availability of solar energy")
    plt.xticks(
        np.arange(1, 13),
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    )
    plt.grid(True)
    plt.tight_layout()

    png_path = os.path.join(render_dir, "plots", "png", f"{city_name}_PV_graph.png")
    plt.savefig(png_path, bbox_inches="tight")
    plt.close()

    # -----------------------------------------------------
    # 5. Interactive Plotly plot (HTML)
    # -----------------------------------------------------
    fig = px.line(df, x="month", y="max", markers=True)

    fig.add_shape(
        type="line",
        x0=1, y0=favorable_threshold,
        x1=12, y1=favorable_threshold,
        line=dict(color="black", dash="dash"),
    )

    fig.add_shape(
        type="line",
        x0=1, y0=excellent_threshold,
        x1=12, y1=excellent_threshold,
        line=dict(color="black", dash="dash"),
    )

    fig.add_annotation(
        x=6.5, y=excellent_threshold + 0.1,
        text="Excellent Conditions",
        showarrow=False,
        font=dict(color="darkgrey"),
    )

    fig.add_annotation(
        x=6.5, y=favorable_threshold + 0.1,
        text="Favorable Conditions",
        showarrow=False,
        font=dict(color="darkgrey"),
    )

    fig.update_xaxes(
        tickvals=list(range(1, 13)),
        ticktext=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        title="",
    )

    fig.update_yaxes(
        title="Daily PV energy yield (kWh/kWp)",
        range=[0, None],
    )

    fig.update_layout(
        template="plotly_white",
        font=font_dict,
        plot_bgcolor="white",
        autosize=True,
    )

    html_path = os.path.join(render_dir, "plots", "html", f"{city_name}_PV_graph.html")
    fig.write_html(html_path, full_html=False, include_plotlyjs="cdn")

    # -----------------------------------------------------
    # 4. Save output CSV
    # -----------------------------------------------------
    tabular_dir = os.path.join(output_dir, "tabular")
    os.makedirs(tabular_dir, exist_ok=True)

    output_path = os.path.join(tabular_dir, f"{city_name}_solar_monthly_stats.csv")

    try:
        df.to_csv(output_path, index=False)
        logger.info(f"solar statistics saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving statistics CSV: {e}")

    if return_df:
        return df

    return None



if __name__ == "__main__":
    # Example standalone test
    compute_stats(city_name="testcity", output_dir="./outputs")
