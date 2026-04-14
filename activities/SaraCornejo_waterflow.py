#!/usr/bin/env python3


import os
import sys
import grass.script as gs


def run_waterflow(scanned_elev, env, **kwargs):
    # first we need to compute x- and y-derivatives
    gs.run_command('r.slope.aspect', elevation=scanned_elev, dx='scan_dx', dy='scan_dy', env=env)
    gs.run_command('r.sim.water', elevation=scanned_elev, dx='scan_dx', dy='scan_dy',
                   rain_value=150, depth='flow', env=env)
    
def run_wateraccum(scanned_elev, env, **kwargs):
    repeat = 2
    input_dem = scanned_elev
    output = "tmp_filldir"
    for i in range(repeat):
        gs.run_command('r.fill.dir', input=input_dem, output=output, direction="tmp_dir", env=env)
        input_dem = output
    # filter depressions deeper than 0.1 m
    gs.mapcalc('{new} = if({out} - {scan} > 0.1, {out} - {scan}, null())'.format(new='ponds', out=output,
                                                                                  scan=scanned_elev), env=env)
    gs.write_command('r.colors', map='ponds', rules='-', stdin='0% aqua\n100% blue', env=env)


def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)
    run_waterflow(scanned_elev=elev_resampled, env=env)
    run_wateraccum(scanned_elev=elev_resampled, env=env)

if __name__ == "__main__":
    main()
