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
from . import utils


@pytest.fixture(scope="session", autouse=True)
def clean_media_dir():
    # before all tests
    yield
    # Will be executed after the last test
    for p in Path(settings.MEDIA_ROOT).iterdir():
        if p.is_file():
            p.unlink()


class SimpleDataSource(data_sources.DataSource):
    label = "A simple data source"
    url_args = {"person_id": "int"}
    first_name = data_sources.Field()
    last_name = data_sources.CharField(help="super help label")
    birth_year = data_sources.IntField(examples=[1982, 1992, 2002])


class ImageDataSource(data_sources.DataSource):
    def get_context_data(self, *args, **kwargs):
        path = "django_docx_template/static/django_docx_template/test_image.png"
        return {
            "first_name": "First Name",
            "last_name": "Last Name",
            "birth_year": 2022,
            "images": {"image_1": data_sources.Image(path, width=170, height=20)},
        }


class TestSimpleDataSource:
    def test_class_path(self):
        sds = SimpleDataSource("any/class/path")
        assert sds.class_path == "any/class/path"

    def test_get_data_fields(self):
        sds = SimpleDataSource("any/class/path")
        data = sds.get_data_fields()
        assert len(data) == 3
        assert "first_name" in data
        assert data["first_name"].data_type is None
        assert "last_name" in data
        assert data["last_name"].data_type is str
        assert "birth_year" in data
        assert data["birth_year"].data_type is int

    def test_get_data_definition(self):
        sds = SimpleDataSource("any/class/path")
        data = sds.get_data_definition()
        assert data[0]["name"] == "birth_year"
        assert data[1]["type"] == "Not provided"
        assert data[0]["type"] == "Integer"
        assert data[2]["type"] == "String"
        assert data[2]["help"] == "super help label"
        assert data[0]["examples_values"] == "1982, 1992, 2002"

    def test_get_url(self):
        sds = SimpleDataSource("any/class/path")
        assert sds.get_url() == "<int:person_id>"
        sds.url_args.update(
            {
                "label": "slug",
                "colour": "float",
            }
        )
        assert sds.get_url() == "<int:person_id>/<slug:label>/<float:colour>"

    def test_get_label(self):
        sds = SimpleDataSource("any/class/path")
        assert sds.get_label() == "A simple data source"

    def test_get_queryset(self):
        sds = SimpleDataSource("any/class/path")
        sds


class TestImage:
    def test_instance_isnstance_of_convertermixin(self):
        path = "django_docx_template/static/django_docx_template/test_image.png"
        img = data_sources.Image(path)
        assert isinstance(img, data_sources.ConverterMixin)

    def test_init_without_correct_file_path(self):
        with pytest.raises(ValueError):
            data_sources.Image("not/a/file/path")

    def test_init(self):
        from docx.shared import Mm
        path = "django_docx_template/static/django_docx_template/test_image.png"
        img = data_sources.Image(path)
        assert img.img_path == path
        assert img.width is None
        assert img.height is None
        img = data_sources.Image(path, width=60, height=70)
        assert isinstance(img.width, Mm)
        assert isinstance(img.height, Mm)

    def test_convert(self):
        from docxtpl import InlineImage
        path = "django_docx_template/static/django_docx_template/test_image.png"
        img = data_sources.Image(path, width=60, height=70)
        inline_image = img.convert(None)
        assert isinstance(inline_image, InlineImage)
        assert inline_image.width == img.width
        assert inline_image.width == img.width
        assert inline_image.height == img.height


@pytest.fixture
def docx_template_fixtures(db):
    content = open("django_docx_template/test_doc.docx", "rb").read()
    suf = SimpleUploadedFile("template.docx", content)
    templates = [
        DocxTemplate(name="Beautiful document", docx=suf),
    ]
    for template in templates:
        template.save()  # should trigger slugification


DIR_PATH = Path("media/test_dir")


def upload_to(instance, filename):
    return DIR_PATH / filename


@pytest.mark.django_db
class TestDocxTemplate:
    def test_slugification(self):
        content = open("django_docx_template/test_doc.docx", "rb").read()
        suf = SimpleUploadedFile("template.docx", content)
        template = DocxTemplate(name="Document to slugify", docx=suf)
        template.save()
        assert template.slug == "document-to-slugify"

    def test_upload_to_hook(self, settings):
        DIR_PATH.mkdir(parents=True, exist_ok=True)
        settings.DJANGO_DOCX_TEMPLATES.update(
            {"upload_to": "django_docx_template.tests.upload_to"}
        )
        content = open("django_docx_template/test_doc.docx", "rb").read()
        suf = SimpleUploadedFile("template.docx", content)
        template = DocxTemplate(name="Beautiful document", docx=suf)
        template.save()
        assert template.docx.name.startswith(str(DIR_PATH))

    def test_merge(self, docx_template_fixtures):
        content = open("django_docx_template/test_doc.docx", "rb").read()
        suf = SimpleUploadedFile("template.docx", content)
        template = DocxTemplate(
            name="Beautiful document",
            docx=suf,
            data_source_class="django_docx_template.tests.SimpleDataSource",
        )
        in_memory_doc = template.merge(item_3="from_keys")
        assert isinstance(in_memory_doc, BytesIO)

    def test_merge_with_image(self):
        content = open("django_docx_template/test_doc.docx", "rb").read()
        suf = SimpleUploadedFile("template.docx", content)
        template = DocxTemplate(
            name="Beautiful document",
            docx=suf,
            data_source_class="django_docx_template.tests.ImageDataSource",
        )
        in_memory_doc = template.merge(item_3="from_keys")
        assert isinstance(in_memory_doc, BytesIO)


class TestUtils:
    def test_import_from_string(self):
        # import_str = "django.utils.text.slugify"
        import_str = "django_docx_template.tests.SimpleDataSource"
        sds = utils.import_from_string(import_str)
        assert isinstance(sds, SimpleDataSource)

    def test_get_all_data_sources(self, settings):
        data_source_list = {
            "data_sources": [
                "django_docx_template.tests.SimpleDataSource",
                "django_docx_template.tests.SimpleDataSource",
                "django_docx_template.tests.SimpleDataSource",
            ]
        }
        settings.DJANGO_DOCX_TEMPLATES = data_source_list
        all_ds = utils.get_all_data_sources()
        assert len(all_ds) == 3
        assert sum([isinstance(sds, SimpleDataSource) for sds in all_ds]) == 3
