import csv
import json
from collections import defaultdict

SOURCE = "data/external/cmoa/cmoa.csv"
OUT = "data/raw/cmoa.jsonl"

FIELDS = [
    ("Accession number", "accession_number"),
    ("Credit line", "credit_line"),
    ("Date acquired", "date_acquired"),
    ("Department", "department"),
    ("Physical location", "physical_location"),
    ("Creation date", "creation_date"),
    ("Medium", "medium"),
    ("Classification", "classification"),
]


def describe_artist(row):
    details = [row["nationality"], "-".join(x for x in (row["birth_date"][:4], row["death_date"][:4]) if x)]
    details = ", ".join(d for d in details if d)
    return f"{row['full_name']} ({details})" if details else row["full_name"]


def artwork_to_doc(rows):
    first = rows[0]
    artists = [describe_artist(r) for r in rows if r["full_name"]]
    lines = [f"Title: {first['title']}", f"Artist: {'; '.join(dict.fromkeys(artists)) or 'Unknown'}"]
    lines += [f"{label}: {first[key]}" for label, key in FIELDS if first[key]]
    return {"url": first["web_url"] or f"cmoa:{first['accession_number']}",
            "title": f"Carnegie Museum of Art collection: {first['title']}",
            "source": "cmoa", "source_type": "museum", "text": "\n".join(lines)}


def main():
    artworks = defaultdict(list)
    for row in csv.DictReader(open(SOURCE, encoding="utf-8")):
        artworks[row["accession_number"] or row["id"]].append(row)
    with open(OUT, "w", encoding="utf-8") as out:
        for rows in artworks.values():
            out.write(json.dumps(artwork_to_doc(rows), ensure_ascii=False) + "\n")
    print(f"{len(artworks)} artworks -> {OUT}")


if __name__ == "__main__":
    main()
