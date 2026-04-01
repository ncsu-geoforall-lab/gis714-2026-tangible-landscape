#!/usr/bin/env python3

import os

import grass.script as gs

def run_waterflow(scanned_elev, env, **kwargs):
    # first we need to compute x- and y-derivatives
    gs.run_command('r.slope.aspect', elevation=scanned_elev, dx='scan_dx', dy='scan_dy', env=env)
    gs.run_command('r.sim.water', elevation=scanned_elev, dx='scan_dx', dy='scan_dy',
                   rain_value=150, depth='flow', env=env)

def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)

    run_waterflow(scanned_elev=elev_resampled, env=env)


if __name__ == "__main__":
    main()
