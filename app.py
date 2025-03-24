from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import yt_dlp
import os
from werkzeug.utils import secure_filename
from imageio_ffmpeg import get_ffmpeg_exe

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with a secure key

# Configuration
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Get FFmpeg path from imageio-ffmpeg
ffmpeg_location = get_ffmpeg_exe()

# YouTube download options
ydl_opts = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
    "noplaylist": True,
    "ffmpeg_location": ffmpeg_location,
}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            flash("Please enter a YouTube URL")
            return redirect(url_for("index"))

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = (
                    ydl.prepare_filename(info)
                    .replace(".webm", ".mp3")
                    .replace(".m4a", ".mp3")
                )
                final_filename = secure_filename(os.path.basename(filename))

            # Return the file as a download response
            return send_file(filename, as_attachment=True, download_name=final_filename)

        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for("index"))

    return render_template("index.html")


@app.teardown_request
def cleanup(exception=None):
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error cleaning up: {e}")


# HTML template with loader and button disabling
index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube to MP3 Downloader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            text-align: center;
        }
        input[type="text"] {
            width: 70%;
            padding: 8px;
            margin: 10px 0;
        }
        input[type="submit"] {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
        .flash {
            padding: 10px;
            margin: 10px 0;
            background-color: #f44336;
            color: white;
        }
        .loader {
            display: none;
            border: 8px solid #f3f3f3;
            border-top: 8px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube to MP3 Downloader</h1>
        <form id="downloadForm" method="post">
            <input type="text" name="url" placeholder="Enter YouTube URL" required>
            <br>
            <input type="submit" value="Download MP3">
        </form>
        <div id="loader" class="loader"></div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <script>
        document.getElementById('downloadForm').addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            // Show loader when form is submitted
            document.getElementById('loader').style.display = 'block';
            // Disable the submit button to prevent multiple submissions
            document.querySelector('input[type="submit"]').disabled = true;

            var formData = new FormData(this);
            
            fetch('/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.blob()) // Process the response as a blob
            .then(blob => {
                // Create a link to download the file
                var url = window.URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'download.mp3'; // Adjust this based on the filename you want
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                
                // Hide loader and enable the button after the download starts
                document.getElementById('loader').style.display = 'none';
                document.querySelector('input[type="submit"]').disabled = false;
            })
            .catch(error => {
                // Handle error
                alert('Error during download: ' + error);
                document.getElementById('loader').style.display = 'none';
                document.querySelector('input[type="submit"]').disabled = false;
            });
        });
    </script>
</body>
</html>
"""

# Create templates folder and write the HTML file
if not os.path.exists("templates"):
    os.makedirs("templates")
with open("templates/index.html", "w") as f:
    f.write(index_html)

if __name__ == "__main__":
    app.run(debug=True)
