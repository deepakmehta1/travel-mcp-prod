import os
import psycopg
from psycopg.types.json import Json

# Configure connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "travel")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"

TOURS = [
    ("GOA-5D4N-OPT2", "Goa 5D/4N – Beachside", 38000, 4, "Goa"),
    ("DEL-3D2N-CITY", "Delhi 3D/2N – Heritage", 22000, 2, "Delhi"),
    ("BLR-3D2N-URBAN", "Bengaluru 3D/2N – Tech & Food", 21000, 2, "Bengaluru"),
    ("MUM-4D3N-COAST", "Mumbai 4D/3N – City & Coast", 26000, 3, "Mumbai"),
    ("JAIP-4D3N-PINK", "Jaipur 4D/3N – Forts & Bazaars", 24000, 3, "Jaipur"),
    ("KER-5D4N-BACK", "Kerala 5D/4N – Backwaters", 42000, 4, "Kerala"),
    ("LAD-6D5N-ALT", "Ladakh 6D/5N – High Altitude", 52000, 5, "Ladakh"),
    ("AGN-3D2N-WINE", "Nashik 3D/2N – Vineyards", 18000, 2, "Nashik"),
    ("KOL-3D2N-ART", "Kolkata 3D/2N – Culture & Cuisine", 20000, 2, "Kolkata"),
    ("PUN-3D2N-FOOD", "Pune 3D/2N – Food & History", 19000, 2, "Pune"),
    ("HYD-4D3N-CHAR", "Hyderabad 4D/3N – Charminar & Biryani", 23000, 3, "Hyderabad"),
]

DDL = """
CREATE TABLE IF NOT EXISTS tours (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_price INTEGER NOT NULL,
    nights INTEGER NOT NULL,
    destination TEXT NOT NULL
);
"""

SQL = """
INSERT INTO tours (code, name, base_price, nights, destination)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (code) DO NOTHING;
"""


def main():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.executemany(SQL, TOURS)
            conn.commit()
            cur.execute("SELECT COUNT(*) FROM tours")
            count = cur.fetchone()[0]
            print(f"Tours present: {count}")


if __name__ == "__main__":
    main()
