import pytest

from app.services.matching import cosine_similarity

pytestmark = pytest.mark.slow


def test_real_sentence_transformer_embeddings_are_meaningful():
    pytest.importorskip("sentence_transformers")

    from app.services.matching import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder()
    vectors = embedder.embed(
        [
            "python backend developer api database",
            "python backend developer api database",
            "graphic designer illustration branding",
        ]
    )

    assert len(vectors) == 3
    assert len(vectors[0]) == len(vectors[1])
    same = cosine_similarity(vectors[0], vectors[1])
    different = cosine_similarity(vectors[0], vectors[2])

    assert same > 0.99
    assert same > different
