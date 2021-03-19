from flask import Markup, url_for
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import FileColumn
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_appbuilder.filemanager import get_file_original_name
from flask_appbuilder.models.decorators import renders

class Data(Model):
    __tablename__ = 'datas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(Integer, ForeignKey('tags.id'))
    tag = relationship("Tag", uselist=False)
    tag_value = Column(Integer, nullable=False)

    def __init__(self, tag_id, tag_value):
        self.tag_id = tag_id
        self.tag_value = tag_value

    def __repr__(self):
        return str(self.id)

    def title(self):
        print(self.tag)
        return self.tag.get_title()
    
    def file_name(self):
        return self.tag.file.file_name()

    def tag_source(self):
        return self.tag.tag_source
    
    def tag_name(self):
        return self.tag.tag_name

class File(Model):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file = Column(FileColumn, nullable=False)
    title = Column(String(50))
    is_load = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.now)

    def download(self):
        return Markup(
            '<a href="'
            + url_for("FileModelView.download", filename=str(self.file))
            + '">下载</a>'
        )

    def file_name(self):
        return get_file_original_name(str(self.file))

class Tag(Model):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship("File")
    tag_source = Column(String(50), nullable=False)
    tag_name = Column(String(50))
    order = Column(Integer)
    data = relationship('Data', uselist=False)

    def __init__(self, file_id, tag_source, order):
        self.file_id = file_id
        self.tag_source = tag_source
        self.order = order

    def file_name(self):
        return self.file.file_name()

    def get_tag_name(self):
        return self.tag_name if (self.tag_name is not None) and len(self.tag_name) > 0 else self.tag_source

    def get_title(self):
        return self.file.title
