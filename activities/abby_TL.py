#!/usr/bin/env python3

import os
import grass.script as gs
 
 
def run_flow_analysis(scanned_elev, env, **kwargs):
    """
    Computes flow accumulation and shows how water moves across the landscape.
    """
    # --- Flow direction and accumulation ---
    gs.run_command(
        "r.watershed",
        elevation=scanned_elev,
        accumulation="flow_accum",
        drainage="flow_dir",
        flags="a",
        env=env,
    )
 
    # --- Extract streams where flow accumulation exceeds threshold ---
    gs.mapcalc(
        "streams = if(abs(flow_accum) > 50, 1, null())",
        env=env,
    )
 
    # --- Compute surface runoff using Manning's equation proxy ---
    # Uses landcover map to apply roughness coefficients
    # Landcover classes from landcover_1m:
    #   1=pond, 2=forest, 3=developed, 4=bare, 5=paved road,
    #   6=dirt road, 7=vineyard, 8=agriculture, 9=wetland,
    #   10=bare ground path, 11=grass
    gs.mapcalc(
        """
        roughness = if(landcover_1m ==  1, 0.020,
                    if(landcover_1m ==  2, 0.100,
                    if(landcover_1m ==  3, 0.015,
                    if(landcover_1m ==  4, 0.023,
                    if(landcover_1m ==  5, 0.011,
                    if(landcover_1m ==  6, 0.025,
                    if(landcover_1m ==  7, 0.060,
                    if(landcover_1m ==  8, 0.035,
                    if(landcover_1m ==  9, 0.075,
                    if(landcover_1m == 10, 0.023,
                    if(landcover_1m == 11, 0.040, 0.030)))))))))))
        """,
        env=env,
    )
 
    # --- Compute slope for runoff estimate ---
    gs.run_command(
        "r.slope.aspect",
        elevation=scanned_elev,
        slope="slope",
        env=env,
    )
 
    # --- Runoff index: lower roughness + steeper slope = faster runoff ---
    gs.mapcalc(
        "runoff_index = slope / roughness",
        env=env,
    )
 
    # --- Classify runoff risk into low/medium/high ---
    gs.mapcalc(
        """
        runoff_risk = if(runoff_index < 5,  1,
                      if(runoff_index < 15, 2, 3))
        """,
        env=env,
    )
 
    # Apply color ramp: green=low, yellow=medium, red=high
    gs.run_command(
        "r.colors",
        map="runoff_risk",
        rules="-",
        env=env,
        stdin="1 green\n2 yellow\n3 red\n",
    )
 
    # --- Flow accumulation color: blue scale ---
    gs.run_command(
        "r.colors",
        map="flow_accum",
        color="blues",
        env=env,
    )
 
    # --- Vectorize stream network for display ---
    gs.run_command(
        "r.to.vect",
        input="streams",
        output="stream_network",
        type="line",
        env=env,
    )
 
 
def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
 
    # --- Dataset setup ---
    elevation = "elev_lid792_1m"
    landcover = "landcover_1m"
    elev_resampled = "elev_resampled"
 
    # --- Set region and resample elevation for performance ---
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command(
        "r.resamp.stats",
        input=elevation,
        output=elev_resampled,
        env=env,
    )
 
    # --- Resample landcover to match region ---
    gs.run_command(
        "r.resamp.stats",
        input=landcover,
        output="landcover_resampled",
        method="mode",
        env=env,
    )
 
    # Override landcover_1m reference to use resampled version in mapcalc
    gs.run_command(
        "g.copy",
        raster="landcover_resampled,landcover_1m",
        env=env,
    )
 
    # --- Run the core flow analysis on scanned/resampled elevation ---
    run_flow_analysis(scanned_elev=elev_resampled, env=env)
 
 
if __name__ == "__main__":
    main()
