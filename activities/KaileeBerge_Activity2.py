import json
import os

import grass.script as gs


def run_function_with_points(
    scanned_elev, eventHandler=None, env=None, points=None, **kwargs
):
    """Doesn't do anything, except loading points from a vector map to Python

    If *points* is provided, the function assumes it is name of an existing vector map.
    This is used during testing.
    If *points* is not provided, the function assumes it runs in Tangible Landscape.
    """
    if not points:
        # If there are no points, ask Tangible Landscape to generate points from
        # a change in the surface.
        points = "points"
        import analyses
        from activities import updateDisplay

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

    point_prob = gs.read_command(
        "r.what",
        map="probabilitySurface",
        points=points,
        format="json",
        env=env,
    )
    point_prob = json.loads(point_prob)
    if point_prob:
        p = point_prob[0]["probabilitySurface"]["value"] * 100

        # update dashboard
        event = updateDisplay(
            value=[point_prob[0]["easting"], point_prob[0]["northing"], p]
        )
        eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)


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

    run_function_with_points(scanned_elev=elev_resampled, env=env, points=points)


if __name__ == "__main__":
    main()
