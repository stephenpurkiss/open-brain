"""Embedding generation for Open Brain using gte-small ONNX model."""
import numpy as np

_tokenizer = None
_ort_session = None


def _load_model():
    """Lazy-load gte-small ONNX model on first use."""
    global _tokenizer, _ort_session
    if _tokenizer is not None:
        return
    from tokenizers import Tokenizer
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download

    model_path = hf_hub_download("Supabase/gte-small", "onnx/model.onnx")
    tokenizer_path = hf_hub_download("Supabase/gte-small", "tokenizer.json")
    _tokenizer = Tokenizer.from_file(tokenizer_path)
    _ort_session = ort.InferenceSession(model_path)


def generate_embedding(text):
    """Generate a 384-dim normalized embedding for text."""
    _load_model()
    encoding = _tokenizer.encode(text)
    input_ids = np.array([encoding.ids], dtype=np.int64)
    attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
    token_type_ids = np.zeros_like(input_ids)
    outputs = _ort_session.run(None, {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "token_type_ids": token_type_ids,
    })
    embedding = outputs[0][0].mean(axis=0)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding.tolist()
