from .crawl import Seed

WIKI_TITLES = [
    "Pittsburgh", "History_of_Pittsburgh", "Economy_of_Pittsburgh", "Education_in_Pittsburgh",
    "Culture_of_Pittsburgh", "Geography_of_Pittsburgh", "Neighborhoods_of_Pittsburgh",
    "Allegheny_County,_Pennsylvania", "Steel_City", "Point_State_Park", "Fort_Pitt_(Pennsylvania)",
    "Fort_Duquesne", "Duquesne_Incline", "Monongahela_Incline", "Pittsburgh_International_Airport",
    "Port_Authority_of_Allegheny_County", "Pittsburgh_Regional_Transit", "Pittsburgh_Marathon",
    "Carnegie_Mellon_University", "List_of_Carnegie_Mellon_University_people", "Allen_Newell",
    "Herbert_A._Simon", "International_Conference_on_Machine_Learning", "University_of_Pittsburgh",
    "Cathedral_of_Learning",
    "Pittsburgh_Steelers", "History_of_the_Pittsburgh_Steelers", "Chuck_Noll", "Bill_Cowher", "Mike_Tomlin",
    "Pittsburgh_Pirates", "History_of_the_Pittsburgh_Pirates", "Roberto_Clemente", "Pittsburgh_Penguins",
    "Heinz_Field", "Acrisure_Stadium", "PNC_Park", "PPG_Paints_Arena",
    "Carnegie_Museum_of_Art", "Carnegie_Museum_of_Natural_History", "Andy_Warhol_Museum", "Andy_Warhol",
    "Heinz_History_Center", "The_Frick_Pittsburgh", "Mattress_Factory", "List_of_museums_in_Pittsburgh",
    "Phipps_Conservatory_and_Botanical_Gardens", "National_Aviary", "Pittsburgh_Zoo_%26_PPG_Aquarium",
    "Kennywood", "Pittsburgh_Symphony_Orchestra", "Pittsburgh_Opera", "Pittsburgh_Cultural_Trust",
    "Pittsburgh_Public_Theater", "Pittsburgh_Ballet_Theatre", "Heinz_Hall", "Benedum_Center",
    "Mister_Rogers'_Neighborhood", "Picklesburgh", "Primanti_Bros.",
]

WIKI_CATEGORIES = [
    "Museums_in_Pittsburgh", "Buildings_and_structures_in_Pittsburgh", "History_of_Pittsburgh",
    "Culture_of_Pittsburgh", "Tourist_attractions_in_Pittsburgh", "Parks_in_Pittsburgh", "Festivals_in_Pittsburgh",
    "Music_venues_in_Pittsburgh", "Theatres_in_Pittsburgh", "Sports_in_Pittsburgh", "Sports_venues_in_Pittsburgh",
    "Carnegie_Mellon_University", "Universities_and_colleges_in_Pittsburgh", "Companies_based_in_Pittsburgh",
    "Bridges_in_Pittsburgh", "Neighborhoods_in_Pittsburgh", "Libraries_in_Pittsburgh", "Restaurants_in_Pittsburgh",
    "Pittsburgh_Steelers", "Pittsburgh_Pirates", "Pittsburgh_Penguins", "People_from_Pittsburgh",
]
WIKI_LISTS = ["List_of_museums_in_Pittsburgh", "List_of_bridges_of_Pittsburgh", "List_of_tallest_buildings_in_Pittsburgh",
              "List_of_Pittsburgh_neighborhoods", "List_of_people_from_Pittsburgh", "Timeline_of_Pittsburgh"]
WIKI_ARTICLE = r"en\.wikipedia\.org/wiki/[^:]+$"
PITTSBURGH_WORDS = (r"(?i)en\.wikipedia\.org/wiki/[^:]*(Pittsburgh|Allegheny|Carnegie|Mellon|Steelers|Pirates|Penguins|"
                    r"Duquesne|Monongahela|Heinz|Frick|Warhol|Phipps|Kennywood|Squirrel_Hill|Oakland|Shadyside|"
                    r"Lawrenceville|Strip_District|North_Shore|Mount_Washington)[^:]*$")

COLLEGE_SITES = {"pitt": "pittsburghpanthers.com", "duquesne": "goduquesne.com",
                 "rmu": "rmucolonials.com", "chatham": "gochathamcougars.com"}
COLLEGE_SPORTS = ["football", "mens-basketball", "womens-basketball", "womens-volleyball", "mens-soccer",
                  "womens-soccer", "mens-ice-hockey", "womens-ice-hockey", "baseball", "softball",
                  "wrestling", "womens-lacrosse", "mens-lacrosse", "field-hockey"]

