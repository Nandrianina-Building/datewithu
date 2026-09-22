from rest_framework.pagination import PageNumberPagination


class TenPerPagePagination(PageNumberPagination):
    """
    Pagination à 10 résultats par page — utilisée pour l'explorateur de
    lieux (page « Explorer »), où l'on veut des pages courtes avec
    Précédent/Suivant plutôt qu'un long défilement.
    """

    page_size = 10
