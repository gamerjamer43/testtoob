# Flask imports
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, make_response, jsonify, abort

# Login authentication
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt

# DB management
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc

# Forms and file upload
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image
from enum import Enum
from mimetypes import MimeTypes
import bleach, cv2, datetime, os, pytz, re, subprocess

# Key holder and warning suppression (SAWarning)
from keyholder import key
# import warnings (to add)

# Flask initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'C:/Users/fuzio/Downloads/testtoob/testtoob/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 250 * 1024 * 1024  # 250MB
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# Database initialization
db = SQLAlchemy(app)

# Login/password manager initialization
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Models ---
# Video models
class VideoVisibility(Enum):
    PUBLIC = "Public"
    UNLISTED = "Unlisted"
    PRIVATE = "Private"

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(tz=pytz.utc))
    thumbnail = db.Column(db.String(20), nullable=False)
    video_file = db.Column(db.String(20), nullable=False)
    views = db.Column(db.Integer, default=0)
    likes = db.relationship('Like', backref='video', lazy=True)
    comments = db.relationship('Comment', backref='video', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.Column(db.Text)
    visibility = db.Column(db.Enum(VideoVisibility), default=VideoVisibility.PUBLIC)
    author = db.relationship('User', backref='uploaded_videos', foreign_keys=[user_id])

    def like_counter(self):
        return Like.query.filter_by(video_id=self.id, reaction_type='like').count()
    
    def dislike_counter(self):
        return Like.query.filter_by(video_id=self.id, reaction_type='dislike').count()
    
class VideoView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    bio = db.Column(db.String(500), nullable=True, default="")
    profile_picture = db.Column(db.String(20), nullable=False, default='default_profile.jpg')
    channel_banner = db.Column(db.String(20), nullable=False, default='default_banner.jpg')
    verified = db.Column(db.Boolean, nullable=False, default=False)

    videos = db.relationship('Video', backref='uploaded_author', foreign_keys=[Video.user_id])
    featured_video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=True)
    featured_video = db.relationship('Video', backref='featured_users', foreign_keys=[featured_video_id])
    
    subscriptions = db.relationship('Subscription', 
                                     backref='subscriber', 
                                     foreign_keys='Subscription.subscriber_id', 
                                     lazy=True)

    def is_subscribed(self, channel):
        return Subscription.query.filter_by(subscriber_id=self.id, channel_id=channel.id).first() is not None
    
    def subscription_count(self):
        return Subscription.query.filter_by(channel_id=self.id).count()

# Interaction (like, dislike, comment, sub, notif) models
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reaction_type = db.Column(db.Enum('like', 'dislike'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notifications_enabled = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(tz=pytz.utc))
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

    user = db.relationship('User', backref='notifications')
    video = db.relationship('Video', backref='notifications')

# Comment related interaction models
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    replies = db.relationship('CommentReply', backref='parent', lazy=True)
    likes = db.relationship('CommentLike', backref='comment', lazy=True)

    author = db.relationship('User', backref='comments')
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    replies = db.relationship('CommentReply', backref='comment', cascade='all, delete-orphan')

    def like_count(self):
        return CommentLike.query.filter_by(comment_id=self.id, is_like=True).count()
    
    def dislike_count(self):
        return CommentLike.query.filter_by(comment_id=self.id, is_like=False).count()

class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_like = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    reply_id = db.Column(db.Integer, db.ForeignKey('comment_reply.id'), nullable=True)

class CommentReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)

    author = db.relationship('User', backref='replies')
    likes = db.relationship('CommentLike', backref='reply', lazy=True, primaryjoin='CommentReply.id == CommentLike.reply_id')

