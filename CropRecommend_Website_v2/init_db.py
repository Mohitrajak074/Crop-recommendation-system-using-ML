"""Initialize the CropRecommend SQLite database."""

from app import app, init_db


if __name__ == "__main__":
    init_db(app)
    print(f"Database initialized at {app.config['DATABASE']}")
