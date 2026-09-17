

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
    webshare_user = os.environ.get("WEBSHARE_PROXY_USERNAME", "").strip()
    webshare_pass = os.environ.get("WEBSHARE_PROXY_PASSWORD", "").strip()

    if webshare_user and webshare_pass:
        if WebshareProxyConfig is None:
            raise RuntimeError(
                "Webshare proxy support is unavailable. "
                "Please update youtube-transcript-api."
            )

        print("YouTube API: Webshare proxy ENABLED")

        proxy_config = WebshareProxyConfig(
            proxy_username=webshare_user,
            proxy_password=webshare_pass,
            domain_name="p.webshare.io",
            proxy_port=80,
            retries_when_blocked=10
        )

        return YouTubeTranscriptApi(
            proxy_config=proxy_config
        )

    print("YouTube API: NO PROXY configured")
    return YouTubeTranscriptApi()