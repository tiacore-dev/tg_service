# utils.py

from urllib.parse import quote, unquote


def slugify(text: str) -> str:
    return quote(text.strip().lower().replace(" ", "_"))


def unslugify(slug: str) -> str:
    return unquote(slug).replace("_", " ").title()


def find_route_by_slug(routes: list[dict], send_slug: str, rec_slug: str) -> dict | None:
    for route in routes:
        if slugify(route['sendCity']) == send_slug and slugify(route['recCity']) == rec_slug:
            return route
    return None
