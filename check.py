import json, os, urllib.request

cfg = json.load(open("coins.json"))
try:
    state = json.load(open("state.json"))
except Exception:
    state = {}

ids = ",".join(c["id"] for c in cfg)
url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
req = urllib.request.Request(url, headers={"User-Agent": "price-alert"})
prices = json.load(urllib.request.urlopen(req, timeout=30))
topic = os.environ["NTFY_TOPIC"]


def notify(msg):
    r = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=msg.encode(),
        headers={"Title": "Price alert"},
    )
    urllib.request.urlopen(r, timeout=30)


for c in cfg:
    name = c["id"]
    p = prices.get(name, {}).get("usd")
    if p is None:
        print("no price for", name)
        continue
    print(name, p)
    for kind in ("above", "below"):
        if kind not in c:
            continue
        key = f"{name}-{kind}-{c[kind]}"
        hit = p > c[kind] if kind == "above" else p < c[kind]
        if hit and not state.get(key):
            notify(f"{name} is ${p} ({kind} {c[kind]})")
            state[key] = True
        elif not hit:
            state[key] = False

json.dump(state, open("state.json", "w"))