SEEDS = [
    Seed("wikipedia", [f"https://en.wikipedia.org/wiki/{t}" for t in WIKI_TITLES], "general",
         max_depth=0, max_pages=len(WIKI_TITLES), follow_links=False),
    Seed("wiki_categories", [f"https://en.wikipedia.org/wiki/Category:{c}" for c in WIKI_CATEGORIES]
         + [f"https://en.wikipedia.org/wiki/{t}" for t in WIKI_LISTS], "general",
         max_depth=1, max_pages=900, allow=WIKI_ARTICLE),
    Seed("wiki_related", [f"https://en.wikipedia.org/wiki/{t}" for t in WIKI_TITLES[:25]], "general",
         max_depth=1, max_pages=400, allow=PITTSBURGH_WORDS),
    Seed("city_pgh", ["https://www.pittsburghpa.gov/Home",
                      "https://www.pittsburghpa.gov/City-Government/Finance-Budget/Taxes"], "general",
         max_depth=2, max_pages=150,
         allow=r"(?i)(Finance-Budget|Taxes|Tax-|About|History|Departments|Recreation-Events|Events)",
         deny=r"(?i)(login|search|calendar\?|oc_lang)"),
    Seed("city_tax_forms", ["https://pittsburghpa.gov/finance/tax-forms"], "tax",
         max_depth=1, max_pages=60, domains=["pittsburghpa.gov"], allow=r"(?i)(tax|regulation|\.pdf|finance)"),
    Seed("city_budget_pdf", ["https://www.pittsburghpa.gov/files/assets/city/v/4/omb/documents/"
                             "operating-budgets/2025-operating-budget.pdf"], "budget",
         max_depth=0, max_pages=1, follow_links=False),
    Seed("visit_pgh", ["https://www.visitpittsburgh.com"], "general", max_depth=2, max_pages=250,
         allow=r"(?i)(things-to-do|events-festivals|food|music|sports|history|neighborhoods|arts|museum|attractions|about)",
         deny=r"(?i)(login|account|meetings|trip-planner|itinerary|\?page=)"),
    Seed("cmu_about", ["https://www.cmu.edu/about/", "https://www.cmu.edu/about/history.html"], "cmu",
         max_depth=2, max_pages=80, domains=["cmu.edu"],
         allow=r"cmu\.edu/(about|admission|academics|research|news|leadership)"),

    Seed("pgh_events", ["https://pittsburgh.events"], "events", max_depth=2, max_pages=900,
         allow=r"pittsburgh\.events/(tickets|event|venue|this-month|[a-z\-]*-events|concerts|sports|comedy|theat)"),
    Seed("cmu_events", ["https://events.cmu.edu", "https://www.cmu.edu/engage/alumni/events/campus/index.html"],
         "events", max_depth=1, max_pages=80, domains=["events.cmu.edu", "cmu.edu"]),
    Seed("pgh_improv", ["https://pittsburgh.improv.com/"], "events", max_depth=2, max_pages=150,
         allow=r"pittsburgh\.improv\.com"),
    Seed("arcade_comedy", ["https://www.arcadecomedytheater.com/"], "events", max_depth=2, max_pages=80),
    Seed("savoyards", ["https://pittsburghsavoyards.org/"], "culture", max_depth=2, max_pages=40),

    Seed("symphony", ["https://www.pittsburghsymphony.org"], "culture", max_depth=2, max_pages=100,
         allow=r"(?i)(calendar|event|concert|about|history|season|performance)"),
    Seed("opera", ["https://pittsburghopera.org"], "culture", max_depth=2, max_pages=60),
    Seed("trust_arts", ["https://trustarts.org"], "culture", max_depth=2, max_pages=150,
         allow=r"(?i)(calendar|event|venue|about|history|production)"),
    Seed("carnegie_museums", ["https://carnegiemuseums.org"], "museum", max_depth=2, max_pages=120),
    Seed("heinz_history", ["https://www.heinzhistorycenter.org"], "museum", max_depth=2, max_pages=100),
    Seed("frick", ["https://www.thefrickpittsburgh.org"], "museum", max_depth=2, max_pages=60),
    Seed("warhol", ["https://www.warhol.org"], "museum", max_depth=2, max_pages=60),

    Seed("picklesburgh", ["https://www.picklesburgh.com/"], "food", max_depth=2, max_pages=30),
    Seed("taco_fest", ["https://www.pghtacofest.com/"], "food", max_depth=2, max_pages=30),
    Seed("restaurant_week", ["https://pittsburghrestaurantweek.com/"], "food", max_depth=2, max_pages=30),
    Seed("visit_food_fests", ["https://www.visitpittsburgh.com/events-festivals/food-festivals/"], "food",
         max_depth=1, max_pages=40, allow=r"events-festivals"),

    Seed("visit_sports", ["https://www.visitpittsburgh.com/things-to-do/pittsburgh-sports-teams/"], "sports",
         max_depth=1, max_pages=30, allow=r"sports"),
    Seed("steelers", ["https://www.steelers.com/team/players-roster/", "https://www.steelers.com/schedule/",
                      "https://www.steelers.com/team/coaches-roster/", "https://www.steelers.com/team/"], "sports",
         max_depth=1, max_pages=80, allow=r"steelers\.com/(team|schedule|history|stadium|news/)"),
    Seed("pirates", ["https://www.mlb.com/pirates", "https://www.mlb.com/pirates/schedule",
                     "https://www.mlb.com/pirates/roster", "https://www.mlb.com/pirates/team/history"], "sports",
         max_depth=1, max_pages=120, allow=r"mlb\.com/(pirates|player/)"),
    Seed("penguins", ["https://www.nhl.com/penguins/", "https://www.nhl.com/penguins/schedule",
                      "https://www.nhl.com/penguins/roster"], "sports",
         max_depth=1, max_pages=40, allow=r"nhl\.com/penguins"),
] + [
    Seed(f"college_{name}", [f"https://{site}/sports/{sport}/{page}" for sport in COLLEGE_SPORTS
                              for page in ("schedule/text", "coaches")],
         "sports", max_depth=0, max_pages=2 * len(COLLEGE_SPORTS), follow_links=False)
    for name, site in COLLEGE_SITES.items()
]
