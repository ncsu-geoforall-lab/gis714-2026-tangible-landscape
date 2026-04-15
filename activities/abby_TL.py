#!/usr/bin/env python3

"""
How does landcover influence runoff?
"""

import os

import grass.script as gs


def run_flow_analysis(scanned_elev, landcover, env, **kwargs):
    """
    Computes flow accumulation and a Manning's n-weighted runoff map.
    Lower roughness i.e. impervious surfaces (roads, developed) = faster runoff.
    Higher roughness (forest, wetland) = slower, reduced runoff.
    """

    # Flow accumulation
    gs.run_command(
        "r.watershed",
        elevation=scanned_elev,
        accumulation="flow_accum",
        flags="a",
        env=env,
    )

    # Assign Manning's n roughness coefficient to each landcover class
    #   1=pond          -> Open Water                      (0.001)
    #   2=forest        -> Mixed Forest                    (0.400)
    #   3=developed     -> Developed, Medium Intensity     (0.0678)
    #   4=bare          -> Barren Land                     (0.0113)
    #   5=paved road    -> Developed, High Intensity       (0.0404)
    #   6=dirt road     -> Developed, Open Space           (0.0404)
    #   7=vineyard      -> Shrub/Scrub                     (0.400)
    #   8=agriculture   -> Cultivated Crops                (0.325)
    #   9=wetland       -> Emergent Herbaceous Wetlands    (0.1825)
    #  10=bare gnd path -> Barren Land                     (0.0113)
    #  11=grass         -> Grassland/Herbaceous            (0.368)
    roughness_expr = (
        f"roughness = if({landcover}==1,0.001,"
        f"if({landcover}==2,0.400,"
        f"if({landcover}==3,0.0678,"
        f"if({landcover}==4,0.0113,"
        f"if({landcover}==5,0.0404,"
        f"if({landcover}==6,0.0404,"
        f"if({landcover}==7,0.400,"
        f"if({landcover}==8,0.325,"
        f"if({landcover}==9,0.1825,"
        f"if({landcover}==10,0.0113,"
        f"if({landcover}==11,0.368,0.0404)))))))))))"
    )
    gs.mapcalc(roughness_expr, env=env)

    # Divide by roughness: smoother surfaces produce more runoff
    # Pond roughness values are extremely small, exclude from the output
    gs.mapcalc(
        "runoff = if(landcover_int == 1, null(), abs(flow_accum) / roughness)", env=env
    )

    # Color: low runoff = blue, high runoff = red
    gs.run_command("r.colors", map="runoff", color="bgyr", env=env)


def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"

    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    landcover_resampled = "landcover_resampled"

    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)
    gs.run_command(
        "r.resamp.stats",
        input="landcover_1m",
        output=landcover_resampled,
        method="mode",
        env=env,
    )
    gs.run_command("g.region", raster=elev_resampled, env=env)

    # Convert to integer for mapcalc
    gs.mapcalc("landcover_int = int(landcover_resampled)", env=env)

    run_flow_analysis(
        scanned_elev=elev_resampled,
        landcover="landcover_int",
        env=env,
    )


if __name__ == "__main__":
    main()
