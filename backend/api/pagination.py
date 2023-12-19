from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """
    Пользовательская пагинация.
    Включает ключ запроса для указания размера страницы.
    """

    page_size = 6
    page_size_query_param = "limit"


class NonePagination(PageNumberPagination):
    """
    Пагинация без страниц.
    Показывает все результаты без пагинации.
    """

    page_size = None
    max_page_size = None
    page_query_param = "page"
