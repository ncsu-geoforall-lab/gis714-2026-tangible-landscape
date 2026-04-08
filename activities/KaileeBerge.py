#!/usr/bin/env python3

import os

import grass.script as gs


def run_waterflow(scanned_elev, env, **kwargs):
    # first we need to compute x- and y-derivatives
    gs.run_command(
        "r.slope.aspect", elevation=scanned_elev, 
        dx="scan_dx", dy="scan_dy", env=env
    )
    gs.run_command(
        "r.sim.water",
        elevation=scanned_elev,
        dx="scan_dx",
        dy="scan_dy",
        rain_value=150,
        depth="flow",
        env=env,
    )

    # erosion modeling
    # Note: first install addon r.divergence using g.extension


def run_usped(scanned_elev, env, **kwargs):
    gs.run_command(
        "r.slope.aspect",
        elevation=scanned_elev,
        slope="slope",
        aspect="aspect",
        env=env,
    )
    gs.run_command(
        "r.watershed",
        elevation=scanned_elev,
        accumulation="flow_accum",
        threshold=1000,
        flags="a",
        env=env,
    )
    # topographic sediment transport factor
    resolution = gs.region()["nsres"]
    gs.mapcalc(
        "sflowtopo = pow(flow_accum * {res},1.3) * pow(sin(slope),1.2)".format(
            res=resolution
        ),
        env=env,
    )
    # compute sediment flow by combining the rainfall, soil and land cover
    # factors with the topographic sediment transport factor. We use a constant
    # value of 270 for rainfall intensity factor
    gs.mapcalc(
        "sedflow = 270. * {k_factor} * {c_factor} * sflowtopo".format(
            c_factor=0.05, k_factor=0.1
        ),
        env=env,
    )
    # compute divergence of sediment flow
    gs.run_command(
        "r.divergence",
        magnitude="sedflow",
        direction="aspect",
        output="erosion_deposition",
        env=env,
    )
    colors = [
        "0% 100:0:100",
        "-100 magenta",
        "-10 red",
        "-1 orange",
        "-0.1 yellow",
        "0 200:255:200",
        "0.1 cyan",
        "1 aqua",
        "10 blue",
        "100 0:0:100",
        "100% black",
    ]
    gs.write_command(
        "r.colors",
        map="erosion_deposition",
        rules="-",
        stdin="\n".join(colors),
        env=env,
    )


def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, 
                   output=elev_resampled, env=env)

    run_waterflow(scanned_elev=elev_resampled, env=env)
    run_usped(scanned_elev=elev_resampled, env=env)


if __name__ == "__main__":
    main()