# --- Forms ---
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class VideoForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    thumbnail = FileField('Thumbnail', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Only .png and .jpg are allowed for thumbnails!')])
    video_file = FileField('Video File', validators=[DataRequired(), FileAllowed(['mov', 'mp4'], 'Only .mov and .mp4 are allowed for videos!')])
    tags = StringField('Tags (comma-separated)', render_kw={'placeholder': 'Enter tags separated by commas', 'oninput': 'validateTags();'}, validators=[Optional()])
    submit = SubmitField('Upload')

class SettingsForm(FlaskForm):
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only!')])
    channel_banner = FileField('Channel Banner', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Only .png and .jpg are allowed for banners!')])
    bio = TextAreaField('Bio', validators=[Length(max=200)], render_kw={"rows": 3})
    featured_video = SelectField('Featured Video', choices=[], coerce=int)
    submit = SubmitField('Update Settings')

class EditForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    thumbnail = FileField('Thumbnail', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')])
    tags = StringField('Tags (comma-separated)', render_kw={'placeholder': 'Enter tags separated by commas', 'oninput': 'validateTags();'}, validators=[Optional()])
    visibility = SelectField('Visibility', choices=[(v.name, v.value) for v in VideoVisibility], default=VideoVisibility.PUBLIC.name)
    submit = SubmitField('Update Video')

# --- Routes ---
# Home page
@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    view_type = request.args.get('view', 'random')
    videos_query = Video.query.filter(Video.visibility == VideoVisibility.PUBLIC)
    average_views = Video.query.with_entities(func.avg(Video.views)).scalar()

    if view_type == 'trending':
        trending_videos_query = (
            videos_query
            .outerjoin(Like)
            .filter(Video.views > average_views if average_views is not None else Video.views > 0)
            .group_by(Video.id)
            .order_by(func.count(Like.id).desc())
        )
        videos = trending_videos_query.paginate(page=page, per_page=16)

    elif view_type == 'random':
        videos = videos_query.order_by(func.random()).paginate(page=page, per_page=16)

    elif view_type == 'subscribed':
        subscribed_channel_ids = [sub.channel_id for sub in current_user.subscriptions]
        subscribed_videos_query = videos_query.filter(Video.user_id.in_(subscribed_channel_ids)).order_by(func.random())
        videos = subscribed_videos_query.paginate(page=page, per_page=16)

    elif view_type == 'new':
        videos = videos_query.order_by(desc(Video.date_posted)).paginate(page=page, per_page=16)

    else:
        videos = videos_query.order_by(func.random()).paginate(page=page, per_page=16)

    return render_template('home.html', videos=videos, view_type=view_type)

# User management (login, logout, register)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(bleach.clean(form.password.data)).decode('utf-8')
        user = User(username=bleach.clean(form.username.data.lower()), email=bleach.clean(form.email.data.lower()), password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
async def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=bleach.clean(form.email.data.lower())).first()
        if user and bcrypt.check_password_hash(user.password, bleach.clean(form.password.data)):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# Send from directory
@app.route('/uploads/<path:filename>')
async def uploaded_file(filename):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    video = Video.query.filter_by(video_file=filename).first()

    if video is None or (video.visibility != VideoVisibility.PUBLIC and current_user.id != video.user_id):
        abort(404 if video is None else 403)
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Upload route
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = VideoForm()
    if form.validate_on_submit():
        video_file = form.video_file.data
        tags = [tag.strip() for tag in bleach.clean(form.tags.data).split(',')] if form.tags.data else []
        tags = ','.join(tags) if len(tags) <= 5 and len(tags) != 0 else ""
        
        # Save the original video file
        video_filename = secure_filename(datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(current_user.id) + "_" + video_file.filename)
        temp_video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        video_file.save(temp_video_path)

        mime = MimeTypes()
        mime_type, _ = mime.guess_type(temp_video_path)
        if mime_type and mime_type.startswith('video'):
            # Create a distinct output filename and path for the converted file
            base_filename = os.path.splitext(video_file.filename)[0]
            output_filename = base_filename + '_converted.mp4'
            output_filename = secure_filename(datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(current_user.id) + "_" + output_filename)
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            # Run ffmpeg conversion with separate input and output paths
            subprocess.run(
                ['ffmpeg', '-i', temp_video_path, '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                 '-loglevel', 'quiet', '-c:a', 'aac', '-b:a', '192k', '-y', output_path],
                check=True
            )
            
            # Remove the original file and update paths
            os.remove(temp_video_path)
            video_filename = output_filename
            temp_video_path = output_path
        elif not mime_type or not mime_type.startswith('video'):
            os.remove(temp_video_path)
            abort(403)

        try:
            cvopen = cv2.VideoCapture(temp_video_path)
            # Note: CAP_PROP_POS_MSEC may not be the best property for duration.
            # You might consider CAP_PROP_FRAME_COUNT and CAP_PROP_FPS for a more accurate duration.
            video_duration = cvopen.get(cv2.CAP_PROP_POS_MSEC)
            
            if video_duration > 3600:
                os.remove(temp_video_path)
                flash('The video is too long! Maximum allowed length is 10 minutes.', 'danger')
                return redirect(url_for('upload'))

        except Exception as e:
            os.remove(temp_video_path)
            flash('There was an issue with the video file. Please try again.', 'danger')
            return redirect(url_for('upload'))

        # Process thumbnail
        thumbnail_file = form.thumbnail.data
        thumbnail_filename = secure_filename(datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(current_user.id) + "_" + thumbnail_file.filename)
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
        thumbnail_file.save(thumbnail_path)

        try:
            with Image.open(thumbnail_path) as img:
                img.save(thumbnail_path, quality=50)
        except Exception as e:
            app.logger.debug(f"Could not compress thumbnail {thumbnail_filename}: {e}")

        video = Video(
            title=bleach.clean(form.title.data),
            description=bleach.clean(form.description.data),
            thumbnail=thumbnail_filename,
            video_file=video_filename,
            user_id=current_user.id,
            date_posted=datetime.datetime.now(tz=pytz.utc),
            tags=tags
        )
        db.session.add(video)
        subscribers = Subscription.query.filter_by(channel_id=current_user.id, notifications_enabled=True).all()

        for subscription in subscribers:
            notification = Notification(
                content=f"{video.author.username} uploaded a new video: {video.title}",
                user_id=subscription.subscriber_id,
                video_id=video.id
            )
            db.session.add(notification)

        db.session.commit()
        flash('Video uploaded successfully!', 'success')
        return redirect(url_for('video', video_id=video.id))
    return render_template('upload.html', form=form)


# Video player route (also handles comments)
@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def video(video_id):
    video = Video.query.get_or_404(video_id)
    recommended_videos = (
        db.session.query(Video)
        .filter(Video.id != video_id, Video.visibility == VideoVisibility.PUBLIC)
        .order_by(func.random())
        .limit(8)
        .all()
    )

    if current_user.is_authenticated:
        if video.visibility == VideoVisibility.PRIVATE and current_user.id != video.author.id:
            return render_template("errors/404.html")

        view_exists = VideoView.query.filter_by(user_id=current_user.id, video_id=video.id).first()
        if not view_exists:
            video.views += 1
            new_view = VideoView(user_id=current_user.id, video_id=video.id)
            db.session.add(new_view)
            db.session.commit()
        
        notif_exists = Notification.query.filter_by(user_id=current_user.id, video_id=video_id).all()
        for notification in notif_exists:
            notification.is_read = True
            db.session.commit()

    else:
        if video.visibility == VideoVisibility.PRIVATE:
            return render_template("errors/403.html")

        viewed_videos = request.cookies.get('viewed_videos')
        if viewed_videos:
            viewed_videos = set(map(int, viewed_videos.split(',')))
        else:
            viewed_videos = set()

        if video.id not in viewed_videos:
            video.views += 1
            viewed_videos.add(video.id)
            db.session.commit()

            response = make_response(render_template('video.html', video=video))
            response.set_cookie('viewed_videos', ','.join(map(str, viewed_videos)), max_age=60*60*24*5)
            response.data = render_template('video.html', video=video, recommended_videos=recommended_videos, tags=[tag.strip() for tag in video.tags.split(',')])
            return response

    comments = Comment.query.filter_by(video_id=video.id).all()
    
    user_like = user_dislike = user_sub = user_notifs = None
    if current_user.is_authenticated:
        user_like = Like.query.filter_by(user_id=current_user.id, video_id=video.id, reaction_type='like').first() is not None
        user_dislike = Like.query.filter_by(user_id=current_user.id, video_id=video.id, reaction_type='dislike').first() is not None
        user_sub = Subscription.query.filter_by(subscriber_id=current_user.id, channel_id=video.author.id).first() is not None
        user_notifs = Subscription.query.filter_by(subscriber_id=current_user.id, channel_id=video.author.id, notifications_enabled=True).first() is not None

    if request.method == 'POST' and current_user.is_authenticated:
        comment_content = bleach.clean(request.form['comment'])
        mentions = re.findall(r'@(\w+)', comment_content)
        if mentions != []:
            for mention in mentions:
                user = User.query.filter_by(username=mention).first()
                if user:
                    comment_content = comment_content.replace(f'@{mention}', f'<a href="{url_for("channel", user_id=user.id)}">@{mention}</a>')

            
        comment = Comment(content=comment_content, user_id=current_user.id, video_id=video.id)
        db.session.add(comment)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'comment': {
                    'author_id': comment.author.id,
                    'author_username': comment.author.username,
                    'content': comment.content,
                    'id': comment.id
                }
            })

        return redirect(url_for('video', video_id=video.id))

    return render_template('video.html', video=video, comments=comments, user_like=user_like, user_dislike=user_dislike, user_sub=user_sub, user_notifs=user_notifs, recommended_videos=recommended_videos)

@app.route('/analytics')
@login_required
def analytics():
    videos = Video.query.filter_by(user_id=current_user.id).all()
    top_videos = sorted(videos, key=lambda x: x.views, reverse=True)
    top_10_videos = top_videos[:10] if len(top_videos) > 10 else top_videos
    video_likes = [video.like_counter() for video in videos]
    return render_template('analytics.html', videos=videos, video_likes=video_likes, top_videos=top_10_videos)

# Edit route
@app.route('/edit_video/<int:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    video = Video.query.get_or_404(video_id)

    if video.user_id != current_user.id:
        return {'message': 'You do not have permission to edit this video.'}, 403

    form = EditForm(obj=video)

    if form.validate_on_submit():
        video.title = bleach.clean(form.title.data)
        video.description = bleach.clean(form.description.data)
        video.tags = bleach.clean(form.tags.data) if len([tag.strip() for tag in form.tags.data.split(',')]) <= 5 else video.tags
        video.visibility = bleach.clean(form.visibility.data)

        if form.thumbnail.data:
            if video.thumbnail:
                old_thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], video.thumbnail)
                if os.path.exists(old_thumbnail_path):
                    os.remove(old_thumbnail_path)
            
            thumbnail = form.thumbnail.data
            thumbnail_filename = secure_filename(datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(current_user.id) + "_" + thumbnail.filename)
            thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename))
            video.thumbnail = thumbnail_filename

        db.session.commit()

        return redirect(url_for('channel', user_id=video.author.id))

    return render_template('edit.html', form=form, video=video)

