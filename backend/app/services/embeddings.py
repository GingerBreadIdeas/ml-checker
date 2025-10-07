import os
import torch
import numpy as np
from sklearn.manifold import TSNE
from typing import List, Tuple
import logging

# Set this environment variable to avoid parallelism-related warnings and errors
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Setup logging
logger = logging.getLogger(__name__)

# Import transformers after setting the environment variable
AutoTokenizer = None
AutoModel = None
TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModel

    TRANSFORMERS_AVAILABLE = True
    logger.info("Successfully imported transformers")
except Exception as e:
    logger.warning(
        f"Transformers not available: {str(e)}. Embedding functionality will be disabled."
    )

# Load model and tokenizer once at module level for better performance
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_TOKENIZER = None
_MODEL = None

if TRANSFORMERS_AVAILABLE:
    try:
        logger.info(f"Pre-loading tokenizer and model: {_MODEL_NAME}")
        _TOKENIZER = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _MODEL = AutoModel.from_pretrained(_MODEL_NAME)
        # Use CPU by default
        _MODEL = _MODEL.to("cpu")
        logger.info("Successfully pre-loaded tokenizer and model")
    except Exception as e:
        logger.warning(
            f"Failed to pre-load model: {str(e)}. Embeddings will load on-demand."
        )
        _TOKENIZER = None
        _MODEL = None


def create_embeddings(
    texts: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> np.ndarray:
    """
    Create embeddings for a list of texts using a pretrained transformer model.

    Args:
        texts: List of strings to embed
        model_name: HuggingFace model identifier

    Returns:
        Array of embeddings with shape (len(texts), embedding_dim)
    """
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    # Tokenize texts and create embeddings in batches
    embeddings = []
    batch_size = 32

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]

        # Tokenize batch
        encoded_inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(device)

        # Compute token embeddings
        with torch.no_grad():
            model_output = model(**encoded_inputs)

        # Use mean pooling to get sentence embeddings
        attention_mask = encoded_inputs["attention_mask"]
        token_embeddings = model_output.last_hidden_state

        # Mask the padding tokens and compute mean of token embeddings
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        sentence_embeddings = torch.sum(
            token_embeddings * input_mask_expanded, 1
        ) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

        # Add batch embeddings to results
        embeddings.append(sentence_embeddings.cpu().numpy())

    # Concatenate all batch embeddings
    embeddings = np.vstack(embeddings)
    return embeddings


def reduce_to_2d(embeddings: np.ndarray, random_state: int = 42) -> np.ndarray:
    """
    Reduce dimensionality of embeddings to 2D using t-SNE.

    Args:
        embeddings: Array of embeddings with shape (n_samples, embedding_dim)
        random_state: Random seed for reproducibility

    Returns:
        Array of 2D points with shape (n_samples, 2)
    """
    tsne = TSNE(
        n_components=2,
        random_state=random_state,
        perplexity=min(30, max(5, len(embeddings) // 10)),
    )
    return tsne.fit_transform(embeddings)


def create_2d_embeddings_for_texts(texts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create embeddings for texts and reduce to 2D for visualization.

    Args:
        texts: List of strings to visualize

    Returns:
        Tuple of (original_embeddings, reduced_embeddings)
        - original_embeddings: Array with shape (n_samples, embedding_dim)
        - reduced_embeddings: Array with shape (n_samples, 2)
    """
    if not texts:
        return np.array([]), np.array([])

    # Get embeddings
    embeddings = create_embeddings(texts)

    # Reduce dimensionality for visualization
    reduced_embeddings = (
        reduce_to_2d(embeddings) if len(texts) > 1 else np.zeros((1, 2))
    )

    return embeddings, reduced_embeddings
