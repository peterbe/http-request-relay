import os
from urllib.parse import urlencode

import requests


CHALICE_URL = os.environ.get("CHALICE_URL", "http://localhost:8000/")


def test_get_happy_path():
    url = "https://www.peterbe.com/api/v0/whereami"
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": url}))
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["attempts"] == 1
    assert data["meta"]["nobody"] is False
    assert data["meta"]["took"]
    assert data["response"]["elapsed"]
    assert data["request"]["headers"] == {}
    assert data["request"]["url"] == url
    assert data["request"]["method"] == "get"
    assert 1 < data["request"]["timeout"] < 60
    assert data["response"]["body"]
    assert data["response"]["headers"]
    assert not data["error"]


def test_head_happy_path():
    url = "https://www.peterbe.com/api/v0/whereami"
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": url, "method": "head"}))
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["attempts"] == 1
    assert data["meta"]["nobody"] is False
    assert data["meta"]["took"]
    assert data["response"]["elapsed"]
    assert data["request"]["headers"] == {}
    assert data["request"]["url"] == url
    assert data["request"]["method"] == "head"
    assert 1 < data["request"]["timeout"] < 60
    assert not data["response"]["body"]
    assert data["response"]["headers"]
    assert not data["error"]


def test_post_happy_path():
    url = "https://www.peterbe.com/api/v0/whereami"
    r = requests.post(CHALICE_URL, json={"url": url})
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["attempts"] == 1
    assert data["meta"]["nobody"] is False
    assert data["meta"]["took"]
    assert data["request"]["headers"] == {}
    assert data["request"]["url"] == url
    assert data["request"]["method"] == "get"  # Note!
    assert 1 < data["request"]["timeout"] < 60
    assert data["response"]["body"]
    assert data["response"]["headers"]
    assert not data["error"]


def test_post_head():
    url = "https://www.peterbe.com/api/v0/whereami"
    r = requests.post(CHALICE_URL, json={"url": url, "method": "head"})
    assert r.status_code == 200
    data = r.json()
    assert data["request"]["method"] == "head"  # Note!
    assert not data["response"]["body"]
    assert data["response"]["headers"]
    assert not data["error"]


def test_get_bad_timeout():
    url = "https://www.peterbe.com/api/v0/whereami"
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": url, "timeout": 0}))
    assert r.status_code == 400
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": url, "timeout": 60}))
    assert r.status_code == 400


def test_get_bad_url():
    r = requests.get(CHALICE_URL)
    assert r.status_code == 400
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": ""}))
    assert r.status_code == 400
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": "ftp://dom.ain/path"}))
    assert r.status_code == 400
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": "**************"}))
    assert r.status_code == 400


def test_get_bad_method():
    url = "https://www.peterbe.com/api/v0/whereami"
    r = requests.put(CHALICE_URL, json={"url": url})
    assert r.status_code == 405
    r = requests.delete(CHALICE_URL + "?" + urlencode({"url": "**************"}))
    assert r.status_code == 405


def test_brotli_support():
    url = "https://www.peterbe.com/permasearch/blogposts.json"
    r = requests.post(
        CHALICE_URL, json={"url": url, "headers": {"accept-encoding": "br"}}
    )
    assert r.status_code == 200
    data = r.json()
    assert not data["error"]
    assert iget(data["response"]["headers"], "content-encoding") == "br"
    assert isinstance(data["response"]["body"], dict)


def iget(map, key, default=None):
    for k in map:
        if k.lower() == key.lower():
            return map[k]
    return default


def test_bad_domain():
    url = "https://xxx.peterbe.com/whatever"
    r = requests.get(CHALICE_URL + "?" + urlencode({"url": url}))
    assert r.status_code == 200
    data = r.json()
    assert not data["response"]
    assert data["error"]
    assert data["error"]["type"] == "ConnectionError"
    assert "xxx.peterbe.com" in data["error"]["value"]
