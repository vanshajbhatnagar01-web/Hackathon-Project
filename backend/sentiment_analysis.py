
import pandas as pd
import re
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "cleaned"
MODEL_DIR = BASE_DIR / "ml"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

reviews = pd.read_csv(
    OUTPUT_DIR / "cleaned_reviews.csv"
)

print("Customer reviews loaded successfully!")
print("Total reviews:", len(reviews))


def get_sentiment(rating):

    if rating <= 2:
        return "Negative"

    elif rating == 3:
        return "Neutral"

    else:
        return "Positive"


reviews["sentiment"] = reviews["rating"].apply(get_sentiment)

print("\nSentiment distribution:")
print(reviews["sentiment"].value_counts())


def clean_text(text):

    text = str(text).lower()

    text = re.sub(r"[^a-z\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


reviews["cleaned_text"] = reviews["review_text"].apply(clean_text)


X = reviews["cleaned_text"]
y = reviews["sentiment"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)



extra_reviews = [
  
    "The food was fresh and absolutely delicious",
    "Amazing coffee and excellent customer service",
    "I loved the pizza, it was perfectly cooked",
    "Very friendly staff and a wonderful experience",
    "The restaurant was clean and the food was great",
    "Excellent quality and worth every rupee",
    "The desserts were delicious and freshly prepared",
    "Fast service and tasty food, highly recommended",

    "The food was cold and completely tasteless",
    "Very poor service, the staff was rude",
    "I waited too long and the food was disappointing",
    "The coffee was burnt and tasted awful",
    "The fries were soggy and full of oil",
    "The restaurant was dirty and uncomfortable",
    "Terrible experience, I will never come back",
    "The order was incorrect and the food was stale",

    "The food was average, nothing special",
    "The coffee was okay, not too good or bad",
    "The service was normal and the prices were reasonable",
    "The restaurant was decent but could improve",
    "The food was acceptable but not impressive",
    "It was an ordinary dining experience",
    "The pizza was fine, but I expected more",
    "Everything was okay, nothing stood out",

    "The staff was extremely rude and unhelpful",
    "Worst coffee I have ever tasted",
    "The service was horrible and the food was cold",
    "Very disappointing experience at this cafe",
    "I hated the food and the service was terrible",
    "The food was stale and the staff ignored us",

    "The coffee was neither good nor bad",
    "The food was decent but quite ordinary",
    "The service was acceptable",
    "The restaurant was average overall",
    "The experience was fine but not memorable",
    "The food was okay and the service was normal"
]

extra_sentiments = [
    "Positive", "Positive", "Positive", "Positive",
    "Positive", "Positive", "Positive", "Positive",

    "Negative", "Negative", "Negative", "Negative",
    "Negative", "Negative", "Negative", "Negative",

    "Neutral", "Neutral", "Neutral", "Neutral",
    "Neutral", "Neutral", "Neutral", "Neutral",

    "Negative", "Negative", "Negative",
    "Negative", "Negative", "Negative",

    "Neutral", "Neutral", "Neutral",
    "Neutral", "Neutral", "Neutral"
]

# Add the new examples to the training data only
X_train = pd.concat([
    pd.Series(X_train).reset_index(drop=True),
    pd.Series(extra_reviews)
], ignore_index=True)

y_train = pd.concat([
    pd.Series(y_train).reset_index(drop=True),
    pd.Series(extra_sentiments)
], ignore_index=True)

print("\nExtra training reviews added:", len(extra_reviews))
print("Total training reviews now:", len(X_train))


print("\nTraining reviews:", len(X_train))
print("Testing reviews:", len(X_test))


model = Pipeline([
    ("tfidf", TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2
    )),

    ("classifier", LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    ))
])


print("\nTraining sentiment model...")

model.fit(X_train, y_train)

print("Model training completed!")


predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nModel Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


reviews["predicted_sentiment"] = model.predict(
    reviews["cleaned_text"]
)

probabilities = model.predict_proba(
    reviews["cleaned_text"]
)

reviews["confidence"] = probabilities.max(axis=1)

print("\nFinal sentiment results:")
print(reviews["predicted_sentiment"].value_counts())


joblib.dump(
    model,
    MODEL_DIR / "sentiment_model.joblib"
)

reviews.to_csv(
    OUTPUT_DIR / "reviews_with_sentiment.csv",
    index=False
)

print("\nModel saved successfully!")
print("Sentiment results saved successfully!")


test_reviews = [
    "The food was amazing and the staff was very friendly",
    "The coffee was average",
    "The food was cold and tasteless",
    "Worst service ever, I will never visit again",
    "The pizza was delicious and fresh",
    "The fries were cold and the service was terrible",
    "The restaurant was okay, nothing special"
]

print("\nTesting more customer reviews:")

for review in test_reviews:

    prediction = model.predict([review])[0]

    print("\nReview:", review)
    print("Predicted sentiment:", prediction)


print("\nSENTIMENT ANALYSIS COMPLETED!")