# Video and comment/reply deletion routes
@app.route('/delete_video/<int:video_id>', methods=['DELETE'])
@login_required
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)

    if video.user_id != current_user.id:
        return {'message': 'You do not have permission to delete this video.'}, 403

    video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], video.video_file)
    thumbnail_file_path = os.path.join(app.config['UPLOAD_FOLDER'], video.thumbnail)

    try:
        if os.path.exists(video_file_path):
            os.remove(video_file_path)
        if os.path.exists(thumbnail_file_path):
            os.remove(thumbnail_file_path)

        Comment.query.filter_by(video_id=video.id).delete()
        Notification.query.filter_by(video_id=video.id).delete()
        db.session.delete(video)
        db.session.commit()

        return {'message': 'Video deleted successfully.', 'success': True}
    except Exception as e:
        return {'message': f'An error occurred while deleting the video:', 'success': False}, 500
    
@app.route('/delete_comment/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        abort(404, description="Comment not found")
    
    if comment.user_id != current_user.id:
        abort(403, description="You do not have permission to delete this comment")

    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": "Comment deleted successfully"}), 200

@app.route('/delete_reply/<int:reply_id>', methods=['DELETE'])
@login_required
def delete_reply(reply_id):
    comment = CommentReply.query.get(reply_id)
    if comment is None:
        abort(404, description="Comment not found")
    
    if comment.user_id != current_user.id:
        abort(403, description="You do not have permission to delete this comment")

    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": "Comment deleted successfully"}), 200

# Search route
@app.route('/search')
def search():
    query = request.args.get('query')
    page = request.args.get('page', 1, type=int)
    search_type = request.args.get('search_type', 'videos')

    matching_channels = []
    videos = []

    if query:
        matching_channels = User.query.filter(User.username.ilike(f'%{query}%')).limit(4).all()
        
        if search_type == 'channels':
            matching_channels = User.query.filter(User.username.ilike(f'%{query}%')).paginate(page=page, per_page=16)
        
        elif search_type == 'videos':
            query_lower = query.lower()
            tag_filter = f'%{query}%'

            videos = Video.query.filter(
                Video.visibility == VideoVisibility.PUBLIC,
                (Video.title.ilike(f'%{query_lower}%')) | 
                (Video.tags.ilike(tag_filter))
            ).paginate(page=page, per_page=16)

    else:
        videos = Video.query.paginate(page=page, per_page=16)

    return render_template('search.html', videos=videos, matching_channels=matching_channels, query=query, search_type=search_type)

# Channel page route
@app.route('/channel/<int:user_id>')
def channel(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'newest')
    is_owner = current_user.is_authenticated and current_user.id == user_id
    if current_user.is_authenticated:
        notifs = Subscription.query.filter_by(
            subscriber_id=current_user.id,
            channel_id=user_id,
            notifications_enabled=True
        ).count() > 0
    else:
        notifs = False

    if is_owner:
        videos_query = Video.query.filter_by(user_id=user_id)
    else:
        videos_query = Video.query.filter_by(user_id=user_id, visibility=VideoVisibility.PUBLIC)

    if sort_by == 'popular':
        videos = videos_query.order_by(desc(Video.views)).paginate(page=page, per_page=8)
    elif sort_by == 'oldest':
        videos = videos_query.order_by(Video.date_posted).paginate(page=page, per_page=8)
    else:
        videos = videos_query.order_by(desc(Video.date_posted)).paginate(page=page, per_page=8)

    return render_template('channel.html', user=user, notifs=notifs, videos=videos, view_type=sort_by)

# Settings route
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()

    user_videos = [(video.id, video.title) for video in current_user.videos]
    form.featured_video.choices = [(0, 'No Featured Video')] + user_videos

    if form.validate_on_submit():
        if form.profile_picture.data:
            profile_picture_filename = secure_filename(datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(current_user.id) + "_" + form.profile_picture.data.filename)
            if profile_picture_filename.lower().endswith(('.png', '.jpg', '.gif')):
                form.profile_picture.data.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_picture_filename))
                current_user.profile_picture = profile_picture_filename
            else:
                flash('Invalid profile picture file type. Only .png, .jpg, and .gif are allowed.', 'danger')
                return redirect(url_for('settings'))

        if form.channel_banner.data:
            channel_banner_filename = secure_filename(datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(current_user.id) + "_" + form.channel_banner.data.filename)
            if channel_banner_filename.lower().endswith(('.png', '.jpg')):
                form.channel_banner.data.save(os.path.join(app.config['UPLOAD_FOLDER'], channel_banner_filename))
                current_user.channel_banner = channel_banner_filename
            else:
                flash('Invalid banner file type. Only .png and .jpg are allowed.', 'danger')
                return redirect(url_for('settings'))

        if form.bio.data.strip() != "":
            current_user.bio = bleach.clean(form.bio.data)

        if form.featured_video.data != 0:
            current_user.featured_video_id = form.featured_video.data
        else:
            current_user.featured_video_id = None

        db.session.commit()
        flash('Your settings have been updated!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', form=form)

