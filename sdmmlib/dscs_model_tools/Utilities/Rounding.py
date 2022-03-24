def remaining_chunk_length(size, chunksize):
    return (chunksize - (size % chunksize)) % chunksize


def roundup(size, chunksize):
    return size + remaining_chunk_length(size, chunksize)
