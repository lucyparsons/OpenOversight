# Routing and view tests
import pytest

@pytest.mark.parametrize("route", [
    ('/'),
    ('/index'),
    ('/find'),
    ('/about'),
    ('/contact'),
    ('/privacy'),
    ('/label')
])
def test_routes_ok(route, client):
    rv = client.get(route)
    assert rv.status_code == 200

@pytest.mark.parametrize("route", [
    ('/gallery'),
    ('/upload')
])
def test_route_method_not_allowd(route, client):
    rv = client.get(route)
    assert rv.status_code == 405