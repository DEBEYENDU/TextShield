"""Entity resolution."""
def resolve(entities):
    # simple exact match
    return {e['normalized']: e for e in entities}
