
from flask import Flask, render_template, request, jsonify, send_file
from youtube_transcript_api import YouTubeTranscriptApi
try:
    from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig
except ImportError:
    WebshareProxyConfig = None
    GenericProxyConfig = None

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import requests
import re
import os
import tempfile
import time
import html
import unicodedata


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

# =========================================================
# YOUTUBE TRANSCRIPT API / RENDER PROXY
# =========================================================
# Render/cloud IPs can be blocked by YouTube. When proxy
# credentials are configured in Render Environment Variables,
# all youtube-transcript-api requests use the proxy.
#
# Required Render variables for Webshare:
#   WEBSHARE_PROXY_USERNAME
#   WEBSHARE_PROXY_PASSWORD
#
# Optional generic proxy variables:
#   YOUTUBE_HTTP_PROXY
#   YOUTUBE_HTTPS_PROXY

def create_youtube_api():
    """
    Create YouTubeTranscriptApi with optional proxy.

    Priority:
    1. Webshare username + password
    2. Generic HTTP/HTTPS proxy
    3. Direct connection
    """

    webshare_user = os.environ.get(
        "WEBSHARE_PROXY_USERNAME",
        ""
    ).strip()

    webshare_pass = os.environ.get(
        "WEBSHARE_PROXY_PASSWORD",
        ""
    ).strip()

    http_proxy = os.environ.get(
        "YOUTUBE_HTTP_PROXY",
        ""
    ).strip()

    https_proxy = os.environ.get(
        "YOUTUBE_HTTPS_PROXY",
        ""
    ).strip()

    # =====================================================
    # 1. WEBSHARE PROXY
    # =====================================================

    if webshare_user and webshare_pass:

        if WebshareProxyConfig is None:

            raise RuntimeError(
                "WebshareProxyConfig is not available. "
                "Please update youtube-transcript-api."
            )

        print(
            "YouTube API: Webshare proxy ENABLED"
        )

        try:

            proxy_config = WebshareProxyConfig(
                proxy_username=webshare_user,
                proxy_password=webshare_pass
            )

            return YouTubeTranscriptApi(
                proxy_config=proxy_config
            )

        except Exception as e:

            raise RuntimeError(
                "Webshare proxy configuration failed: "
                + str(e)
            )

    # =====================================================
    # 2. GENERIC PROXY
    # =====================================================

    if http_proxy or https_proxy:

        if GenericProxyConfig is None:

            raise RuntimeError(
                "GenericProxyConfig is not available. "
                "Please update youtube-transcript-api."
            )

        # -------------------------------------------------
        # Validate proxy URLs
        # -------------------------------------------------

        def validate_proxy_url(proxy_url):

            if not proxy_url:
                return None

            # A proxy must contain a scheme.
            # Example:
            # http://user:password@host:port

            if not re.match(
                r"^[a-zA-Z][a-zA-Z0-9+.-]*://",
                proxy_url
            ):

                raise RuntimeError(
                    "Invalid proxy URL: "
                    + proxy_url
                    + ". Use complete format like "
                      "'http://username:password@host:port'."
                )

            return proxy_url

        http_proxy = validate_proxy_url(
            http_proxy
        )

        https_proxy = validate_proxy_url(
            https_proxy
        )

        print(
            "YouTube API: Generic proxy ENABLED"
        )

        print(
            "HTTP proxy:",
            http_proxy
        )

        print(
            "HTTPS proxy:",
            https_proxy
        )

        try:

            proxy_config = GenericProxyConfig(

                http_url=http_proxy,

                https_url=https_proxy

            )

            return YouTubeTranscriptApi(

                proxy_config=proxy_config

            )

        except Exception as e:

            raise RuntimeError(
                "Generic proxy configuration failed: "
                + str(e)
            )

    # =====================================================
    # 3. DIRECT CONNECTION
    # =====================================================

    print(
        "YouTube API: NO PROXY configured"
    )

    return YouTubeTranscriptApi()