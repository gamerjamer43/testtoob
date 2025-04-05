# Frontend
from tkinter import messagebox
import tkinter as tk

# Backend
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import datetime, pytz

# Initialize Flask and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    videos = db.relationship('Video', backref='author', lazy=True)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    subscribers = db.relationship('Subscription', backref='channel', foreign_keys='Subscription.channel_id', lazy=True)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(tz=pytz.utc))
    thumbnail = db.Column(db.String(20), nullable=False)
    video_file = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

    author = db.relationship('User', backref='comments')
    replies = db.relationship('CommentReply', backref='comment', cascade='all, delete-orphan')

class CommentReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)

    author = db.relationship('User', backref='replies')

# Admin Panel Class
class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Video Management")
        self.root.geometry("800x800")
        self.root.configure(bg="#f0f0f0")

        # Ew. Tkinter. I'll make it minimally disgusting for as short as possible
        title_label = tk.Label(root, text="Admin Video Management", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        left_frame = tk.Frame(root, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        video_frame = tk.Frame(left_frame, bg="#f0f0f0")
        video_frame.pack(pady=10)
        self.video_listbox = tk.Listbox(video_frame, width=40, height=10, font=("Arial", 12))
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        video_scrollbar = tk.Scrollbar(video_frame)
        video_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.video_listbox.config(yscrollcommand=video_scrollbar.set)
        video_scrollbar.config(command=self.video_listbox.yview)
        self.delete_video_button = tk.Button(left_frame, text="Delete Video", command=self.delete_video, font=("Arial", 12), bg="#ff6666", fg="white")
        self.delete_video_button.pack(pady=10)
        user_frame = tk.Frame(left_frame, bg="#f0f0f0")
        user_frame.pack(pady=10)
        self.user_listbox = tk.Listbox(user_frame, width=40, height=10, font=("Arial", 12))
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        user_scrollbar = tk.Scrollbar(user_frame)
        user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_listbox.config(yscrollcommand=user_scrollbar.set)
        user_scrollbar.config(command=self.user_listbox.yview)
        self.delete_user_button = tk.Button(left_frame, text="Delete User", command=self.delete_user, font=("Arial", 12), bg="#ff6666", fg="white")
        self.delete_user_button.pack(pady=10)
        self.user_info_button = tk.Button(left_frame, text="Show User Info", command=self.show_user_info, font=("Arial", 12), bg="#007BFF", fg="white")
        self.user_info_button.pack(pady=10)
        self.show_subscribers_button = tk.Button(left_frame, text="Show Subscribers", command=self.show_subscribers, font=("Arial", 12), bg="#007BFF", fg="white")
        self.show_subscribers_button.pack(pady=10)
        self.toggle_verified_button = tk.Button(left_frame, text="Toggle Verified Status", command=self.toggle_verified, font=("Arial", 12), bg="#ffa500", fg="white")
        self.toggle_verified_button.pack(pady=10)
        right_frame = tk.Frame(root, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        comment_frame = tk.Frame(right_frame, bg="#f0f0f0")
        comment_frame.pack(pady=10)
        self.comment_listbox = tk.Listbox(comment_frame, width=40, height=10, font=("Arial", 12))
        self.comment_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        comment_scrollbar = tk.Scrollbar(comment_frame)
        comment_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.comment_listbox.config(yscrollcommand=comment_scrollbar.set)
        comment_scrollbar.config(command=self.comment_listbox.yview)
        self.delete_comment_button = tk.Button(right_frame, text="Delete Comment", command=self.delete_comment, font=("Arial", 12), bg="#ff6666", fg="white")
        self.delete_comment_button.pack(pady=10)
        reply_frame = tk.Frame(right_frame, bg="#f0f0f0")
        reply_frame.pack(pady=10)
        self.reply_listbox = tk.Listbox(reply_frame, width=40, height=10, font=("Arial", 12))
        self.reply_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        reply_scrollbar = tk.Scrollbar(reply_frame)
        reply_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.reply_listbox.config(yscrollcommand=reply_scrollbar.set)
        reply_scrollbar.config(command=self.reply_listbox.yview)
        self.delete_reply_button = tk.Button(right_frame, text="Delete Reply", command=self.delete_reply, font=("Arial", 12), bg="#ff6666", fg="white")
        self.delete_reply_button.pack(pady=10)
        self.root.bind('<Control-r>', self.refresh)
        # The big fat block of UGH. it is finished.

        self.load_videos()
        self.load_users()
        self.load_comments()
        self.load_replies()
        self.start_auto_refresh()

    # Routes accessed in the big block of indecipherable ugh. Pick thru it if u want i did and i wont again. :(
    def load_videos(self):
        with app.app_context():
            self.video_listbox.delete(0, tk.END)
            videos = Video.query.all()
            for video in videos:
                self.video_listbox.insert(tk.END, f"{video.id}: {video.title}")

    def load_users(self):
        with app.app_context():
            self.user_listbox.delete(0, tk.END)
            users = User.query.all()
            for user in users:
                verified_status = "✅" if user.verified else "❌"
                self.user_listbox.insert(tk.END, f"{user.id}: {user.username} - {verified_status}")

    def load_comments(self):
        with app.app_context():
            self.comment_listbox.delete(0, tk.END)
            comments = Comment.query.all()
            for comment in comments:
                self.comment_listbox.insert(tk.END, f"{comment.id}: {comment.content[:30]}... (by {comment.author.username})")

    def load_replies(self):
        with app.app_context():
            self.reply_listbox.delete(0, tk.END)
            replies = CommentReply.query.all()
            for reply in replies:
                self.reply_listbox.insert(tk.END, f"{reply.id}: {reply.content[:30]}... (by {reply.author.username})")

    def delete_video(self):
        with app.app_context():
            selected_index = self.video_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Warning", "Please select a video to delete.")
                return
            
            video_id = self.video_listbox.get(selected_index).split(":")[0]
            video = Video.query.get(video_id)

            if video:
                video_file_path = os.path.join('C:/Users/fuzio/Downloads/testtoob/uploads', video.video_file)
                thumbpath = os.path.join('C:/Users/fuzio/Downloads/testtoob/uploads', video.thumbnail)

                if os.path.exists(video_file_path):
                    os.remove(video_file_path)
                if os.path.exists(thumbpath):
                    os.remove(thumbpath)
                db.session.delete(video)
                db.session.commit()
                messagebox.showinfo("Success", "Video deleted successfully.")
                self.load_videos()
            else:
                messagebox.showerror("Error", "Video not found.")

    def delete_user(self):
        with app.app_context():
            selected_index = self.user_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Warning", "Please select a user to delete.")
                return
            
            user_id = self.user_listbox.get(selected_index).split(":")[0]
            user = User.query.get(user_id)

            if not user:
                messagebox.showerror("Error", "User not found.")
                return
                
            videos = Video.query.filter_by(user_id=user.id).all()
            for video in videos:
                video_file_path = os.path.join('C:/Users/fuzio/Downloads/testtoob/uploads', video.video_file)
                thumbpath = os.path.join('C:/Users/fuzio/Downloads/testtoob/uploads', video.thumbnail)

                if os.path.exists(video_file_path):
                    os.remove(video_file_path)
                if os.path.exists(thumbpath):
                    os.remove(thumbpath)

            db.session.delete(user)
            db.session.commit()
            messagebox.showinfo("Success", "User deleted successfully.")
            self.load_users()

    def delete_comment(self):
        with app.app_context():
            selected_index = self.comment_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Warning", "Please select a comment to delete.")
                return
            
            comment_id = self.comment_listbox.get(selected_index).split(":")[0]
            comment = Comment.query.get(comment_id)

            if comment:
                db.session.delete(comment)
                db.session.commit()
                messagebox.showinfo("Success", "Comment deleted successfully.")
                self.load_comments()
            else:
                messagebox.showerror("Error", "Comment not found.")

    def delete_reply(self):
        with app.app_context():
            selected_index = self.reply_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Warning", "Please select a reply to delete.")
                return
            
            reply_id = self.reply_listbox.get(selected_index).split(":")[0]
            reply = CommentReply.query.get(reply_id)

            if not reply:
                messagebox.showerror("Error", "Reply not found.")
                return
            
            db.session.delete(reply)
            db.session.commit()
            messagebox.showinfo("Success", "Reply deleted successfully.")
            self.load_replies()
                

    def toggle_verified(self):
        with app.app_context():
            selected_index = self.user_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Warning", "Please select a user to toggle verification.")
                return
            
            user_id = self.user_listbox.get(selected_index).split(":")[0]
            user = User.query.get(user_id)

            if user:
                user.verified = not user.verified
                db.session.commit()
                messagebox.showinfo("Success", f"User {user.username} verification status updated to {user.verified}.")
                self.load_users()
            else:
                messagebox.showerror("Error", "User not found.")

    def show_user_info(self):
        with app.app_context():
            selected_index = self.user_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Warning", "Please select a user to view their information.")
                return
            
            user_id = self.user_listbox.get(selected_index).split(":")[0]
            user = User.query.get(user_id)

            if user:
                info = f"User ID: {user.id}\nUsername: {user.username}\nEmail: {user.email}\nVerified: {user.verified}"
                messagebox.showinfo("User Info", info)
            else:
                messagebox.showerror("Error", "User not found.")

    def show_subscribers(self):
        selected_index = self.user_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Please select a user to view their subscribers.")
            return
        
        user_id = self.user_listbox.get(selected_index).split(":")[0]
        
        with app.app_context():
            user = User.query.get(user_id)
            if not user: 
                messagebox.showerror("Error", "User not found.") 
                return
        
            subscribers = [User.query.get(sub.subscriber_id).username for sub in user.subscribers]
            if subscribers:
                subscribers_list = "\n".join(subscribers)
                messagebox.showinfo("Subscribers", f"Subscribers for {user.username}:\n{subscribers_list}")
            else:
                messagebox.showinfo("Subscribers", f"{user.username} has no subscribers.")
                

    def start_auto_refresh(self):
        self.load_videos()
        self.load_users()
        self.load_comments()
        self.load_replies()
        self.root.after(5000, self.start_auto_refresh)

    def refresh(self, event=None):
        self.load_videos()
        self.load_users()
        self.load_comments()
        self.load_replies()

if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    panel = AdminPanel(root)
    root.mainloop()