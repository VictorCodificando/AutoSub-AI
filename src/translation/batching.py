from src.models import TranscriptionSegment


def create_batchs(
    segments: list[TranscriptionSegment], max_size=400
):  # Max size is the max characters in a segment sended to the llm, every segment must have max_size or less characters
    batch = []

    for s in segments:
        if batch and (len(batch) >= max_size):
            yield batch
            batch = []
        batch.append(s)
    if batch:
        yield batch
