load("render.star", "render")
load("schema.star", "schema")
load("time.star", "time")
load("http.star", "http")
load("cache.star", "cache")
load("math.star", "math")
load("animation.star", "animation")
load("encoding/json.star", "json")

USE_FIXTURE_DATA = False  # True
FPS_ESTIMATE = 20
CACHE_TTL = 60

COLORS_BY_LINE = {
    "J": {"background": "#D7892A", "text": "#FFF"},
    "K": {"background": "#74A0BB", "text": "#FFF"},
    "L": {"background": "#8F338E", "text": "#FFF"},
    "M": {"background": "#338246", "text": "#FFF"},
    "N": {"background": "#234C89", "text": "#FFF"},
    "T": {"background": "#BB3735", "text": "#FFF"},
    "S": {"background": "#FFFF35", "text": "#000"},
    "BART": {"background": "#3F80DC", "text": "#FFF"},
}

BART_FILTER_BELOW_MINS = 10
BART_STOP_ID = "16th"
BART_DIR = "N"
BART_API_KEY = "MW9S-E7SL-26DU-VV8V"
BART_API_URI = (
    "https://api.bart.gov/api/etd.aspx?cmd=etd&key=%s&orig=%s&dir=%s&json=y"
    % (BART_API_KEY, BART_STOP_ID, BART_DIR)
)
BART_CACHE_KEY = "bart_data"

MUNI_FILTER_BELOW_MINS = 9
MUNI_STOP_ID = 15726
MUNI_API_KEY = "063bab8e-6059-46b0-9c74-ddad0540a6d1"
MUNI_API_URI = (
    "http://api.511.org/transit/StopMonitoring?api_key=%s&agency=SF&format=json&stopCode=%d"
    % (MUNI_API_KEY, MUNI_STOP_ID)
)
MUNI_CACHE_KEY = "muni_data"


def main(config):
    muni_stop_id = config.get("muni_stop_id")
    print(muni_stop_id)

    if USE_FIXTURE_DATA:
        bart_ests_mins_all = [10, 12, 19, 73]
        muni_estimates_all = [
            {"mins": 11, "line": "J"},
            {"mins": 15, "line": "M"},
            {"mins": 18, "line": "S"},
            {"mins": 36, "line": "K"},
        ]
    else:
        bart_ests_mins_all = get_bart_data()
        muni_estimates_all = get_muni_data()

    bart_ests_mins = bart_ests_mins_all[0:3]
    muni_estimates = muni_estimates_all[0:3]

    print(
        "There are bart trains coming in "
        + ", ".join([str(s) for s in bart_ests_mins])
        + " mins"
    )
    print(
        "There are muni trains coming in "
        + ", ".join([str(est["mins"]) for est in muni_estimates])
        + " mins"
    )

    transit_data = {
        "bart_ests_mins": bart_ests_mins,
        "muni_estimates": muni_estimates,
    }
    return render.Root(delay=0, child=render_all(transit_data))


def get_schema():
    return schema.Schema(
        version="1",
        fields=[
            schema.Location(
                id="location",
                name="Location",
                desc="Location for which to display time.",
                icon="locationDot",
            ),
            schema.Text(
                id="muni_stop_id",
                name="MUNI stop_id",
                desc="Enter a muni stop_id",
                icon="user",
            ),
            schema.Text(
                id="bart_stop_id",
                name="BART stop_id",
                desc="Enter a bart stop_id",
                icon="user",
            ),
        ],
    )


def get_bart_data():
    bart_data = fetch_data(BART_CACHE_KEY, BART_API_URI)

    station_data = bart_data["root"]["station"][0]
    etds = station_data["etd"]
    all_estimates = []
    for etd in etds:
        for estimate in etd["estimate"]:
            all_estimates.append(estimate)

    bart_trains_estimates_strs = [est["minutes"] for est in all_estimates]
    unsorted_bart_trains_estimates_mins = [
        int(est_str) for est_str in bart_trains_estimates_strs if est_str.isdigit()
    ]
    bart_ests_mins = sorted(unsorted_bart_trains_estimates_mins)
    bart_ests_mins_filtered = [x for x in bart_ests_mins if x >= BART_FILTER_BELOW_MINS]
    return bart_ests_mins_filtered


