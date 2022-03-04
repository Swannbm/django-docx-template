from io import BytesIO
from pydoc import locate
import random

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from docxtpl import DocxTemplate as DocxEngine

from .utils import import_from_string, merge_url_parts
from .data_sources import DataSource


def upload_to_hook(instance: 'DocxTemplate', filename: str) -> str:
    """This is a hook to set a upload_to throug settings"""
    try:
        func = locate(settings.DJANGO_DOCX_TEMPLATES["upload_to"])
        return func(instance, filename)
    except (ValueError, KeyError, TypeError):
        return filename


class DocxTemplate(models.Model):
    slug = models.SlugField("slug", primary_key=True, blank=True)
    name = models.CharField("Name", max_length=100)
    # description = models.TextField("Description", blank=True, null=True)
    docx = models.FileField(upload_to=upload_to_hook)
    data_source_class = models.CharField(
        "DataSource class", max_length=250, blank=True, null=True
    )

    @property
    def data_source(self) -> DataSource:
        return import_from_string(self.data_source_class)

    def get_url(self) -> str:
        url = settings.DJANGO_DOCX_TEMPLATES["docx_template_url"]
        url = url.replace("<slug>", self.slug)
        url = url.replace("<slug:slug>", self.slug)
        return merge_url_parts(url, self.data_source.get_url())

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def _merge(self, context: dict()) -> BytesIO:
        """Load actual docx file and merge all fields. Return the final doc as BytesIO."""
        docx_engine = DocxEngine(self.docx)
        docx_engine.render(context)
        buffer = BytesIO()
        docx_engine.save(buffer)
        buffer.seek(0)
        return buffer

    def merge(self, **kwargs) -> BytesIO:
        """Load the docx template and merge it. Then return it as in memory object

        1. Load dynamically the data_source and get context data from it
        2. Open the filefield as DocxTemplate
        3. merge document
        4. save the new document in memory and return it

        Parameters
        ==========
        * **kwargs: all keys required to load correctly context data

        Return
        ======
        BytesIO
        """
        context = self.data_source.get_context_data(**kwargs)
        return self._merge(context=context)

    def merge_example(self, example_number=None) -> BytesIO:
        if example_number:
            context = self.data_source.get_example(example_number)
        else:
            combinations = self.data_source.get_all_example_combinations()
            context = random.choice(combinations)
        return self._merge(context=context)
