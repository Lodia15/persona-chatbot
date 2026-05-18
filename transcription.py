from youtube_transcript_api import YouTubeTranscriptApi

video_id = "KByM64mjESc"

api = YouTubeTranscriptApi()

transcript = api.fetch(video_id, languages=["ka"])

full_text = ""

for item in transcript:
    full_text += item.text + "\n"

with open("documents/interview1.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

print("Transcript saved.")