# Like, Dislike and Subscription routes
@app.route('/like/<int:video_id>', methods=['POST'])
@login_required
def like_video(video_id):
    existing_reaction = Like.query.filter_by(user_id=current_user.id, video_id=video_id).first()

    if existing_reaction:
        if existing_reaction.reaction_type == 'like':
            db.session.delete(existing_reaction)
            is_liked = False
        else:
            db.session.delete(existing_reaction)
            new_like = Like(user_id=current_user.id, video_id=video_id, reaction_type='like')
            db.session.add(new_like)
            is_liked = True
    else:
        like = Like(user_id=current_user.id, video_id=video_id, reaction_type='like')
        db.session.add(like)
        is_liked = True

    db.session.commit()

    like_count = Video.query.get(video_id).like_counter()
    dislike_count = Video.query.get(video_id).dislike_counter()
    
    return jsonify({'isLiked': is_liked, 'likeCount': like_count, 'dislikeCount': dislike_count})


@app.route('/dislike/<int:video_id>', methods=['POST'])
@login_required
def dislike_video(video_id):
    existing_reaction = Like.query.filter_by(user_id=current_user.id, video_id=video_id).first()

    if existing_reaction:
        if existing_reaction.reaction_type == 'dislike':
            db.session.delete(existing_reaction)
            is_disliked = False
        else:
            db.session.delete(existing_reaction)
            new_dislike = Like(user_id=current_user.id, video_id=video_id, reaction_type='dislike')
            db.session.add(new_dislike)
            is_disliked = True
    else:
        dislike = Like(user_id=current_user.id, video_id=video_id, reaction_type='dislike')
        db.session.add(dislike)
        is_disliked = True

    db.session.commit()

    like_count = Video.query.get(video_id).like_counter()
    dislike_count = Video.query.get(video_id).dislike_counter()
    
    return jsonify({'isDisliked': is_disliked, 'likeCount': like_count, 'dislikeCount': dislike_count})

