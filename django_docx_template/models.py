from io import BytesIO
from pydoc import locate
import random

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from docxtpl import DocxTemplate as DocxEngine

from .utils import import_from_string, merge_url_parts
from .data_sources import DataSource


def upload_to_hook(instance: "DocxTemplate", filename: str) -> str:
    """This is a hook to set a upload_to throug settings"""
    try:
        func = locate(settings.DJANGO_DOCX_TEMPLATES["upload_to"])
        return func(instance, filename)
    except (ValueError, KeyError, TypeError):
        return filename


class DocxTemplate(models.Model):
    slug = models.SlugField("Slug", primary_key=True, blank=True)
    name = models.CharField("Name", max_length=100)
    # description = models.TextField("Description", blank=True, null=True)
    docx = models.FileField(upload_to=upload_to_hook)
    data_source_class = models.CharField(
        "DataSource class", max_length=250, blank=True, null=True
    )

    @property
    def data_source(self) -> DataSource:
        return import_from_string(self.data_source_class)

    def get_absolute_url(self):
        return reverse("docx_template:detail", args={"slug": self.slug})

    def get_merge_url(self) -> str:
        """This method is used for building urls.py, therefore it can't use reverse()"""
        return merge_url_parts(
            f"templates/merge/{self.slug}",
            self.data_source.get_url(),
        )

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def _clean_context(self, docx_engine, context):
        """Hook to transform context data before merging document."""
        self._clean_context_image(docx_engine, context)

    def _clean_context_image(self, docx_engine, context):
        """
        Because we need a reference to DocxTemplate to correctly add image
        we have to wait the very last moment to init InLine object.

        Example of 'context' parameter:
        ===============================

        context["images"] = {
            "image_1": Image("path/to/file.png"),
            "image_2": Image("path/to/file.png", width=170),
        }

        output:

        context = {
            "image_1": InlineImage(...),
            "image_2": InlineImage(...),
        }

        Todo
        ====
        . avoid storing all images in a specific part of the context, make a recursive
        function to find all instances of previous class to replace it with correct
        InLine image
        """
        context["cleaned_images"] = list()
        images = context.get("images", list())
        for name, image in images.items():
            context[name] = image.convert(docx_engine)

    def _merge(self, context: dict()) -> BytesIO:
        """Load actual docx file and merge all fields. Return the final doc as BytesIO."""
        docx_engine = DocxEngine(self.docx)
        self._clean_context(docx_engine, context)
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
