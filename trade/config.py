from trade.api import get_client
import os
from dotenv import load_dotenv
from src.infrastructure.context_test_extensions.api_interface import FakeAPI

load_dotenv()


class Config(object):
    def __init__(self) -> None:
        self.ryan_key: str = os.getenv("RYAN_KEY")
        self.ryan_accountId: str = os.getenv("RYAN_ACCOUNTID")
        self.morgan_key: str = os.getenv("MORGAN_KEY")
        self.morgan_accountId: str = os.getenv("MORGAN_ACCOUNTID")
        self.callbackUri = "https://127.0.0.1:8080"
        self.secrets_path = f"{os.getcwd()}"
        self.params = {
            "API_KEY": self.morgan_key,
            "ACCOUNT_ID": self.morgan_accountId,
            "CALLBACK_URI": self.callbackUri,
            "SECRET_PATH": self.secrets_path,
            "TOKEN_NAME": "tokens/token.json",
            "AUTH": f"{self.morgan_key}@AMER.OAUTHAP",
        }

    def test(self, context) -> None:
        self.params["db"] = "test"
        self.csv_path = "test_files/test_csvs"
        self.mode = "test"
        self.params["client"] = FakeAPI(context)
        self.params["expiration"] = 1

    def real(self) -> None:
        self.params["client"] = get_client(
            self.params["SECRET_PATH"],
            self.params["AUTH"],
            self.params["CALLBACK_URI"],
            self.params["TOKEN_NAME"],
        )
        self.params["expiration"] = 30
        self.params["db"] = "ameritrade"
        self.csv_path = "csv_files"
        self.mode = "real"

    def ryan(self) -> None:
        self.params["API_KEY"] = self.ryan_key
        self.params["ACCOUNT_ID"] = self.ryan_accountId
        self.params["TOKEN_NAME"] = "tokens/ryan_token.json"
        self.params["AUTH"] = f"{self.ryan_key}@AMER.OAUTHAP"