@app.route('/subscribe/<int:channel_id>', methods=['GET', 'POST'])
@login_required
def subscribe(channel_id):
    subscription = Subscription.query.filter_by(subscriber_id=current_user.id, channel_id=channel_id).first()
    if subscription:
        db.session.delete(subscription)
        is_subscribed = False
    else:
        subscription = Subscription(subscriber_id=current_user.id, channel_id=channel_id)
        db.session.add(subscription)
        is_subscribed = True
    db.session.commit()

    subscription_count = User.query.get(channel_id).subscription_count()
    return jsonify({'isSubscribed': is_subscribed, 'subscriptionCount': subscription_count})

# Notification routes
@app.route('/toggle_notifications/<int:channel_id>', methods=['POST'])
@login_required
def toggle_notifications(channel_id):
    subscription = Subscription.query.filter_by(subscriber_id=current_user.id, channel_id=channel_id).first()
    if subscription:
        subscription.notifications_enabled = not subscription.notifications_enabled
        db.session.commit()
        return jsonify(success=True, notifications_enabled=subscription.notifications_enabled)
    return jsonify(success=False, error='Subscription not found.')

@app.route('/delete_notification/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.filter_by(user_id=current_user.id, id=notification_id).first()
    if notification:
        db.session.delete(notification)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, error='Notification not found.')

