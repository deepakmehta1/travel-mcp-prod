import os
import psycopg
from datetime import date, timedelta

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "travel")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"

EMAIL = "arundeepak92@gmail.com"
PHONE = "+919999999999"
NAME = "Arundeepak"
TOUR_CODE = "GOA-5D4N-OPT2"


def main():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # ensure user/customer exists
            cur.execute(
                """
                INSERT INTO users (name, email, phone, password_hash)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                (NAME, EMAIL, PHONE, "pbkdf2_sha256$1$seed$deadbeef"),
            )
            cur.execute(
                """
                INSERT INTO customers (name, email, phone, preferences)
                VALUES (%s, %s, %s, '{}'::jsonb)
                ON CONFLICT (phone) DO NOTHING
                """,
                (NAME, EMAIL, PHONE),
            )
            cur.execute("SELECT id FROM customers WHERE phone = %s", (PHONE,))
            customer_id = cur.fetchone()[0]

            # ensure tour exists
            cur.execute(
                "SELECT code, base_price FROM tours WHERE code = %s", (TOUR_CODE,)
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Tour not found, seed tours first")
            base_price = row[1]

            # seed booking
            start_date = date.today() + timedelta(days=30)
            end_date = start_date + timedelta(days=4)
            cur.execute(
                """
                INSERT INTO bookings (customer_id, tour_code, start_date, end_date, total_price, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (customer_id, TOUR_CODE, start_date, end_date, base_price, "CONFIRMED"),
            )
            conn.commit()
            print("Seeded booking for", EMAIL)


if __name__ == "__main__":
    main()
