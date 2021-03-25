from flask import Markup, url_for
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import FileColumn, ImageColumn
from flask_appbuilder.filemanager import ImageManager
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

class Predict(Model):
    __tablename__ = "predicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('predict_files.id'))
    file = relationship('PredictFile')
    predict_value = Column(String(100))
    predict_type_id = Column(Integer, ForeignKey('predict_types.id'))
    predict_type = relationship('PredictType')
    predict_record_id = Column(Integer, ForeignKey('predict_records.id'))
    predict_record = relationship('PredictRecord')


    def file_name(self):
        return self.file.file_name()
    
    def predict_name(self):
        return self.file.name

    def predict_type_name(self):
        if self.predict_type:
            return self.predict_type.name
        else:
            return ""

    def predict_image(self):
        if self.predict_type:
            return self.predict_type.photo_img()
        return ""

    def predict_record_name(self):
        if self.predict_record:
            return self.predict_record.name
        return ""

    def predict_record_file_name(self):
        if self.predict_record:
            return self.predict_record.file_name()
        return ""

class PredictFile(Model):
    __tablename__ = "predict_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file = Column(FileColumn, nullable=False)
    name = Column(String(100), nullable=False, unique=True)
    
    def file_name(self):
        return get_file_original_name(str(self.file))

    def __repr__(self):
        return self.name

class PredictType(Model):
    __tablename__ = 'predict_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    source_name = Column(String(100), nullable=False, unique=True)

    predict_image_id = Column(Integer, ForeignKey('predict_images.id'))
    predict_image = relationship('PredictImage')

    def photo_img(self):
        if self.predict_image:
            return self.predict_image.photo_img()
        return ""

    def photo_img_thumbnail(self):
        return self.predict_image.photo_img_thumbnail() if self.predict_image else ""

    def photo_name(self):
        return self.predict_image if self.predict_image else ""


class PredictImage(Model):
    __tablename__ = "predict_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    image = Column(ImageColumn(size=(300, 300, True), thumbnail_size=(30, 30, True)))

    def __repr__(self):
        return self.name

    def image_name(self):
        return get_file_original_name(str(self.image))

    def photo_img(self):
        im = ImageManager()
        if self.image:
            return Markup('<a href="' + url_for('PredictImageModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="' + im.get_url(self.image) +\
              '" alt="Photo" class="img-rounded img-responsive"></a>')
        else:
            return Markup('<a href="' + url_for('PredictImageModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')

    def photo_img_thumbnail(self):
        im = ImageManager()
        if self.image:
            return Markup('<a href="' + url_for('PredictImageModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="' + im.get_url_thumbnail(self.image) +\
              '" alt="Photo" class="img-rounded img-responsive"></a>')
        else:
            return Markup('<a href="' + url_for('PredictImageModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')

class PredictRecord(Model):
    __tablename__ = "predict_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    file = Column(FileColumn, nullable=False)

    def __repr__(self):
        return self.name

    def file_name(self):
        return get_file_original_name(str(self.file))