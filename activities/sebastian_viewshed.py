#!/usr/bin/env python3

import os
import grass.script as gs


def run_points(scanned_elev, env, **kwargs):

    points = "points"
    import analyses

    analyses.change_detection(
        "scan_saved",
        scanned_elev,
        points,
        height_threshold=[10, 100],
        cells_threshold=[5, 50],
        add=True,
        max_detected=5,
        debug=True,
        env=env,
    )

    data = (
        gs.read_command(
            "v.out.ascii",
            input=points,
            type="point",
            format="point",
            separator="comma",
            env=env,
        )
        .strip()
        .splitlines()
    )

    if data:
        x, y = [float(p) for p in data[0].split(",")[:2]]
        return x, y


def run_viewshed(scanned_elev, x, y, env, **kwargs):
    gs.run_command(
        "r.viewshed",
        input=scanned_elev,
        output="viewshed",
        coordinates=f"{x},{y}",
        env=env,
    )


def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)

    coords = run_points(scanned_elev=elev_resampled, env=env)
    if coords is not None:
        x, y = coords
        run_viewshed(scanned_elev=elev_resampled, x=x, y=y, env=env)


if __name__ == "__main__":
    main()
