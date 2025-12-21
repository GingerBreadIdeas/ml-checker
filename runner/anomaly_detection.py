import logging
import os
from typing import List, Tuple

import numpy as np
import torch
from sklearn.manifold import TSNE

# Set this environment variable to avoid parallelism-related warnings and errors
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Setup logging
logger = logging.getLogger(__name__)





def create_2d_embeddings_for_texts(
    texts: List[str],
) -> Tuple[np.ndarray, np.ndarray]:
    if not texts:
        return np.array([]), np.array([])

    # Get embeddings
    embeddings = create_embeddings(texts)

    # Reduce dimensionality for visualization
    reduced_embeddings = (
        reduce_to_2d(embeddings) if len(texts) > 1 else np.zeros((1, 2))
    )

    return embeddings, reduced_embeddings
