#!/usr/bin/env python3

import os

import grass.script as gs


def run_sun(scanned_elev, day_of_year, time, env, **kwargs):
    gs.run_command(
        "r.sun",
        elevation=scanned_elev,
        day=day_of_year,
        time=time,
        glob_rad="global_irradiation",
        env=env,
    )


def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)

    run_sun(
        scanned_elev=elev_resampled, day_of_year=261, time=12, env=env
    )  # testing with my birthday!


if __name__ == "__main__":
    main()
