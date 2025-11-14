# 📤 BUDB Upload to MySQL


**BUDB Upload to MySQL Tool** is a Python-based tool designed to efficiently transfer bottoms-up contact data from a local SQLite database to a MySQL server. It supports batch uploads, checkpointing for resuming interrupted processes, and optional table truncation. The tool ensures smooth integration with existing MySQL setups and is packaged for easy execution with PyInstaller.


---

![Version](https://img.shields.io/badge/version-1.0.0-ffab4c?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11%2B-273946?style=for-the-badge&logo=python&logoColor=ffab4c)
![Status](https://img.shields.io/badge/status-active-273946?style=for-the-badge&logo=github&logoColor=ffab4c)

---

## ✨ Features

- **SQLite to MySQL Upload**: Efficiently uploads data from a local SQLite `.db` file to a MySQL database with support for large datasets.
- **Automatic Column Mapping**: Predefined mapping ensures that columns from SQLite are correctly aligned with MySQL table columns.
- **Checkpointing**: Keeps track of the last uploaded row in a `checkpoint.txt` file, allowing safe resumption of uploads after failure.
- **Batch Processing**: Inserts rows by batches for optimized performance and reduced memory usage.
- **Truncate MySQL Table Option**: Safely clear the MySQL table before uploading, if required, and reset checkpoint automatically
- **Progress Tracking**: Supports a callback function to track upload progress, ideal for GUI integration.
- **Robust Error Handling**: Logs errors at batch level and ensures database connections are safely closed on failure.
- **Configurable via `.env`**: MySQL credentials and connection parameters can be stored securely in a `.env` file.
- **Cross-Platform Compatibility**: Works both as a standalone Python script and a packaged executable using PyInstaller.
- **Flexible Directory Handling**: Automatically detects the script/executable location and manages database folder creation.

---

## 📝 Requirements

- Python 3.11+
- `pandas`
- `pymysql`
- `sqlite3` (built-in)
- `customtkinter`
- `python-dotenv`

> Tip: You can install all dependencies via:
> ```bash
> pip install -r requirements.txt
> ```

---
## 🚀 Installation and Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/budb_upload_to_mysql.git
   cd budb_upload_to_mysql

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt

3. **Folder Structure**
    <pre>project/
    │
    ├── database/                      # Contains BUDB .db file
    ├── config/                        # Configuration files
    │   └── .env                       # Environment variables
    ├── gui.py                         # GUI interface
    ├── main.py                        # Main script
    ├── requirements.txt               # Dependencies
    └── checkpoint.txt                 # Checkpoint file
    </pre>

4. **Ensure the `.env` file contains the ffg. variables:**
    ```bash
    MYSQL_HOST=your_host
    MYSQL_USER=your_user
    MYSQL_PASSWORD=your_password
    MYSQL_DATABASE=your_database
    MYSQL_PORT=3306
    MYSQL_CHARSET=utf8mb4
    ```
   - The tool will automatically load these environment variables from `config/.env`.


5. **Compile the tool**
   ```bash
   pyinstaller --onefile --windowed --name budb_upload_to_mysql gui.py
---

## 🖥️ User Guide

1. **Opening the Tool**
   * Double-click the program file to start it.

2. **Checking Your Files**
   * When the tool opens, it will display the `.db` file(s) currently in the `database` folder.
   * Ensure that **only one (1) .db file** — the most recent BUDB — is in the folder.
   * If the file is missing or incorrect:
     * Click **Open database folder** to open the `database` folder and adjust your file.
     * Then click **Refresh** in the tool to reload the list.

3. **Uploading the BUDB Local File**
   * Make sure the display box shows the correct BUDB `.db` file.
   * Click the **UPLOAD BUDB** button.
   * If the MySQL table is not empty, a prompt will ask if you want to truncate it before uploading.
   * An **Uploading** window will appear — do not close it.
   * Wait until you see **“Upload finished successfully!”**.

> ⚠️ **Important Notes**
>
> * Do not close the **Uploading** popup before it finishes — this can interrupt the process.
> * You cannot run the tool twice at the same time.
> * The tool will ignore any file that is not a `.db` file.
> * If the upload is interrupted, the tool will resume from the last successfully uploaded row when run again.


---

## 👩‍💻 Credits
- **2025-10-07**: Project created by **Julia** ([@dyoliya](https://github.com/dyoliya))  
- 2025–present: Maintained by **Julia** for **Community Minerals II, LLC**
