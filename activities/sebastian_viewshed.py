#!/usr/bin/env python3

import os

import grass.script as gs


def calib_contours(scanned_elev, env, **kwargs):
    interval = 2
    gs.run_command(
        "r.contour",
        input=scanned_elev,
        output="contours",
        step=interval,
        flags="t",
        env=env,
    )


def run_viewshed(scanned_elev, env, points=None, **kwargs):
    viewshed_surface = scanned_elev
    if not points:
        points = "points"
        import analyses

        analyses.change_detection(
            kwargs["scanned_calib_elev"],
            scanned_elev,
            points,
            height_threshold=[10, 100],
            cells_threshold=[5, 50],
            add=True,
            max_detected=1,
            debug=True,
            env=env,
        )
        viewshed_surface = kwargs["scanned_calib_elev"]

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

    if len(data) < 1:
        # For the cases when the analysis expects at least 2 points, we check the
        # number of points and return from the function if there is less than 2
        # points. (No points is a perfectly valid state in Tangible Landscape,
        # so we need to deal with it here.)
        return

    point = data[0]
    x, y = [float(p) for p in point.split(",")][:2]

    gs.run_command(
        "r.viewshed",
        input=viewshed_surface,
        output="viewshed",
        coordinates=f"{x},{y}",
        flags="e",
        env=env,
    )


def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)

    points = "points"
    gs.write_command(
        "v.in.ascii",
        flags="t",
        input="-",
        output=points,
        separator="comma",
        stdin="638432,220382\n638621,220607",
        env=env,
    )

    # Call the analysis.
    run_viewshed(scanned_elev=elev_resampled, env=env, points=points)


if __name__ == "__main__":
    main()
