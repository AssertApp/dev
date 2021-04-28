def URLValidate(url):
    if url.startswith("http://"):
        return url.replace("http://","https://")
    if not url.startswith("https://"):
        return "https://" + url
    return url
