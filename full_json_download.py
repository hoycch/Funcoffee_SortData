import re
from library import UserDataSaver, get_config, ApiClient

def download_all_data(phone_number, password, server_code, country_code, home_dir):
    
    saving_folder = UserDataSaver(f"{home_dir}")
    full_phone = f"{country_code}-{phone_number}"
    cfg = get_config(server_code)
    with ApiClient(cfg) as client:
        try:
            print(f"working on {country_code}-{phone_number} with <{password}>" )
            token = client.login(country_code, phone_number, password)
            if token is not None:
                json = client.get_json(cfg.USER_INFO_URL, token=token)
                saving_folder.save_json(full_phone, json, "user_info", {"server_code": server_code, "country_code": country_code, "password": password})
                saving_folder.download_option_picture(json.get("row"), "avatar", full_phone)
                user_id = json.get("row", {}).get("userId")
                json = client.get_json(cfg.TEAM_INFO_URL, token=token, data={"userId": user_id})
                saving_folder.save_json(full_phone, json, "team_info")

                json = client.get_json(cfg.AUTH_CHECK_URL, token=token)
                saving_folder.save_json(full_phone, json, "Invest_Auth")
                if json.get("row"):
                    saving_folder.download_option_picture(json.get("row"), "sfz1", full_phone)
                    saving_folder.download_option_picture(json.get("row"), "sfz2", full_phone)

                json = client.get_multiple_json(cfg.INVEST_RECORD_URL, token=token, data={"size": 10000,"currentNum": 1,"entity": {}})
                saving_folder.save_user_binary(full_phone, json.content, f"InvestRecord/{server_code}_{full_phone}", "json")

                json = client.get_multiple_json(cfg.CAPITAL_FLOW_URL, token=token, data={"size": 100000,"currentNum": 1,"entity": {}})
                saving_folder.save_user_binary(full_phone, json.content, f"CapitalFlow/{server_code}_{full_phone}", "json")
                

        except Exception as e:
            print(e)
    return phone_number
    