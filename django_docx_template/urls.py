from django.conf import settings
from django.urls import path

from . import views
from .models import DocxTemplate
from .utils import merge_url_parts


app_name = "docx_template"


def get_template_urls():
    urlpatterns = []
    templates = DocxTemplate.objects.all()
    for template in templates:
        # merge url
        url = template.get_url()
        name = f"{template.slug}-merge"
        kwargs = {"slug": template.slug}
        view = views.TemplateMergeView.as_view()
        p = path(url, view, kwargs, name=name)
        urlpatterns.append(p)
    return urlpatterns


urlpatterns = get_template_urls()

urlpatterns += [
    path("templates", views.TemplateListView.as_view(), name="list"),
    path(
        settings.DJANGO_DOCX_TEMPLATES["docx_template_url"],
        views.TemplateDetailView.as_view(),
        name="detail",
    ),
    path("templates/create", views.TemplateCreateView.as_view(), name="create"),
    path("templates/update/<slug>", views.TemplateUpdateView.as_view(), name="update"),
    path("templates/delete/<slug>", views.TemplateDeletelView.as_view(), name="delete"),
    path(
        merge_url_parts(
            settings.DJANGO_DOCX_TEMPLATES["docx_template_url"],
            "example",
        ),
        views.TemplateExampleMergeView.as_view(),
        name="merge-example",
    ),
    path(
        merge_url_parts(
            settings.DJANGO_DOCX_TEMPLATES["docx_template_url"],
            "example/<int:example_number>",
        ),
        views.TemplateExampleMergeView.as_view(),
        name="merge-example",
    ),
    path("sources", views.DataSourceListView.as_view(), name="data_source_list"),
    path(
        "sources/detail/<slug>",
        views.DataSourceDetailView.as_view(),
        name="data_source",
    ),
]
