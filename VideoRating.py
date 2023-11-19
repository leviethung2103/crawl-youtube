from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import MultiLabelBinarizer
import pandas as pd
import re
import sqlite3


class VideoRatingPredictor:
    def __init__(self, csv_path=None, database=None):
        self.csv_path = csv_path
        self.database = database
        self.descriptions = []
        self.ratings = []
        self.model = None
        self.data_frame = None
        self.descriptions = []
        self.ratings = []

    def get_data_from_db(self):

        conn = sqlite3.connect(self.database)
        query = "SELECT * FROM videos"
        data_frame = pd.read_sql_query(query, conn)
        conn.close()
        return data_frame

    def remove_stopwords(self, text):
        stopwords = [
            'là', 'của', 'lại', 'và', 'hay', 'vì', 'ở', 'có', 'trên', 'qua', 'nếu',
            'như', 'cho', 'để', 'thì', 'mà', 'với', 'còn', 'không', 'đã', 'rồi',
            'sau', 'từ', 'khi', 'cùng', 'này', 'này', 'theo', 'trước', 'sẽ', 'được',
            'nên', 'về', 'mới', 'đến', 'đang', 'cả', 'vậy', 'thế', 'những', 'ai',
            'các', 'cái', 'gì', 'ấy', 'nơi', 'ngoài', 'tất cả', 'ra', 'bằng', 'thành',
            'giữa', 'hơn', 'phải', 'thật', 'đúng', 'nhanh', 'nhấp', 'chậm'
        ]

        # Split the text into individual words
        words = text.split()

        # Remove the stop words from the list of words
        filtered_words = [word for word in words if word not in stopwords]

        # reconstruct the text by joining the filtered words
        filtered_texrt = ' '.join(filtered_words)

        return filtered_texrt

    def remove_patterns(self, string):
        # Updated regex pattern to match the additional pattern ":"
        pattern = r"(https?:\/\/)|[:,:]|\.\.\.|\.:|-"

        return re.sub(pattern, "", string)

    def preprocess(self, text):
        return self.remove_patterns(self.remove_stopwords(text))

    def process_row(self, row):
        desc = row['description'].lower()
        rating = int(row['rating'])
        if rating != 0:
            self.descriptions.append(self.preprocess(desc))
            self.ratings.append(rating)

    def train_model(self):
        # Features: Descriptions
        # Labels: Ratings
        if self.database is not None:
            self.data_frame = self.get_data_from_db()
        else:
            self.data_frame = pd.read_csv(self.csv_path)

        self.data_frame.apply(self.process_row, axis=1)

        # Create a pipeline with TF-IDF vectorizer and SVM classifier
        self.model = make_pipeline(TfidfVectorizer(), SVC(kernel='linear'))

        # Fit the model
        self.model.fit(self.descriptions, self.ratings)

    def predict_ratings(self, new_video_description):
        """ self.model.predict can receieve a list """
        if self.model is None:
            self.train_model()
        predicted_ratings = self.model.predict([
            self.preprocess(new_video_description)])
        return predicted_ratings[0]


if __name__ == "__main__":
    # Example: Predict ratings for new videos
    csv_path = "video_info.csv"
    database = "video_info.db"
    new_video_descriptions = [
        "israel",
        "chủ tịch nước",
        "quân sự",
        "thời sự toàn cảnh",
        "mưa",
        "công nghệ",
        "tiền",
        "nhà đất"
    ]

    predictor = VideoRatingPredictor(csv_path=None, database=database)
    predictor.train_model()
    predicted_ratings = predictor.predict_ratings(new_video_descriptions)

    print("List of Recommended Videos:")
    for video, rating in list(zip(new_video_descriptions, predicted_ratings)):
        print(f"Video: {video}, Predicted Rating: {rating}")
