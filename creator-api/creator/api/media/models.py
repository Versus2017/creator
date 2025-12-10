import logging
import os
from sqlalchemy_utils import generic_relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import (
    create_engine,
    Unicode,
    Text,
    Column,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    Boolean,
    Date
)
from PIL import Image
from sqlalchemy.orm import Mapped, mapped_column
from ...db import (
    CRUDMixin,
    ProfileMixin,
    sm,
    string_property,
)
from ...config import config

logger = logging.getLogger(__name__)


class MediaModel(CRUDMixin, ProfileMixin,):
    __tablename__ = 'media'

    object_type: Mapped[str] = mapped_column(Unicode, nullable=True)
    object_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    @declared_attr
    def object(cls):
        return generic_relationship(cls.object_type, cls.object_id)

    @string_property
    def filename(self):
        pass

    @classmethod
    def link_obj(cls, media_ids, obj):
        for m in cls.get_by_obj(obj):
            m.delete()

        for media_id in media_ids:
            m = cls.get_or_404(media_id)
            m.update(
                object_id=obj.id,
                object_type=obj.__class__.__name__,
            )

    @classmethod
    def get_by_obj(cls, obj):
        return cls.query.filter(cls.object == obj).order_by(MediaModel.id)

    @classmethod
    def save_thumbnail(cls, filename):
        directory = config.UPLOADS_DEFAULT_DEST
        if len(filename.split('.')) != 2:
            return
        path = os.path.join(directory, filename)
        name = filename.split('.')[0]
        ext = filename.split('.')[1]
        im = Image.open(path)
        im.thumbnail(config.DEFAULT_THUMBNAIL_SIZE)
        thumbnail_filename = '{}_thumbnail.{}'.format(name, ext)
        thumbnail_path = os.path.join(directory, thumbnail_filename)
        logger.info(
            'writing thumbnail image to file %s', thumbnail_filename)
        im.save(thumbnail_path)
        return thumbnail_filename

    @property
    def url(self):
        external_url = config.EXTERNAL_URL
        debug = config.DEBUG
        # filepath = config.UPLOADS_DEFAULT_DEST
        url = f'{external_url}/media/{self.filename}'
        if not debug:
            return url.replace('http://', 'https://')
        return url

    @property
    def thumbnail_url(self):
        external_url = config.EXTERNAL_URL
        debug = config.DEBUG
        thumbnail_filename = f'{self.filename.split(".")[0]}_thumbnail.{self.filename.split(".")[1]}'
        url = f'{external_url}/media/{thumbnail_filename}'
        if not debug:
            return url.replace('http://', 'https://')
        return url

    def dump(self):
        return dict(
            id=self.id,
            filename=self.filename,
            thumbnail_url=self.thumbnail_url,
            url=self.url,
        )
