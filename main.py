# -------------------------ABOUT --------------------------

# pyinstaller --onefile --windowed --name generate_owner_data gui.py --clean --add-data "main.py;." --hidden-import pandas --hidden-import tqdm
# Tool: BUDB Upload MySQL
# Developer: dyoliya
# Created: 2025-10-07

# © 2025 dyoliya. All rights reserved.

# ---------------------------------------------------------

import sqlite3
import pymysql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ----------------------- DIRECTORIES -----------------------
def exe_dir():
    """Get folder where the exe (or script) is located"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)   # running as exe
    return os.path.dirname(os.path.abspath(__file__))  # running as script

BASE_DIR = exe_dir()
DEFAULT_BOTTOMS_UP_FOLDER = os.path.join(BASE_DIR, "database")
os.makedirs(DEFAULT_BOTTOMS_UP_FOLDER, exist_ok=True)

# ----------------------- COLUMN MAPPING -----------------------
column_mapping = {
    "id": "id",
    "source_name": "source_name",
    "date_created": "date_created",
    "Owner ID": "owner_id",
    "Owner": "owner",
    "Combined Name": "combined_name",
    "First Name": "first_name",
    "Middle Name": "middle_name",
    "Last Name": "last_name",
    "Input: Address": "input_address",
    "Input: City": "input_city",
    "Input: State": "input_state",
    "Input: Zip Code": "input_zip_code",
    "County": "county",
    "State": "state",
    "county_of_interest": "county_of_interest",
    "Contact Type": "contact_type",
    "ATTN": "attn",
    "# of Interests": "number_of_interests",
    "contact_group_id": "contact_group_id",
    "multiple_county_count": "multiple_county_count",
    "all_counties": "all_counties",
    "is_latest_offer": "is_latest_offer",
    "Category": "category",
    "PDP Value ($)": "pdp_value",
    "Total Value - Low ($)": "total_value_low",
    "Total Value - High ($)": "total_value_high",
    "effective_total_value": "effective_total_value",
    "sum_of_all_offers": "sum_of_all_offers",
    "Address Changed": "address_changed",
    "Serial Number": "serial_number",
    "md_address": "md_address",
    "md_city": "md_city",
    "md_state": "md_state",
    "md_postalcode": "md_postal_code",
    "phone1": "phone1",
    "phone2": "phone2",
    "phone3": "phone3",
    "phone4": "phone4",
    "phone5": "phone5",
    "email1": "email1",
    "email2": "email2",
    "email3": "email3",
    "email4": "email4",
    "email5": "email5",
    "contact_id": "contact_id"
}

def load_mysql_config():
    env_path = Path("config") / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    return {
        "host": os.getenv("MYSQL_HOST"),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4")
    }

# ----------------------- MAIN FUNCTION -----------------------
def main(
    BOTTOMS_UP_FOLDER=DEFAULT_BOTTOMS_UP_FOLDER,
    sqlite_table="bottoms_up",
    mysql_table="bottoms_up_contacts",
    checkpoint_file="checkpoint.txt",
    batch_size=10000,
    test_limit=None,
    logger=print,
    progress_callback=None,
    truncate=None
):
    # --- Find .db file ---
    db_files = [f for f in os.listdir(BOTTOMS_UP_FOLDER) if f.lower().endswith(".db")]
    if len(db_files) == 0:
        raise FileNotFoundError(f"No .db file found in {BOTTOMS_UP_FOLDER}")
    elif len(db_files) > 1:
        raise RuntimeError(f"Only one db is allowed. But, multiple .db files found in\n{BOTTOMS_UP_FOLDER}.")
    sqlite_db_path = os.path.join(BOTTOMS_UP_FOLDER, db_files[0])
    logger(f"Using SQLite DB: {db_files[0]}")

    # --- Connect to SQLite ---
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_columns = ", ".join([f'"{col}"' for col in column_mapping.keys()])

    # --- Connect to MySQL ---
    mysql_config = load_mysql_config()
    mysql_conn = pymysql.connect(**mysql_config)
    mysql_cursor = mysql_conn.cursor()
    mysql_cursor.execute("SET SESSION sql_mode=''")

    # --- Read checkpoint ---
    last_id_uploaded = 0
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            last_id_uploaded = int(f.read().strip())

    # --- Ask to truncate MySQL if not empty ---
    mysql_cursor.execute(f"SELECT COUNT(*) FROM {mysql_table}")
    count_mysql_table = mysql_cursor.fetchone()[0]

    if count_mysql_table != 0:
        if truncate is None:
            # GUI must specify True/False
            raise RuntimeError("MySQL table is not empty. GUI must specify truncate=True/False.")
        elif truncate:
            logger("🧹 Truncating MySQL table...")
            mysql_cursor.execute(f"TRUNCATE TABLE {mysql_table}")
            mysql_conn.commit()
            last_id_uploaded = 0
            with open(checkpoint_file, "w") as f:
                f.write("0")
            logger("✅ Table truncated. Checkpoint reset.")


    # --- Determine total rows to upload ---
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {sqlite_table} WHERE id > ?", (last_id_uploaded,))
    total_rows = sqlite_cursor.fetchone()[0]
    if test_limit:
        total_rows = min(total_rows, test_limit)

    if total_rows == 0:
        logger("ℹ️ No new rows to upload.")
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()
        return

    # --- Prepare insert query ---
    mysql_columns = ", ".join([f"`{col}`" for col in column_mapping.values()])
    placeholders = ", ".join(["%s"] * len(column_mapping))
    insert_query = f"INSERT INTO {mysql_table} ({mysql_columns}) VALUES ({placeholders})"

    # --- Fetch SQLite rows starting from last uploaded ID ---
    sqlite_cursor.execute(f"""
        SELECT {sqlite_columns} 
        FROM {sqlite_table} 
        WHERE id > ? 
        ORDER BY id
    """, (last_id_uploaded,))

    # --- Batch insert with checkpoint & progress ---
    processed_rows = 0
    while True:
        if test_limit:
            remaining = test_limit - processed_rows
            if remaining <= 0:
                break
            batch = sqlite_cursor.fetchmany(min(batch_size, remaining))
        else:
            batch = sqlite_cursor.fetchmany(batch_size)

        if not batch:
            break

        try:
            mysql_cursor.executemany(insert_query, batch)
            mysql_conn.commit()
        except Exception as e:
            logger(f"❌ Error inserting batch starting at id {batch[0][0]}: {e}")
            break

        # --- Row-level progress ---
        for i, row in enumerate(batch, start=1):
            processed_rows += 1
            if progress_callback and processed_rows % 100 == 0:
                progress_fraction = processed_rows / total_rows
                progress_callback(progress_fraction, sqlite_db_path)


        # --- Update checkpoint ---
        last_id_in_batch = batch[-1][0]
        with open(checkpoint_file, "w") as f:
            f.write(str(last_id_in_batch))

    logger(f"✅ Upload complete. Total rows inserted: {processed_rows}")

    # --- Verify MySQL table count ---
    mysql_cursor.execute(f"SELECT COUNT(*) FROM {mysql_table}")
    actual_rows = mysql_cursor.fetchone()[0]
    logger(f"ℹ️  Total rows currently in MySQL table '{mysql_table}': {actual_rows}")

    # --- Cleanup ---
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()


# ----------------------- RUN DIRECTLY -----------------------
if __name__ == "__main__":
    main()
