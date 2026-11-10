import csv
import inspect
import json
from pathlib import Path
from urllib.parse import urlparse
import requests
from filelock import FileLock
import time

class UserDataSaver:
    def __init__(self, folder):
        # Resolve folder relative to the script that creates this instance
        caller_frame = inspect.stack()[1]
        script_dir = Path(caller_frame.filename).resolve().parent
        self.output_dir = script_dir / folder

    def initialize_output_directory(self):
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def save_user_csv(self, username, data, filename):
        """
        Append one user row into a single shared CSV:
            output_dir / {filename}.csv

        Safe for multiple processes (uses file lock).
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / f"{filename}.csv"
        lock_path = filepath.with_suffix(".lock")

        # "source" column first, then the rest of the data
        row = {"source": username, **data}

        with FileLock(lock_path):                 # only one process can enter at a time
            file_exists = filepath.exists() and filepath.stat().st_size > 0

            with filepath.open(
                "a",
                encoding="utf-8-sig",
                newline=""
            ) as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())

                if not file_exists:
                    writer.writeheader()

                writer.writerow(row)

    def save_json(self, username, data, filename, credentials=None):
        """
        Append a JSON object into a list stored in:
            output_dir / {username}-{filename}.json

        - If the file does not exist → create it with an empty list [] as root
        - Merge the optional `credentials` dict (password, server_code, country_code, ...)
        into the data object before appending
        - Safe for multiple processes via FileLock
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / f"{filename}.json"
        lock_path = filepath.with_suffix(".lock")

        # 1. Make a copy of the data and add the extra fields
        row = dict(data)          # shallow copy so we don't mutate the original
        if credentials:
            row.update(credentials)   # adds password, server_code, country_code, etc.

        with FileLock(lock_path):                 # only one process can enter at a time
            # 2. Load existing root (or create empty list)
            if filepath.exists() and filepath.stat().st_size > 0:
                with filepath.open("r", encoding="utf-8") as f:
                    try:
                        root = json.load(f)
                    except json.JSONDecodeError:
                        root = []
                if not isinstance(root, list):
                    root = [root]                 # safety: force list if somehow not
            else:
                root = []

            # 3. Append the enriched object
            root.append(row)

            # 4. Write everything back
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(root, f, ensure_ascii=False, indent=2)

    def save_multiple_json(self, username, data, filename, credentials=None):
        """
        Save a JSON-serializable object (dict, list, etc.) to a .json file
        under output_dir / username / {filename}.json
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        filepath = self.output_dir/ f"{username}-{filename}.json"

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data.content, f, ensure_ascii=False, indent=2)



    def save_user_binary(self, username, data: bytes, filename: str, extension: str = "jpg"):
        """
        Save binary data (e.g. image bytes) to:
        output_dir / username / {filename}.{extension}
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / f"{filename}.{extension.lstrip('.')}"

        with filepath.open("wb") as f:          # "wb" = write binary
            f.write(data)

    def download_option_picture(
        self,
        json_obj: dict,
        attr_name: str,
        username: str,
        extension: str = "jpg",
        timeout: int = 15,
    ):
        url = json_obj.get(attr_name)
        if not url:
            return  # attribute missing or empty → do nothing

        def _do_download() -> None:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()  # raise if status is 4xx / 5xx
            self.save_user_binary(
                username=username,
                data=resp.content,
                filename=f"jpgs/{username}_{attr_name}",
                extension=extension,
            )

        # ── Attempt 1 ──────────────────────────────────────────────
        try:
            _do_download()
            return
        except requests.RequestException as e:
            print(f"Failed to download {attr_name} from {url}: {e} — retrying once...")
            time.sleep(1)

        # ── Attempt 2 ──────────────────────────────────────────────
        try:
            _do_download()
            return
        except requests.RequestException as e:
            print(
                f"Failed again to download {attr_name} from {url}: {e}. "
                "Waiting 5 minutes before final retry..."
            )
            time.sleep(5 * 60)  # 5 minutes

        # ── Attempt 3 (final) ──────────────────────────────────────
        try:
            _do_download()
        except requests.RequestException as e:
            print(f"Final attempt failed for {attr_name} from {url}: {e}. Giving up.")
            # just continue — do not re-raise