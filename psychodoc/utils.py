try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
except ImportError:
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    torch = None
    print("Transformers/Torch not installed. Sentiment analysis will be simulated.")
import threading

_tokenizer = None
_model = None
_loading = False
_lock = threading.Lock()

def _load_model_sync():
    """Synchronously load the model"""
    global _tokenizer, _model
    if AutoTokenizer is None or torch is None:
        return
        
    print("Loading sentiment analysis model...")
    _tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
    _model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
    _model.eval()
    print("Model loaded successfully!")

def _load_model_background():
    """Load model in background thread"""
    global _loading
    if not _loading:
        _loading = True
        thread = threading.Thread(target=_load_model_sync, daemon=True)
        thread.start()

def _load_model():
    """Get model, loading if necessary"""
    global _tokenizer, _model, _loading
    with _lock:
        if _tokenizer is None or _model is None:
            if not _loading:
                _load_model_sync()  # Load immediately if not already loading
            else:
                # Wait for background load to complete
                while _tokenizer is None or _model is None:
                    import time
                    time.sleep(0.1)
    return _tokenizer, _model

def analyze_sentiment(text):
    """Analyze sentiment with lazy-loaded model"""
    tokenizer, model = _load_model()
    
    if tokenizer is None or model is None:
        # Fallback/Mock behavior if model not loaded
        return "Neutral"
        
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        scores = torch.softmax(outputs.logits, dim=1).squeeze().tolist()
    sentiment_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
    predicted = sentiment_map[scores.index(max(scores))]
    return predicted

# Pre-load model in background when module is imported (optional)
# Uncomment the line below if you want to start loading immediately
# _load_model_background()