from flask import Flask, render_template, request, jsonify, send_file
import requests
import re
import os
from urllib.parse import urlparse
import time
import random

app = Flask(__name__)

# Buat folder downloads jika belum ada
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_download_url(tiktok_url):
    """Mendapatkan URL download video TikTok"""
    try:
        # Gunakan API TikWM yang lebih sederhana
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}"
        response = requests.get(api_url)
        if response.ok:
            data = response.json()
            if data.get('data', {}).get('play'):
                return data['data']['play']
        raise ValueError("Tidak dapat menemukan URL video")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

def download_video(url, filename):
    """Download video"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        return file_path
    except Exception as e:
        print(f"Error downloading: {str(e)}")
        raise

def validate_tiktok_url(url):
    """Validasi URL TikTok"""
    try:
        parsed = urlparse(url)
        valid_domains = ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com', 'www.tiktok.com']
        return any(domain in parsed.netloc for domain in valid_domains)
    except:
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """Handle download request"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL tidak diberikan'}), 400

        if not validate_tiktok_url(url):
            return jsonify({'error': 'URL TikTok tidak valid'}), 400

        filename = f"tiktok_{int(time.time())}_{random.randint(1000, 9999)}.mp4"
        
        # Dapatkan URL video
        video_url = get_download_url(url)
        if not video_url:
            return jsonify({'error': 'Tidak dapat mengekstrak URL video'}), 500

        # Download video
        file_path = download_video(video_url, filename)
        
        return jsonify({
            'success': True,
            'message': 'Video downloaded successfully',
            'download_path': f'/get-video/{filename}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-video/<filename>')
def get_video(filename):
    """Serve downloaded video"""
    try:
        return send_file(os.path.join(DOWNLOAD_FOLDER, filename),
                        mimetype='video/mp4',
                        as_attachment=True,
                        download_name=filename)
    except Exception as e:
        return jsonify({'error': 'File tidak ditemukan'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)