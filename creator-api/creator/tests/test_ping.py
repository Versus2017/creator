

def test_ping(client):
    resp = client.get('/v1/ping')
    assert resp.status_code == 200
    assert 'success' in resp.json['data']
