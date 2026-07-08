from app.core.auth import (
    SESSION_COOKIE,
    check_credentials,
    create_session_token,
    revoke_session_token,
    verify_session_token,
)


# --- Core auth unit tests ---

def test_check_credentials_correct():
    assert check_credentials("admin", "testpassword") is True


def test_check_credentials_wrong_password():
    assert check_credentials("admin", "wrongpassword") is False


def test_check_credentials_wrong_username():
    assert check_credentials("wronguser", "testpassword") is False


def test_verify_session_token_invalid():
    assert verify_session_token("not-a-valid-token") is False


def test_revoke_session_token_valid():
    token = create_session_token()
    assert verify_session_token(token) is True
    revoke_session_token(token)
    assert verify_session_token(token) is False


def test_revoke_session_token_invalid_is_noop():
    revoke_session_token("invalid-token")  # must not raise


# --- API login/logout tests ---

def test_login_page_get(anon_client):
    response = anon_client.get("/login")
    assert response.status_code == 200


def test_login_success(anon_client):
    response = anon_client.post(
        "/login",
        data={"username": "admin", "password": "testpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/dashboard" in response.headers["location"]


def test_login_wrong_password(anon_client):
    response = anon_client.post(
        "/login",
        data={"username": "admin", "password": "wrongpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_login_wrong_username(anon_client):
    response = anon_client.post(
        "/login",
        data={"username": "wronguser", "password": "testpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_logout(client):
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers["location"]
    assert SESSION_COOKIE not in response.cookies or response.cookies[SESSION_COOKIE] == ""
