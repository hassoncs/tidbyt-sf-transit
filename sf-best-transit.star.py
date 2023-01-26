load("render.star", "render")
load("time.star", "time")
load("http.star", "http")
load("cache.star", "cache")
load("math.star", "math")
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
BART_CACHE_KEY = "bart_data"

MUNI_CHURCH_ST_STOP_ID = 15726
MUNI_API_URI = "http://api.511.org/transit/StopMonitoring?api_key=063bab8e-6059-46b0-9c74-ddad0540a6d1&agency=SF&format=json&stopCode=15726"
MUNI_CACHE_KEY = "muni_data"
CACHE_TTL = 120


def main(config):
    bart_ests_mins = get_bart_data()
    muni_estimates = get_muni_data()

    print(
        "There are bart trains coming in "
        + ", ".join([str(s) for s in bart_ests_mins])
        + " mins"
    )
    print(
        "There are muni trains coming in "
        + ", ".join([str(est["expected_arrival_mins"]) for est in muni_estimates])
        + " mins"
    )

    lines = ["J", "K", "L", "M", "N", "T"]
    bart_ests_mins = []
    # render it!
    return render.Root(
        delay=500, child=render_all(lines=lines, bart_ests_mins=bart_ests_mins)
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
        int(est_str) for est_str in bart_trains_estimates_strs
    ]
    bart_ests_mins = sorted(unsorted_bart_trains_estimates_mins)
    return bart_ests_mins


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
        expected_arrival_mins = math.floor(duration.minutes)
        return {
            "line": journey["LineRef"],
            "expected_arrival_mins": expected_arrival_mins,
        }

    muni_estimates = [process_stop_visit(stop_visit) for stop_visit in stop_visits]
    return muni_estimates


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


def render_all(lines, bart_ests_mins):
    return render.Column(
        children=[draw_muni_dots(lines), render_bart_times(bart_ests_mins)]
    )


def render_bart_times(bart_ests_mins):
    times = " ".join([str(mins) for mins in bart_ests_mins])
    return render.Row(children=[render.Text(content="bart " + times)])


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