def get_muni_data():
    muni_data = fetch_data(MUNI_CACHE_KEY, MUNI_API_URI)
    stop_visits = muni_data["ServiceDelivery"]["StopMonitoringDelivery"][
        "MonitoredStopVisit"
    ]

    def process_stop_visit(stop_visit):
        journey = stop_visit["MonitoredVehicleJourney"]
        expected_arrival_time = journey["MonitoredCall"]["ExpectedArrivalTime"]
        expected_arrival = time.parse_time(expected_arrival_time)
        duration = expected_arrival - time.now()
        mins = math.floor(duration.minutes)
        return {
            "line": journey["LineRef"],
            "mins": mins,
        }

    muni_estimates = [process_stop_visit(stop_visit) for stop_visit in stop_visits]
    muni_estimates_filtered = [
        est for est in muni_estimates if est["mins"] >= MUNI_FILTER_BELOW_MINS
    ]

    return muni_estimates_filtered


def fetch_data(cache_key, url):
    data_json_str = cache.get(cache_key)
    if data_json_str != None:
        print("Hit! Using cached %s data." % cache_key)
    else:
        print("Miss! Fetching new %s data..." % cache_key)
        rep = http.get(url)
        if rep.status_code != 200:
            fail("Request failed with status %d" % rep.status_code)

        body_str = rep.body()
        start_idx = body_str.find("{")
        data_json_str = body_str[start_idx:]
        cache.set(cache_key, data_json_str, ttl_seconds=CACHE_TTL)
    return json.decode(data_json_str)


def render_all(transit_data):
    lines = []
    bart_ests_mins = transit_data["bart_ests_mins"]
    muni_estimates = transit_data["muni_estimates"]
    return render.Stack(
        children=[
            render.Column(
                expanded=True,
                main_align="space_evenly",  # Controls horizontal alignment
                cross_align="center",  # Controls vertical alignment
                children=[
                    render_muni_times(muni_estimates),
                    render_bart_times(bart_ests_mins),
                ],
            ),
            # render_progress_bar(),
        ]
    )


def render_progress_bar():
    width = 6
    end_x = 64  # - width
    return animation.Transformation(
        child=render.Box(width=width, height=1, color="#ccc"),
        duration=FPS_ESTIMATE * 61,
        delay=0,
        # origin=animation.Origin(0.5, 0.5),
        # direction="alternate",
        fill_mode="forwards",
        keyframes=[
            animation.Keyframe(
                percentage=0.0,
                transforms=[
                    animation.Translate(0, 31),
                ],
                # curve="ease_in_out",
            ),
            animation.Keyframe(
                percentage=1.0,
                transforms=[
                    animation.Translate(end_x, 31),
                ],
            ),
        ],
    )


def render_bart_times(bart_ests_mins):
    times = " ".join([str(mins) for mins in bart_ests_mins])
    return render.Padding(
        child=render.Row(
            children=[
                render.Text(content="BART ", font="tb-8"),
                # render.Text(content="a ", color="#4498D4", font="tb-8"),
                render.Text(content=times, font="tb-8"),
            ]
        ),
        pad=(4, 0, 2, 0),
    )


def render_muni_times(muni_estimates):
    lines = [est["line"] for est in muni_estimates]
    times = " ".join([str(estimate["mins"]) for estimate in muni_estimates])
    items = [render_muni_estimate(est) for est in muni_estimates]
    # items = [render.Text(content="mins")]
    return render.Row(children=items)


def render_muni_estimate(estimate):
    return render.Padding(
        child=render.Row(
            children=[
                render_muni_dot(estimate["line"]),
                render.Text(content=str(estimate["mins"])),
            ]
        ),
        pad=(2, 0, 0, 0),
    )


def render_muni_dots(lines):
    return render.Padding(
        child=render.Row(
            children=[render_muni_dot(line) for line in lines],
        ),
        pad=(0, 0, 0, 0),
    )


def render_muni_dot(line):
    colors = COLORS_BY_LINE[line]
    background_color = colors["background"]
    text_color = colors["text"]
    return render.Padding(
        child=render.Stack(
            children=[
                render.Circle(
                    color=background_color,
                    diameter=8,
                    child=render.Text(content=line, color=text_color),
                ),
            ],
        ),
        pad=(0, 0, 1, 0),
    )
