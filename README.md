# TestToob

testtoob is a flask-based video sharing platform that lets users upload, view, and interact with videos. built using flask, flask-login for authentication, flask-sqlalchemy for database management, and flask-wtf for form handling. additional libraries such as pillow, cv2, bleach, and ffmpeg are used for file processing and security.

## features

- **user authentication:** registration, login, and logout functionality with password hashing via flask-bcrypt.
- **video upload and processing:** users can upload video files and thumbnails. videos are processed using ffmpeg to ensure proper encoding (and no viruses), and thumbnails are compressed using pillow.
- **video management:** videos can have different visibility settings (public, unlisted, private) and include details like title, description, tags, and date posted.
- **engagement:** users can like, dislike, and comment on videos. comments support replies and mentions that link to user channels.
- **subscriptions and notifications:** users can subscribe to channels and receive notifications when new videos are uploaded.
- **search and analytics:** search functionality for both videos and channels, with analytics for creators such as view counts and like counts.
- **error handling:** custom error pages for common http errors like 400, 403, 404, and file size limits.
- **security:** uses bleach to sanitize user inputs and ensure secure file uploads; sessions are configured with secure cookies.

## libraries used

- flask (the website stuff)
- flask-login (user account management)
- flask-sqlalchemy (ORM manager for sqlite3 and flask)
- flask-wtf (what the forms, form security/cors)
- flask-bcrypt (encryption)
- pillow (image handling)
- opencv (cv2 for video processing)
- bleach (for input sanitization)
- ffmpeg (for video conversion)
- sqlite (the database)

## file structure

- **app.py:** main flask application file containing route definitions, models, forms, and error handling.
- **templates/:** folder containing html templates for different pages (e.g. home, login, register, upload, video, channel, settings, error pages).
- **static/:** folder for static files like css, javascript, and images.
- **uploads/:** directory configured for storing uploaded video and thumbnail files.

## routes overview

- **home page (/):** displays videos based on different views (random, trending, subscribed, new).
- **user routes:** 
  - `/register` for user registration,
  - `/login` for user login,
  - `/logout` for logging out.
- **upload route (/upload):** handles video uploads and file processing.
- **video route (/video/<video_id>):** displays individual video pages with comments, likes, and related recommendations.
- **channel route (/channel/<user_id>):** displays user channels with their uploaded videos and channel info.
- **search route (/search):** allows searching for videos and channels.
- **analytics route (/analytics):** provides creators with basic analytics on their videos.
- **settings route (/settings):** allows users to update profile settings including profile picture, channel banner, bio, and featured video.
- **interaction routes:** include like, dislike, subscription, and notification endpoints to handle user engagement with videos and comments.

## getting started

1. install required packages (flask, flask-login, flask-sqlalchemy, flask-wtf, flask-bcrypt, pillow, opencv-python, bleach, pytz, etc.).
2. configure your secret key and database uri in the app configuration.
3. run the app using `python app.py` (the app runs on port 5000 by default).
4. access the app in your browser at `http://localhost:5000`.

i am also attempting to host this full time at some point here, lost interest in this project in favor of Boron but i will return to work on this more at some point

## notes

- video uploads are limited to a maximum of 250mb.
- file uploads and session cookies are configured with security best practices.
- ensure that ffmpeg is installed and accessible on your system for video conversion.