"""
Nexus-Prime-Omega Credentials
PAT and FG token are injected at runtime via GitHub Secrets:
  GH_PAT     -> github_token()
  GH_PAT_FG  -> github_token_fg()
All other creds are hardcoded (non-secret data like usernames, sites).
"""
import os

class Accounts:
    GITHUB_USERNAME   = "NexusPrime1112"
    GITHUB_PASSWORD   = "NEXUSPRIME--1112"
    GITHUB_FIRST_REPO = "https://github.com/NexusPrime1112/v1"

    @classmethod
    def github_token(cls):
        """Read from GitHub Actions secret GH_PAT (injected at runtime)."""
        return os.environ.get("GH_PAT", "")

    @classmethod
    def github_token_fg(cls):
        """Read from GitHub Actions secret GH_PAT_FG (injected at runtime)."""
        return os.environ.get("GH_PAT_FG", "")

    TWITTER_USERNAME    = "NexusPrime1112"
    TWITTER_PASSWORD    = "NEXUSPRIME--1112"
    TWITTER_DM_PASSCODE = "2000"
    GOOGLE_EMAIL    = "dprjfacts@gmail.com"
    GOOGLE_PASSWORD = "D4P16R18J10"
    PROTON_USERNAME = "nexusprime1112@proton.me"
    PROTON_PASSWORD = "NEXUSPRIME--1112k"
    CHROME_PROFILE_PATH = 'cook'
    BRO_REPO = 'https://github.com/NexusPrime1112/bro.git'
    BRO_REPO_NAME = 'bro'
    CHATGPT_URL = 'https://chatgpt.com'
    DEEPSEEK_URL = 'https://chat.deepseek.com'
    CHATGPT_EMAIL    = "dprjfacts@gmail.com"
    CHATGPT_PASSWORD = "D4P16R18J10k"
    DEEPSEEK_EMAIL   = "dprjfacts@gmail.com"
    DEEPSEEK_PASSWORD = "D4P16R18J10"
    OTP_ROUTING = {
        "github":  ["gmail", "protonmail"],
        "twitter": ["gmail"],
        "x.com":   ["gmail"],
        "default": ["gmail", "protonmail"],
    }
    NEW_ACCOUNTS = []
