"""
Збирає відгуки бізнесу з Google через офіційний Places API (їх дозволено показувати на сайті з підписом Google).
Один запит віддає максимум 5 відгуків, тому скрипт об'єднує кілька: найрелевантніші й найновіші, різними мовами.

  python3 get_reviews.py "Estoria Beauty Salon Spiridonos Lamprou 13a Limassol" demos/estoria/data/reviews.json

Ключ береться зі змінної середовища GOOGLE_MAPS_API_KEY.
"""
import json
import os
import sys

import requests

KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


def find_place_id(query):
    r = requests.post("https://places.googleapis.com/v1/places:searchText",
                      json={"textQuery": query, "pageSize": 1},
                      headers={"X-Goog-Api-Key": KEY, "X-Goog-FieldMask": "places.id,places.rating,places.userRatingCount"},
                      timeout=30)
    r.raise_for_status()
    p = r.json()["places"][0]
    return p["id"], p.get("rating"), p.get("userRatingCount")


def new_api(place_id, lang):
    r = requests.get(f"https://places.googleapis.com/v1/places/{place_id}",
                     params={"languageCode": lang},
                     headers={"X-Goog-Api-Key": KEY, "X-Goog-FieldMask": "reviews"}, timeout=30)
    if not r.ok:
        return []
    out = []
    for rv in r.json().get("reviews", []):
        t = rv.get("originalText") or rv.get("text") or {}
        a = rv.get("authorAttribution", {})
        out.append({"author": a.get("displayName", ""), "rating": rv.get("rating"), "text": t.get("text", ""),
                    "lang": t.get("languageCode", ""), "time": rv.get("publishTime", "")[:10],
                    "when": rv.get("relativePublishTimeDescription", ""), "url": rv.get("googleMapsUri", "")})
    return out


def legacy_api(place_id, lang, sort):
    r = requests.get("https://maps.googleapis.com/maps/api/place/details/json",
                     params={"place_id": place_id, "fields": "reviews", "language": lang, "reviews_sort": sort,
                             "reviews_no_translations": "true", "key": KEY}, timeout=30)
    if not r.ok or r.json().get("status") != "OK":
        return []
    from datetime import datetime, timezone
    out = []
    for rv in r.json().get("result", {}).get("reviews", []):
        out.append({"author": rv.get("author_name", ""), "rating": rv.get("rating"), "text": rv.get("text", ""),
                    "lang": rv.get("language", ""),
                    "time": datetime.fromtimestamp(rv.get("time", 0), timezone.utc).strftime("%Y-%m-%d"),
                    "when": rv.get("relative_time_description", ""), "url": rv.get("author_url", "")})
    return out


def main():
    if not KEY:
        sys.exit("Немає GOOGLE_MAPS_API_KEY")
    query, out_path = sys.argv[1], sys.argv[2]
    pid, rating, count = find_place_id(query)
    seen, reviews = set(), []
    batches = [new_api(pid, l) for l in ("ru", "en", "uk")]
    batches += [legacy_api(pid, l, s) for l in ("ru", "en") for s in ("most_relevant", "newest")]
    for batch in batches:
        for rv in batch:
            k = (rv["author"], rv["text"][:40])
            if rv["text"] and k not in seen:
                seen.add(k)
                reviews.append(rv)
    reviews.sort(key=lambda r: r["time"], reverse=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump({"place_id": pid, "rating": rating, "count": count, "reviews": reviews},
              open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    good = [r for r in reviews if (r["rating"] or 0) >= 4]
    print(f"Рейтинг {rating} ({count}). Унікальних відгуків з текстом: {len(reviews)}, з них 4–5★: {len(good)} -> {out_path}")


if __name__ == "__main__":
    main()
