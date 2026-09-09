import httpx

query = """
[out:json][timeout:30];
node["shop"](around:1000,28.7041,77.1025);
out center;
"""

url = "https://overpass-api.de/api/interpreter"

# Try 1
print("Try 1 (data dict)")
try:
    r1 = httpx.post(url, data={"data": query}, headers={"User-Agent": "GramVyaparBackend/1.0"})
    print(r1.status_code)
except Exception as e:
    print(e)

# Try 2
print("Try 2 (raw body)")
try:
    r2 = httpx.post(url, content=query, headers={"User-Agent": "GramVyaparBackend/1.0", "Content-Type": "application/x-www-form-urlencoded"})
    print(r2.status_code)
except Exception as e:
    print(e)
