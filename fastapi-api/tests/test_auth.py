import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.anyio
async def test_signup_and_login(tmp_path, monkeypatch):
    async with AsyncClient(app=app, base_url="https://traxy-backend.uc.r.appspot.com") as ac:
        # sign up
        r = await ac.post('/api/auth/signup', json={"username": "u1", "password": "p1"})
        assert r.status_code == 200
        # login
        r2 = await ac.post('/api/auth/login', json={"username": "u1", "password": "p1"})
        assert r2.status_code == 200
        assert 'access_token' in r2.json()
