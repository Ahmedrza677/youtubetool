import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyC6McCslf5ndJlf2TrDQMrp2z0QhYCxfno"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# API Quota Tracking
TOTAL_QUOTA = 10000  # Default daily quota limit
quota_used = 0

def update_quota(usage):
    global quota_used
    quota_used += usage

def get_quota_status():
    return max(0, TOTAL_QUOTA - quota_used)

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
min_subs = st.number_input("Min Subscribers:", min_value=0, value=500)
max_subs = st.number_input("Max Subscribers:", min_value=1, value=5000)

# Broader keywords
keywords = ["Self Improvement", "Tech Reviews", "Stock Market", "Fitness", "AI Tools"]

# Quota Status
quota_remaining = get_quota_status()
st.progress(quota_remaining / TOTAL_QUOTA)
st.write(f"API Quota Remaining: {quota_remaining} units")

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
            update_quota(100)  # Search API call costs 100 units
            
            if "items" not in data:
                continue

            video_ids = [video["id"].get("videoId", "") for video in data["items"] if "id" in video]
            channel_ids = [video["snippet"].get("channelId", "") for video in data["items"] if "snippet" in video]
            
            if not video_ids or not channel_ids:
                continue
            
            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()
            update_quota(1 * len(video_ids))  # Video stats call costs 1 unit per video
            
            channel_params = {"part": "statistics,snippet", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()
            update_quota(3 * len(channel_ids))  # Channel stats call costs 3 units per channel
            
            if "items" not in stats_data or "items" not in channel_data:
                continue
            
            for video, stat, channel in zip(data["items"], stats_data["items"], channel_data["items"]):
                title = video["snippet"].get("title", "N/A")
                video_url = f"https://www.youtube.com/watch?v={video['id'].get('videoId', '')}"
                thumbnail_url = video["snippet"].get("thumbnails", {}).get("medium", {}).get("url", "")
                channel_name = channel["snippet"].get("title", "N/A")
                subscribers = int(channel["statistics"].get("subscriberCount", 0))
                
                if min_subs <= subscribers <= max_subs:
                    all_results.append({
                        "Title": title,
                        "Channel": channel_name,
                        "URL": video_url,
                        "Subscribers": subscribers,
                        "Thumbnail": thumbnail_url
                    })
                else:
                    st.write(f"Skipping {title} - Subs: {subscribers}")
        
        if all_results:
            df = pd.DataFrame(all_results)
            st.success(f"Found {len(df)} videos!")
            for _, row in df.iterrows():
                st.image(row["Thumbnail"], caption=row["Title"], use_column_width=True)
                st.markdown(f"**[{row['Title']}]({row['URL']})**")
                st.write(f"**Channel:** {row["Channel"]}")
                st.write(f"**Subscribers:** {row["Subscribers"]}")
                st.write("---")
            
            # CSV Download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "youtube_results.csv", "text/csv")
        else:
            st.warning("No results match the filters!")
        
        # Update and display quota status
        quota_remaining = get_quota_status()
        st.progress(quota_remaining / TOTAL_QUOTA)
        st.write(f"API Quota Remaining: {quota_remaining} units")
        
    except Exception as e:
        st.error(f"Error: {e}")
