import requests
import yt_dlp


class YoutubeScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        self.lang = "en"

    def scrape(self):
        """
        Extracts YouTube subtitles as a string.

        Args:
            url (str): The YouTube video URL.
            lang (str): The language code for subtitles (default: "en" for English).

        Returns:
            str: The subtitle text if available, otherwise an error message.
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "skip_download": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.link, download=False)
            # Get manual or auto subtitles
            subtitles = info.get("subtitles", {})
            automatic_captions = info.get("automatic_captions", {})

            # Choose manual subtitles first, otherwise fallback to auto captions
            subtitle_list = subtitles.get(self.lang, []) or automatic_captions.get(self.lang, [])

            if not subtitle_list:
                return "No subtitles available for the requested language."

            # Get the first subtitle URL (usually VTT format)
            subtitle_url = subtitle_list[0]["url"]

            # Download and return subtitle text
            response = requests.get(subtitle_url)
            response.raise_for_status()
            events = response.json().get("events")
            subtitle_text = ""
            for event in events:
                if "segs" in event:
                    for seg in event["segs"]:
                        subtitle_text += seg["utf8"]
            return subtitle_text, info.get("title", "")

        except Exception as e:
            print(f"Error fetching subtitles: {str(e)}")
            return ""
