from rest_framework.pagination import PageNumberPagination

from .constants import PAGE_SIZE, MAX_PAGE_SIZE


class CustomPagination(PageNumberPagination):
    """Кастомный пагинатор"""

    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
    max_page_size = MAX_PAGE_SIZE
