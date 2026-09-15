"""Entity normalization."""
def normalize_email(v): return v.strip().lower()
def normalize_phone(v): return ''.join(filter(str.isdigit, v))
def normalize_domain(v): return v.lower().strip('.')
def normalize_url(v): return v.lower()
