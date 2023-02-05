"""
Applet: SFBestTransit
Summary: See next transit arrivals for both Muni and Bart
Description: See next transit arrivals from SFMTA and BART. Optimized for 2 nearby stops.
Author: hassoncs
"""


load("render.star", "render")
load("schema.star", "schema")
load("time.star", "time")
load("http.star", "http")
load("cache.star", "cache")
load("math.star", "math")
load("animation.star", "animation")
load("encoding/json.star", "json")

CACHE_TTL = 60
FPS_ESTIMATE = 20


BART_PUBLIC_API_KEY = "MW9S-E7SL-26DU-VV8V"
MUNI_API_KEY = "063bab8e-6059-46b0-9c74-ddad0540a6d1"

BART_FIXTURE = [
    {"mins": 2, "color": "#339933"},
    {"mins": 4, "color": "#339933"},
    {"mins": 10, "color": "#0099cc"},
    {"mins": 12, "color": "#ffff33"},
    {"mins": 19, "color": "#0099cc"},
    {"mins": 73, "color": "#ffff33"},
]
MUNI_FIXTURE = [
    {"mins": 4, "line": "K"},
    {"mins": 11, "line": "J"},
    {"mins": 15, "line": "M"},
    {"mins": 18, "line": "S"},
    {"mins": 36, "line": "K"},
]

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

BART_STOP_NAMES_BY_STOP_ID = {
    "12TH": "12th St. Oakland City Center",
    "16TH": "16th St. Mission",
    "19TH": "19th St. Oakland",
    "24TH": "24th St. Mission",
    "ANTC": "Antioch",
    "ASHB": "Ashby",
    "BALB": "Balboa Park",
    "BAYF": "Bay Fair",
    "BERY": "Berryessa",
    "CAST": "Castro Valley",
    "CIVC": "Civic Center/UN Plaza",
    "COLM": "Colma",
    "CONC": "Concord",
    "DALY": "Daly City",
    "DBRK": "Downtown Berkeley",
    "DUBL": "Dublin/Pleasanton",
    "DELN": "El Cerrito Del Norte",
    "PLZA": "El Cerrito Plaza",
    "EMBR": "Embarcadero",
    "FRMT": "Fremont",
    "FTVL": "Fruitvale",
    "GLEN": "Glen Park",
    "HAYW": "Hayward",
    "LAFY": "Lafayette",
    "LAKE": "Lake Merritt Daly City/Richmond",
    "MCAR": "MacArthur Richmond/Antioch",
    "MLBR": "Millbrae SFO/Antioch/Richmond",
    "MLPT": "Milpitas Daly City/Richmond",
    "MONT": "Montgomery St. East Bay",
    "NBRK": "North Berkeley Richmond",
    "NCON": "North Concord/Martinez Antioch",
    "COLS": "Oakland Coliseum - OAC Daly City/Richmond",
    "OAKL": "Oakland International Airport Coliseum",
    "ORIN": "Orinda Antioch",
    "PCTR": "Pittsburg Center Antioch",
    "PITT": "Pittsburg/Bay Point Antioch",
    "PHIL": "Pleasant Hill/Contra Costa Centre Antioch",
    "POWL": "Powell St. East Bay",
    "RICH": "Richmond Daly City/Millbrae/Berryessa",
    "ROCK": "Rockridge Antioch",
    "SBRN": "San Bruno Antioch/Richmond",
    "SFIA": "San Francisco International AirporSF/Antioch",
    "SANL": "San Leandro Daly City/Richmond",
    "SHAY": "South Hayward Daly City/Richmond",
    "SSAN": "South San Francisco Antioch/Richmond",
    "UCTY": "Union City Daly City/Richmond",
    "WCRK": "Walnut Creek",
    "WARM": "Warm Springs/South Fremont",
    "WDUB": "West Dublin/Pleasanton",
    "WOAK": "West Oakland",
}

BART_DIRECTIONS_SCHEMA_OPTIONS = [
    schema.Option(
        display="North",
        value="N",
    ),
    schema.Option(
        display="South",
        value="S",
    ),
]


