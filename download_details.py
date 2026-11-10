from pathlib import Path

import pandas as pd

import full_json_download


ACCOUNTS_FILE = Path(__file__).parent / "old_data" / "user-info.json"


def download_accounts(accounts_file: Path = ACCOUNTS_FILE) -> None:
    target_json = pd.read_json('data/user_info.json')
    old_json = pd.read_json('old_data/user_info.json', dtype={"password", str})
    working_df = old_json[~old_json['row'].str.get('mobile').isin(target_json['row'].str.get('mobile'))]


    for i, user_obj in working_df.iterrows():
        
        full_json_download.download_all_data(
            user_obj['row'].get("mobile"),
            user_obj["password"],
            user_obj["server_code"],
            user_obj["country_code"],
            "data",
        )


if __name__ == "__main__":
    download_accounts()
