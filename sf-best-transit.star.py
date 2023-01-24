load("render.star", "render")
load("time.star", "time")
load("http.star", "http")
load("cache.star", "cache")
load("encoding/json.star", "json")

WALK_TO_BART_MINS = 9
WALK_TO_CHURCH_MINS = 8

COLORS_BY_LINE = {
    "J": "#D7892A",
    "K": "#74A0BB",
    "L": "#8F338E",
    "M": "#338246",
    "N": "#234C89",
    "T": "#BB3735",
    "BART": "#3F80DC",
}


BART_API_URI = "https://api.bart.gov/api/etd.aspx?cmd=etd&orig=16th&key=MW9S-E7SL-26DU-VV8V&dir=N&json=y"


def main(config):
    # timezone = config.get("timezone") or "America/New_York"
    # now = time.now().in_location(timezone)

    bart_data = None
    bart_data_cached = cache.get("bart_data")
    if bart_data_cached != None:
        print("Hit! Displaying cached data.")
        bart_data = json.decode(bart_data_cached)
    else:
        print("Miss! Fetching new bart data...")
        rep = http.get(BART_API_URI)
        if rep.status_code != 200:
            fail("Bart request failed with status %d", rep.status_code)
        bart_data = rep.json()
        cache.set("bart_data", str(bart_data), ttl_seconds=120)

    station_data = bart_data["root"]["station"][0]
    etds = station_data["etd"]
    all_estimates = []
    for etd in etds:
        for estimate in etd["estimate"]:
            all_estimates.append(estimate)

    # print(all_estimates)
    bart_trains_estimates_strs = [est["minutes"] for est in all_estimates]
    bart_trains_estimates_mins = [
        int(est_str) for est_str in bart_trains_estimates_strs
    ]
    sorted_bart_trains_estimates_mins = sorted(bart_trains_estimates_mins)
    print(
        "There are bart trains coming in "
        + ", ".join([str(s) for s in sorted_bart_trains_estimates_mins])
        + " mins"
    )

    # return render.Root(
    #     child = render.Text("BTC: %d USD" % rate)
    # )

    lines = ["J", "K", "L", "M", "N", "T"]
    return render.Root(delay=500, child=draw_muni_dots(lines))


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


def draw_muni_dots(lines):
    return render.Row(
        children=[draw_muni_dot(line) for line in lines],
    )


def draw_muni_dot(line):
    color = COLORS_BY_LINE[line]
    return render.Stack(
        children=[
            render.Circle(
                color=color,
                diameter=10,
                child=render.Text(
                    content=line,
                ),
            ),
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
