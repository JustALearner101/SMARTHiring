from app.dto.BaseDTO import PaginatedResponse, PaginationParams


def test_pagination_params_defaults():
    params = PaginationParams()
    assert params.page == 1
    assert params.page_size == 20
    assert params.offset == 0
    assert params.limit == 20


def test_pagination_params_custom():
    params = PaginationParams(page=3, page_size=15)
    assert params.page == 3
    assert params.page_size == 15
    assert params.offset == 30
    assert params.limit == 15


def test_paginated_response_create_empty():
    res = PaginatedResponse.create(items=[], total=0, page=1, page_size=20)
    assert res.items == []
    assert res.total == 0
    assert res.page == 1
    assert res.page_size == 20
    assert res.total_pages == 0
    assert res.has_next is False
    assert res.has_prev is False


def test_paginated_response_create_first_page():
    items = ["item1", "item2", "item3"]
    res = PaginatedResponse.create(items=items, total=25, page=1, page_size=10)
    assert len(res.items) == 3
    assert res.total == 25
    assert res.page == 1
    assert res.page_size == 10
    assert res.total_pages == 3
    assert res.has_next is True
    assert res.has_prev is False


def test_paginated_response_create_middle_page():
    items = ["item11", "item12"]
    res = PaginatedResponse.create(items=items, total=25, page=2, page_size=10)
    assert res.total_pages == 3
    assert res.has_next is True
    assert res.has_prev is True


def test_paginated_response_create_last_page():
    items = ["item21"]
    res = PaginatedResponse.create(items=items, total=25, page=3, page_size=10)
    assert res.total_pages == 3
    assert res.has_next is False
    assert res.has_prev is True


def test_paginated_response_create_exact_division():
    items = ["item11", "item12"]
    res = PaginatedResponse.create(items=items, total=20, page=2, page_size=10)
    assert res.total_pages == 2
    assert res.has_next is False
    assert res.has_prev is True
