from karen.streamlit_apps import espn, yahoo


STREAMLIT_APPS = {
    "ESPN": espn.build_app,
    "Yahoo": yahoo.build_app,
}


def get_streamlit_app(
    st, platform, league_id, secret_name, platforms=STREAMLIT_APPS
):
    if platform not in platforms:
        raise NotImplementedError(
            f"'{platform}' is not a supported platform! Must be one of: "
            f"{', '.join(platforms.keys())}"
        )

    app_builder = platforms[platform]
    app = app_builder(st, league_id, secret_name)
    return app