@app.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date_posted.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    notifications_html = render_template('notifications.html', notifications=user_notifications)
    
    return jsonify({
        'html': notifications_html,
        'count': unread_count
    })

# Comment reply, like and dislike routes
@app.route('/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def reply_to_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    reply_content = bleach.clean(request.form['reply'])
    mentions = re.findall(r'@(\w+)', reply_content)
    if mentions != []:
        for mention in mentions:
            user = User.query.filter_by(username=mention).first()
            if user:
                reply_content = reply_content.replace(f'@{mention}', f'<a href="{url_for("channel", user_id=user.id)}">@{mention}</a>')
    
    users_to_notify = User.query.filter_by(id=comment.user_id).all()
    for user in users_to_notify:
        notification = Notification(
            content=f"{current_user.username} replied to your comment",
            user_id=user.id,
            video_id=comment.video_id
        )
    db.session.add(notification)
    
    if reply_content.strip("").strip("\n") != "":
        reply = CommentReply(content=reply_content, user_id=current_user.id, comment_id=comment.id)
        db.session.add(reply)
        db.session.commit()
    return redirect(url_for('video', video_id=comment.video_id))

@app.route('/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    existing_like = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = CommentLike(is_like=True, user_id=current_user.id, comment_id=comment_id)
        db.session.add(new_like)
    db.session.commit()
    return redirect(url_for('video', video_id=Comment.query.get(comment_id).video_id))

@app.route('/comment/<int:comment_id>/dislike', methods=['POST'])
@login_required
def dislike_comment(comment_id):
    existing_dislike = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment_id, is_like=False).first()
    if existing_dislike:
        db.session.delete(existing_dislike)
    else:
        new_dislike = CommentLike(is_like=False, user_id=current_user.id, comment_id=comment_id)
        db.session.add(new_dislike)
    db.session.commit()
    return redirect(url_for('video', video_id=Comment.query.get(comment_id).video_id))

# --- Error handling ---
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return render_template('errors/413.html'), 413

@app.errorhandler(400)
def page_not_found(e):
    return render_template('errors/400.html'), 400

@app.errorhandler(403)
def page_not_found(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

# --- Main ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)