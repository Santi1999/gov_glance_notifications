"""FCM topic names. Must stay identical to notificationTopics.js in the app.

FCM topic names are case-sensitive, so "legislativeNews" and
"LegislativeNews" are different topics.
"""

# Keys must match the country values passed to build_push_topic. The app uses
# us / ca / mx / uk; if the database's country_schema values differ, map them
# to these keys before calling build_push_topic.
COUNTRY_PREFIXES = {
    "us": "",
    "ca": "Canada",
    "mx": "Mexico",
    "uk": "UK",
}

BRANCH_TOPICS = {
    "legislative": "LegislativeNews",
    "executive": "ExecutiveNews",
    "judicial": "JudicialNews",
    "defense": "DefenseNews",
    "defence": "DefenseNews",
    "economy": "EconomyNews",
    "environment": "EnvironmentNews",
    "foreign affairs": "ForeignAffairsNews",
    "foreignaffairs": "ForeignAffairsNews",
    "health": "HealthNews",
    "elections": "ElectionNews",
    "science & tech": "ScienceTechNews",
    "sciencetech": "ScienceTechNews",
    "science": "ScienceTechNews",
    "spending": "SpendingNews",
    "infrastructure": "InfrastructureNews",
    "regulations": "RegulationsNews",
    "justice": "JusticeNews",
}

DEFAULT_TOPIC = "GovGlanceNews"


def build_push_topic(branch, country="us"):
    prefix = COUNTRY_PREFIXES.get((country or "us").strip().lower(), "")
    name = BRANCH_TOPICS.get((branch or "").strip().lower(), DEFAULT_TOPIC)
    return f"{prefix}{name}"