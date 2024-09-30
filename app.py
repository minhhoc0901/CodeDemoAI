import pandas as pd
from flask import Flask, render_template, request
from googleapiclient.discovery import build
import os
from recommendation import recommend_videos, log_user_interaction

app = Flask(__name__)

# Thay YOUR_API_KEY bằng API Key của bạn
API_KEY = 'AIzaSyCVUxi32JXtp082wuZI0m3lvwf857g1_os'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Tạo thư mục user_data nếu chưa tồn tại
if not os.path.exists('user_data'):
    os.makedirs('user_data')

# File để lưu trữ dữ liệu hành vi người dùng
USER_DATA_FILE = 'user_data/user_interactions.csv'

# Trang chủ
@app.route('/', methods=['GET', 'POST'])
def index():
    videos = []
    recommended_videos = []
    selected_video_id = None  # ID video được chọn để xem

    if request.method == 'POST':
        query = request.form['query']
        videos = youtube_search(query)

        # Ghi lại hành vi xem của người dùng
        for video in videos:
            log_user_interaction(query, video['videoId'])

        # Đề xuất video liên quan
        if videos:
            recommended_ids = recommend_videos(videos[0]['videoId'])
            recommended_videos = [video for video in videos if video['videoId'] in recommended_ids]

    # Đề xuất video khi load trang
    else:
        # Đọc dữ liệu hành vi người dùng để lấy video đã xem
        if os.path.isfile(USER_DATA_FILE):
            interactions = pd.read_csv(USER_DATA_FILE)
            # Loại bỏ các giá trị NaN trong cột 'query'
            interactions = interactions[interactions['query'].notna()]
            if not interactions.empty:
                last_query = interactions['query'].mode()[0]  # Lấy truy vấn phổ biến nhất
                videos = youtube_search(last_query)

                # Ghi lại hành vi xem
                for video in videos:
                    log_user_interaction(last_query, video['videoId'])

                # Đề xuất video liên quan
                recommended_ids = recommend_videos(videos[0]['videoId'])
                recommended_videos = [video for video in videos if video['videoId'] in recommended_ids]

    # Lấy ID video được chọn từ tham số URL
    selected_video_id = request.args.get('video_id')

    return render_template('index.html', videos=videos, recommended_videos=recommended_videos, selected_video_id=selected_video_id)

# Hàm tìm kiếm video trên YouTube
def youtube_search(query, max_results=10):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    
    search_response = youtube.search().list(
        q=query,
        part='snippet',
        maxResults=max_results
    ).execute()

    videos = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            video_data = {
                'videoId': search_result['id']['videoId'],
                'title': search_result['snippet']['title'],
                'description': search_result['snippet']['description'],
                'thumbnail': search_result['snippet']['thumbnails']['high']['url']
            }
            videos.append(video_data)
    
    return videos

if __name__ == '__main__':
    app.run(debug=True)
