"""Tests for prompt rendering API."""

from fastapi.testclient import TestClient


def _register_test_prompt(client: TestClient) -> None:
    """Helper to register a test prompt."""
    client.post(
        "/v1/prompts",
        json={
            "id": "test_sales",
            "name": "销售测试",
            "category": "sales",
            "variables": [
                {"name": "product_name", "required": True},
                {"name": "price", "required": True},
                {"name": "vip", "required": False, "default": False},
            ],
            "template": "推荐 {{ product_name }}，售价 {{ price }} 元。{% if vip %}VIP 尊享！{% endif %}",
        },
    )


def test_render_simple_variables(client: TestClient) -> None:
    """Test rendering with simple variable interpolation."""
    _register_test_prompt(client)

    response = client.post(
        "/v1/prompts/test_sales/render",
        json={"variables": {"product_name": "iPhone", "price": "5999"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["prompt_id"] == "test_sales"
    assert "iPhone" in data["rendered"]
    assert "5999" in data["rendered"]


def test_render_conditional(client: TestClient) -> None:
    """Test rendering with Jinja2 conditional."""
    _register_test_prompt(client)

    response = client.post(
        "/v1/prompts/test_sales/render",
        json={"variables": {"product_name": "iPhone", "price": "5999", "vip": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert "VIP 尊享！" in data["rendered"]


def test_render_missing_variables(client: TestClient) -> None:
    """Test rendering with missing required variables returns 400."""
    _register_test_prompt(client)

    response = client.post(
        "/v1/prompts/test_sales/render",
        json={"variables": {"product_name": "iPhone"}},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "MISSING_VARIABLES"
    assert "price" in data["detail"]["missing"]


def test_render_default_variables(client: TestClient) -> None:
    """Test rendering with default variable values."""
    _register_test_prompt(client)

    response = client.post(
        "/v1/prompts/test_sales/render",
        json={"variables": {"product_name": "iPhone", "price": "5999"}},
    )
    assert response.status_code == 200
    data = response.json()
    # vip defaults to false, so VIP text should not appear
    assert "VIP 尊享！" not in data["rendered"]


def test_render_not_found(client: TestClient) -> None:
    """Test rendering a non-existent prompt returns 404."""
    response = client.post(
        "/v1/prompts/non_existent/render",
        json={"variables": {}},
    )
    assert response.status_code == 404
