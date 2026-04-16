import os

import grass.script as gs


def run_waterflow(scanned_elev, env, **kwargs):
    # first compute x- and y-derivatives
    gs.run_command(
        "r.slope.aspect", elevation=scanned_elev, dx="scan_dx", dy="scan_dy", env=env
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
    # Note: first install addon r.divergence


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


def run_probability(
    env, erosion_deposition="erosion_deposition", flow="flow", **kwargs
):
    # coefficients I would obtain from CH1
    b0 = -2.0  # intercept
    b1 = -0.5  # erosion/deposition
    b2 = 0.8  # flow

    # logistic transformation
    gs.mapcalc(
        f"""probabilitySurface = 1 / (1 + exp(-({b0} + {b1} * {erosion_deposition}+ {b2} * {flow})))""",
        env=env,
    )
    colors = ["0 white", "0.25 blue", "0.5 yellow", "0.75 orange", "1 red"]
    gs.write_command(
        "r.colors",
        map="probabilitySurface",
        rules="-",
        stdin="\n".join(colors),
        env=env,
    )


# someone places a pin to make a guess
# return the probabilty of a species at pin


def run_function_with_points(scanned_elev, eventHandler, env, points=None, **kwargs):
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
    # Output point coordinates from GRASS GIS and read coordinates into a Python list.
    # point_list = []
    # data = (
    #     gs.read_command(
    #         "v.out.ascii",
    #         input=points,
    #         type="point",
    #         format="point",
    #         separator="comma",
    #         env=env,
    #     )
    #     .strip()
    #     .splitlines()
    # )
    # if len(data) < 1:
    #     # For the cases when the analysis expects at least 2 points, we check the
    #     # number of points and return from the function if there is less than 2
    #     # points. (No points is a perfectly valid state in Tangible Landscape,
    #     # so we need to deal with it here.)
    #     return
    # for point in data:
    #     point_list.append([float(p) for p in point.split(",")][:2])

    point_prob = gs.read_command(
        "r.what",
        map="probabilitySurface",
        points=points,
        env=env,
    )
    print(point_prob.split("|")[-1])
    # percentage = float(point_prob.split("|")[-1]) * 100

    # the output seems to be three columns separated by |
    # coordinates and the probability
    # 2890|28689|0.15

    # label = gs.read_command(
    #    "v.what.rast.label",
    #    vector=points,
    #    raster="probabilitySurface",
    #    #output=label,
    #    env=env,
    # )
    # print(label)

    # update dashboard
    event = updateDisplay(value=point_prob)
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
    # throw eventHandler into defining function
    # activities_panel


def main():
    env = os.environ.copy()
    env["GRASS_OVERWRITE"] = "1"
    elevation = "elev_lid792_1m"
    elev_resampled = "elev_resampled"
    gs.run_command("g.region", raster=elevation, res=4, flags="a", env=env)
    gs.run_command("r.resamp.stats", input=elevation, output=elev_resampled, env=env)

    run_waterflow(scanned_elev=elev_resampled, env=env)
    run_usped(scanned_elev=elev_resampled, env=env)
    run_probability(erosion_deposition="erosion_deposition", flow="flow", env=env)

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
