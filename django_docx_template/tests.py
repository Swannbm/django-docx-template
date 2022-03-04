"""

"""
from io import BytesIO
import pytest
from pathlib import Path

from django.conf import settings
# from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile

from . import data_sources
from .models import DocxTemplate
from .utils import import_from_string


@pytest.fixture(scope='session', autouse=True)
def clean_media_dir():
    # before all tests
    yield
    # Will be executed after the last test
    for p in Path(settings.MEDIA_ROOT).iterdir():
        if p.is_file():
            p.unlink()


class SimpleDataSource(data_sources.DataSource):
    label = "A simple data source"
    url_tags = {"person_id": "int"}
    first_name = data_sources.CharField()
    last_name = data_sources.CharField(help="super help label")
    birth_year = data_sources.IntField(examples=[1982, 1992, 2002])


class TestSimpleDataSource:
    def test_get_data_fields(self):
        sds = SimpleDataSource()
        data = sds.get_data_fields()
        assert len(data) == 3
        assert "first_name" in data
        assert isinstance(data["first_name"].data_type, str)
        assert "last_name" in data
        assert "birth_year" in data
        assert isinstance(data["first_name"].data_type, int)

    def test_get_data_definition(self):
        sds = SimpleDataSource()
        data = sds.get_data_definition()
        assert data[0]['name'] == "first_name"
        assert data[1]['type'] == "String"
        assert data[2]['type'] == "Integer"
        assert data[1]['description'] == "super help label"
        assert data[2]['examples'] == [1982, 1992, 2002]

    def test_get_url(self):
        sds = SimpleDataSource()
        assert sds.get_url() == "<int:person_id>"
        sds.url_tags.update({
            "label":"slug",
            "colour":"float",
        })
        assert sds.get_url() == "<int:person_id>/<slug:label>/<float:colour>"

    def test_get_label(self):
        sds = SimpleDataSource()
        assert sds.get_label() == "A simple data source"

    def test_get_queryset(self):
        sds = SimpleDataSource()


@pytest.fixture
def docx_template_fixtures(db):
    content = open("django_docx_template/test_doc.docx", "rb").read()
    suf = SimpleUploadedFile("template.docx", content)
    templates = [
        DocxTemplate(name="Beautiful document", docx=suf),
    ]
    for template in templates:
        template.save()  # should trigger slugification


class TestDocxTemplate:
    @pytest.mark.django_db
    def test_slugification(self):
        content = open("django_docx_template/test_doc.docx", "rb").read()
        suf = SimpleUploadedFile("template.docx", content)
        template = DocxTemplate(name="Document to slugify", docx=suf)
        template.save()
        assert template.slug == "document-to-slugify"

    def test_upload_to_hook(self):
        # TODO
        pass

    def test_merge(self, docx_template_fixtures):
        content = open("django_docx_template/test_doc.docx", "rb").read()
        suf = SimpleUploadedFile("template.docx", content)
        template = DocxTemplate(
            name="Beautiful document",
            docx=suf,
            data_source_class="django_docx_template.tests.CustomDataSource",
        )
        in_memory_doc = template.merge(item_3="from_keys")
        assert isinstance(in_memory_doc, BytesIO)


class TestDataSource:
    def test_get_data_definition(self):
        ds = CustomDataSource()
        definition = ds.get_data_definition()
        assert len(definition) == 3
        assert definition[1]["name"] == "item_2"


class TestUtils:
    def test_import_from_string(self):
        import_str = "django.utils.text.slugify"
        slugify = import_from_string(import_str)
        assert slugify("1 2 3") == "1-2-3"
