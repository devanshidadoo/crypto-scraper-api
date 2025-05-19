import os
import warnings

# Suppress TF low-level C++ logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Suppress Python warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Suppress TensorFlow Python logger warnings
import tensorflow as tf
tf.get_logger().setLevel("ERROR")  # ✅ this removes the line you're seeing

from transformers import pipeline


# initialize once
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)
CANDIDATES = ["Bitcoin", "Ethereum", "Tether", "Other"]

def summarize_text(text: str) -> str:
    # you can chunk if text > model max tokens
    out = summarizer(
        text, max_length=200, min_length=100, do_sample=False
    )
    return out[0]["summary_text"]

def classify_coin(text: str) -> str:
    out = classifier(text, candidate_labels=CANDIDATES)
    return out["labels"][0]  # highest‐scoring label

if __name__ == "__main__":
    sample = "Not only is Bitcoin (BTC) the first cryptocurrency, but it’s also the best known of the more than 19,000 cryptocurrencies in existence today. Financial media eagerly covers each new dramatic high and stomach-churning decline, making Bitcoin an inescapable part of the landscape.While the wild volatility might produce great headlines, it hardly makes Bitcoin the best choice for novice investors or people looking for a stable store of value. Understanding the ins and outs can be tricky—let’s take a closer look at how Bitcoin works."
    print("SUMMARY:", summarize_text(sample))
    print("COIN:", classify_coin(sample))

