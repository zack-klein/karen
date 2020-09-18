from karen.leagues.espn import EspnLeague


PLATFORMS = {"ESPN": EspnLeague}


def get_league(
    platform_name, league_id, year, secret_name, platforms=PLATFORMS
):
    if platform_name not in platforms:
        raise NotImplementedError(
            f"Platform '{platform_name}' not supported!"
            f"\nMust be one of: {', '.join(platforms.keys())}."
        )

    platform = platforms.get(platform_name)
    league = platform(league_id, year, secret_name)
    return league
