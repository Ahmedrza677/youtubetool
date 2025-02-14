import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyBMezgGyfMl18MlzDYT4xAoYnlRrxxLtn4"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
min_subs = st.number_input("Min Subscribers:", min_value=0, value=500)
max_subs = st.number_input("Max Subscribers:", min_value=1, value=1000)
min_likes = st.number_input("Min Likes:", min_value=0, value=100)
min_comments = st.number_input("Min Comments:", min_value=0, value=10)

# Broader keywords
keywords = ["Self Improvement", "Tech Reviews", "Stock Market", "Fitness", "AI Tools"]

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []
        
        for keyword in keywords:
            st.write(f"Searching for keyword: {keyword}")
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }
            
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()
            
            if "items" not in data:
                continue

            video_ids = [video["id"]["videoId"] for video in data["items"]]
            channel_ids = [video["snippet"]["channelId"] for video in data["items"]]
            
            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()
            
            channel_params = {"part": "statistics,snippet", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()
            
            for video, stat, channel in zip(data["items"], stats_data["items"], channel_data["items"]):
                title = video["snippet"]["title"]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                thumbnail_url = video["snippet"]["thumbnails"]["medium"]["url"]
                channel_name = channel["snippet"]["title"]
                views = int(stat["statistics"].get("viewCount", 0))
                likes = int(stat["statistics"].get("likeCount", 0))
                comments = int(stat["statistics"].get("commentCount", 0))
                subscribers = int(channel["statistics"].get("subscriberCount", 0))
                
                if min_subs <= subscribers <= max_subs and likes >= min_likes and comments >= min_comments:
                    engagement_rate = (views + likes + comments) / max(1, subscribers)
                    all_results.append({
                        "Title": title,
                        "Channel": channel_name,
                        "URL": video_url,
                        "Views": views,
                        "Likes": likes,
                        "Comments": comments,
                        "Subscribers": subscribers,
                        "Engagement Rate": engagement_rate,
                        "Thumbnail": thumbnail_url
                    })
        
        if all_results:
            df = pd.DataFrame(all_results).sort_values(by="Engagement Rate", ascending=False)
            st.success(f"Found {len(df)} videos!")
            for _, row in df.iterrows():
                st.image(row["Thumbnail"], caption=row["Title"], use_column_width=True)
                st.markdown(f"**[{row['Title']}]({row['URL']})**")
                st.write(f"**Channel:** {row['Channel']}")
                st.write(f"**Views:** {row['Views']} | **Likes:** {row['Likes']} | **Comments:** {row['Comments']}")
                st.write(f"**Subscribers:** {row['Subscribers']} | **Engagement Rate:** {row['Engagement Rate']:.2f}")
                st.write("---")
            
            # CSV Download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "youtube_results.csv", "text/csv")
        else:
            st.warning("No results match the filters!")
    except Exception as e:
        st.error(f"Error: {e}")
