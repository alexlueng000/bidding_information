from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Bidding Information Platform"
    app_version: str = "0.1.0"
    app_description: str = "A platform for collecting bidding information from various sources."
    app_author: str = "branstark000"
    app_author_email: str = ""
    app_license: str = "MIT"
    app_copyright: str = "Copyright 2025 branstark000"

    database_url: str = ""
