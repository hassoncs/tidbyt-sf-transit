load("render.star", "render")
load("time.star", "time")

# WALK_TO_BART_MINS = 9
# WALK_TO_CHURCH_MINS = 8


def main(config):
    timezone = config.get("timezone") or "America/New_York"
    now = time.now().in_location(timezone)

    return render.Root(delay=500, child=draw_muni_dot())


def render_test():
    return render.Box(
        child=render.Animation(
            children=[
                render.Text(
                    content="next",
                    # content = now.format("3:04 PM"),
                    font="6x13",
                ),
                render.Text(
                    content="train",
                    # content = now.format("3 04 PM"),
                    font="6x13",
                ),
                render.Circle(
                    color="#666",
                    diameter=30,
                    child=render.Circle(color="#0ff", diameter=10),
                ),
            ],
        ),
    )


def draw_muni_dot():
    return render.Stack(
        children=[
            render.Circle(
                color="#911",
                diameter=10,
                child=render.Text("J"),
            ),
            # render.Row(
            #     main_align="center", cross_align="center", children=[render.Text("F")]
            # ),
        ],
    )


def draw_muni_dot_test():
    return render.Stack(
        children=[
            render.Box(width=50, height=25, color="#911"),
            render.Text("hello there"),
            render.Box(width=4, height=32, color="#119"),
        ],
    )