def main(config):
    bart_ests_mins_all = get_bart_data(config)
    muni_estimates_all = get_muni_data(config)

    bart_ests_mins = bart_ests_mins_all[0:3]
    muni_estimates = muni_estimates_all[0:3]

    print(
        "There are bart trains coming in "
        + ", ".join([str(est["mins"]) for est in bart_ests_mins])
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
    bart_station_options = [
        schema.Option(
            display=BART_STOP_NAMES_BY_STOP_ID[key],
            value=key,
        )
        for key in BART_STOP_NAMES_BY_STOP_ID.keys()
    ]
    return schema.Schema(
        version="1",
        fields=[
            schema.Text(
                id="muni_stop_id",
                name="MUNI stop_id",
                desc="Enter a muni stop_id",
                icon="user",
                default="15726",
            ),
            schema.Text(
                id="muni_filter_below_mins",
                name="muni_filter_below_mins",
                desc="Don't show arrivals under this many mins",
                icon="user",
                default="0",
            ),
            schema.Dropdown(
                id="bart_stop_id",
                name="BART stop",
                desc="The bart stop to use.",
                icon="brush",
                default=bart_station_options[0].value,
                options=bart_station_options,
            ),
            schema.Dropdown(
                id="bart_dir",
                name="BART Direction",
                desc="The direction to show.",
                icon="brush",
                default=BART_DIRECTIONS_SCHEMA_OPTIONS[0].value,
                options=BART_DIRECTIONS_SCHEMA_OPTIONS,
            ),
            schema.Text(
                id="bart_filter_below_mins",
                name="bart_filter_below_mins",
                desc="Don't show arrivals under this many mins",
                icon="user",
                default="0",
            ),
            schema.Toggle(
                id="use_test_data",
                name="use_test_data",
                desc="use_test_data",
                icon="compress",
            ),
        ],
    )


def build_bart_api_url(bart_stop_id, bart_dir):
    return "https://api.bart.gov/api/etd.aspx?cmd=etd&key=%s&orig=%s&dir=%s&json=y" % (
        BART_PUBLIC_API_KEY,
        bart_stop_id,
        bart_dir,
    )


def get_bart_data(config):
    bart_stop_id = config.str("bart_stop_id")
    if bart_stop_id == None:
        fail("bart_stop_id not set in config")

    bart_dir = config.str("bart_dir")
    if bart_dir == None:
        fail("bart_dir not set in config")

    if config.bool("use_test_data", False):
        bart_ests_mins = BART_FIXTURE
    else:
        bart_api_url = build_bart_api_url(bart_stop_id, bart_dir)
        bart_data = fetch_data(bart_api_url, bart_api_url)

        station_data = bart_data["root"]["station"][0]
        etds = station_data["etd"]
        all_estimates = []
        for etd in etds:
            for estimate in etd["estimate"]:
                all_estimates.append(estimate)

        unsorted_bart_trains_estimates_mins = [
            {"mins": int(est["minutes"]), "color": est["hexcolor"]}
            for est in all_estimates
            if est["minutes"].isdigit()
        ]
        bart_ests_mins = sorted(
            unsorted_bart_trains_estimates_mins,
            lambda x: x["mins"],
        )
    bart_filter_below_mins = int(config.get("bart_filter_below_mins", "0"))
    bart_ests_mins_filtered = [
        x for x in bart_ests_mins if x["mins"] >= bart_filter_below_mins
    ]
    return bart_ests_mins_filtered


def build_muni_api_url(muni_stop_id):
    return (
        "http://api.511.org/transit/StopMonitoring?api_key=%s&agency=SF&format=json&stopCode=%s"
        % (MUNI_API_KEY, muni_stop_id)
    )


def get_muni_data(config):
    muni_stop_id = config.str("muni_stop_id")
    if muni_stop_id == None:
        fail("muni_stop_id not set in config")

    if config.bool("use_test_data", False):
        muni_estimates = MUNI_FIXTURE
    else:
        muni_api_url = build_muni_api_url(muni_stop_id)
        muni_data = fetch_data(muni_api_url, muni_api_url)
        stop_visits = muni_data["ServiceDelivery"]["StopMonitoringDelivery"][
            "MonitoredStopVisit"
        ]
        muni_estimates = [
            extract_muni_stop_visit(stop_visit) for stop_visit in stop_visits
        ]

    muni_filter_below_mins = int(config.get("muni_filter_below_mins", "0"))
    muni_estimates_filtered = [
        est for est in muni_estimates if est["mins"] >= muni_filter_below_mins
    ]
    return muni_estimates_filtered


def extract_muni_stop_visit(stop_visit):
    journey = stop_visit["MonitoredVehicleJourney"]
    expected_arrival_time = journey["MonitoredCall"]["ExpectedArrivalTime"]
    expected_arrival = time.parse_time(expected_arrival_time)
    duration = expected_arrival - time.now()
    mins = math.floor(duration.minutes)
    return {
        "line": journey["LineRef"],
        "mins": mins,
    }


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
            render_progress_bar(),
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
    return render.Padding(
        child=render.Row(
            children=[
                render.Text(content="BART ", font="tb-8"),
                render.Row(
                    children=[render_bart_estimate(est) for est in bart_ests_mins]
                ),
            ],
            expanded=True,
            main_align="center",
            cross_align="center",
        ),
        pad=(0, 0, 0, 0),
    )


def render_bart_estimate(est):
    return render.Padding(
        child=render.Row(
            children=[
                render.Padding(
                    child=render.Box(width=2, height=6, color=est["color"]),
                    pad=(0, 1, 0, 0),
                ),
                render.Text(content=str(est["mins"]), font="tb-8"),
            ]
        ),
        pad=(0, 0, 0, 0),
    )


def render_muni_times(muni_estimates):
    items = [render_muni_estimate(est) for est in muni_estimates]
    return render.Row(
        children=items,
        expanded=True,
        main_align="center",
        cross_align="center",
    )


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
    return render.Row(
        children=[render_muni_dot(line) for line in lines],
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
