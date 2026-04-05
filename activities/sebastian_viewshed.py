#!/usr/bin/env python3

import os
import grass.script as gs

def run_marker(scanned_elev, elevation, env, **kwargs):
    gs.mapcalc("difference = $scanned_elev - $elevation", scanned_elev=scanned_elev, elevation=elevation)
    gs.mapcalc("difference = if(difference == 1, 1, null())")

def run_viewshed(elevation, difference, env, **kwargs):
    gs.run_command("g.region", raster=difference, zoom=difference)
    region = gs.parse_command("g.region", flags="g")
    x_centre = (float(region["e"]) + float(region["w"])) / 2
    y_centre = (float(region["n"]) + float(region["s"])) / 2
    gs.run_command("g.region", raster="ortho_2001_t792_1m@PERMANENT")
    gs.run_command("r.viewshed", input=elevation, output="viewshed", coordinates=f"{x_centre},{y_centre}", env=env)

def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elevation"
    region = "ortho_2001_t792_1m"
    elev_resampled = "elev_resampled"
    difference = "difference"
    gs.run_command("g.region", raster=region, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)

    run_marker(scanned_elev=elev_resampled, elevation=elevation, env=env)
    run_viewshed(elevation=elevation, difference=difference, env=env)

if __name__ == "__main__":
    main()
