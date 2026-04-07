#!/usr/bin/env python
"""Create PostgreSQL database user and grant permissions."""

import sys

import psycopg2

# Try multiple password configurations for postgres
postgres_passwords = [
    "postgres",  # default
    "iamwhoiam",  # our standard password
    "",  # empty password
    "password",  # common default
]

connection_made = False
conn = None

for password in postgres_passwords:
    try:
        conn_str = "dbname=postgres user=postgres"
        if password:
            conn_str += f" password={password}"
        conn = psycopg2.connect(conn_str)
        connection_made = True
        print("✓ Connected to PostgreSQL")
        break
    except psycopg2.OperationalError:
        continue

if not connection_made:
    print("❌ Could not connect to PostgreSQL with any known password.")
    print("Please manually set postgres password in setup_db.py line 16")
    sys.exit(1)

try:
    if conn is None:
        sys.exit(1)
    cur = conn.cursor()

    # Create user matt
    try:
        cur.execute("CREATE USER matt WITH PASSWORD 'iamwhoiam'")
        print("✓ User matt created")
    except psycopg2.errors.DuplicateObject:
        print("✓ User matt already exists")

    # Grant privileges
    cur.execute("ALTER USER matt WITH SUPERUSER CREATEDB LOGIN")
    print("✓ Superuser privileges granted")

    cur.execute("GRANT ALL PRIVILEGES ON DATABASE kortana TO matt")
    print("✓ Database privileges granted")

    cur.execute("GRANT ALL ON SCHEMA public TO matt")
    print("✓ Schema permissions granted")

    conn.commit()
    cur.close()
    conn.close()
    print("\n✅ Database setup complete!")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
