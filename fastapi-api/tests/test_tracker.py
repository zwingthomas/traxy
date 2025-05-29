import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.anyio
async def test_tracker_crud_and_aggregate(monkeypatch):
    async with AsyncClient(app=app, base_url="https://traxy-backend.uc.r.appspot.com") as ac:
        # signup/login
        await ac.post('/api/auth/signup', json={"username":"t1","password":"p1"})
        r = await ac.post('/api/auth/login', json={"username":"t1","password":"p1"})
        token = r.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        # create tracker
        tr = await ac.post('/api/trackers', json={"name":"Test","color":"#0f0","rule":{"multiplier":1},"visibility":"public"}, headers=headers)
        assert tr.status_code == 200
        tid = tr.json()['id']
        # record activities
        await ac.post('/api/activities', json={"tracker_id": tid, "value": 2}, headers=headers)
        # get aggregates
        agg = await ac.get(f'/api/users/t1/trackers?visibility=public', headers=headers)
        assert agg.status_code == 200
        data = agg.json()
        assert isinstance(data, list)