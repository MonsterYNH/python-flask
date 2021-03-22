from flask import render_template, redirect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.actions import action
from flask_appbuilder import ModelView, BaseView, expose
from flask_appbuilder.api import ModelRestApi
from sqlalchemy.sql import func
import json
import pandas as pd
import numpy as np
import keras

from . import appbuilder, db
from .models import Data, File, Tag, Predict, PredictFile, PredictType, PredictImage, PredictRecord

class DataModelView(ModelView):
    datamodel = SQLAInterface(Data)
    label_columns = {
        "title": "指标名",
        "tag_source": "标签名",
        "tag_name": "展示名",
        "tag_value": "标签值",
        "file_name": "文件名"
    }
    base_permissions = ['can_show', 'can_list']
    list_columns = ['title', 'tag_source', 'tag_name','tag_value', 'file_name']


class DataChartView(BaseView):
    route_base = "/datachart"
    @expose('/datas/')
    def datas(self):
        files = db.session().query(File).all()
        result = []
        for file in files:
            tags = db.session().query(Tag).filter_by(file_id=file.id).order_by(Tag.order).all()
            result.append({
                'file_name': file.file_name(),
                'title': file.title,
                'tag_names': [tag.get_tag_name() for tag in tags],
                'tag_values': [tag.data.tag_value for tag in tags],
                'tag_name_values': [{'name': tag.get_tag_name(), 'value': tag.data.tag_value} for tag in tags]
            })
        return {
            "data": result
        }

    @expose("/")
    def chart(self):
        return self.render_template('data_charts.html')

class TagModelView(ModelView):
    datamodel = SQLAInterface(Tag)

    label_columns = {
        "tag_source": "标签名",
        "tag_name": "展示名",
        "file_name": "文件名",
        "order": "排序"
    }
    edit_columns = ["tag_source", "tag_name", "order"]
    list_columns = ['file_name', 'tag_source','tag_name', 'order']
    base_permissions = ['can_show', 'can_list', 'can_edit']



class FileModelView(ModelView):
    datamodel = SQLAInterface(File)
    related_views = [DataModelView]

    add_columns = ["file"]

    label_columns = {
        "file_name": "文件名",
        "title": "名称",
        "is_load": "是否加载",
        "download": "下载",
    }

    list_columns = ["file_name", "title", "is_load", "download"]

    @action("load_data", "加载数据", "确认加载?")
    def load_data(self, items):
        for item in items:
            item.is_load = True
            item.title = self.parse_file(item.id, self.appbuilder.app.config['UPLOAD_FOLDER']+item.file, item.file)
            self.datamodel.edit(item)
        self.update_redirect()
        return redirect(self.get_redirect())

    @action("delete_with_data", "删除文件及其数据", "确认删除?")
    def delete_with_data(self, items):
        file_ids = [item.id for item in items]
        print(file_ids)
        tags = db.session().query(Tag).filter(Tag.file_id.in_(file_ids)).all()
        tag_ids = [tag.id for tag in tags]
        datas = db.session().query(Data).filter(Data.tag_id.in_(tag_ids))
        session = db.session()
        try:
            # delete data
            for data in datas:
                session.delete(data)
            # delete tag
            for tag in tags:
                session.delete(tag)
            # delete file
            for item in items:
                session.delete(item)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
        
        
        self.update_redirect()
        return redirect(self.get_redirect())

    def parse_file(self, file_id, path, file_name):
        data = pd.read_csv(path, header=0)
        title = data.columns.values[0]
        values = data[title].value_counts()
        session = db.session()
        try:
            for tag_source, tag_value in values.iteritems():
                tag_source = str(tag_source)
                tag = session.query(Tag).filter_by(file_id=file_id, tag_source=tag_source).first()
                if tag is None:
                    count = session.query(Tag).filter_by(file_id=file_id).count()
                    session.add(Tag(file_id, tag_source, count+1))
                    tag = session.query(Tag).filter_by(file_id=file_id, tag_source=tag_source).first()
                session.add(Data(tag.id, tag_value))
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close() 
        return title

class PredictFileModelView(ModelView):
    datamodel = SQLAInterface(PredictFile)

    label_columns = {
        'name': '模型名',
        'file': '模型文件',
        'file_name': '模型文件',
    }

    add_columns = ['name', 'file']

    list_columns = ['name', 'file_name']

class PredictTypeModelView(ModelView):
    datamodel = SQLAInterface(PredictType)

    label_columns = {
        'name': '类型名',
        'source_name': '原始名',
    }

    add_columns = ['name', 'source_name', 'predict_image']

    list_columns = ['name', 'source_name', 'photo_name', 'photo_img']

class PredictImageModelView(ModelView):
    datamodel = SQLAInterface(PredictImage)

    label_columns = {
        "photo_img": "图像",
        "name": "图像名",
        "image": "图像"
    }

    add_columns = ['name', 'image']

    list_columns = ['name', 'photo_img']

class PredictModelView(ModelView):
    datamodel = SQLAInterface(Predict)

    add_columns = ['file', 'predict_record']

    label_columns = {
        'file': '模型文件',
        'file_id': '模型文件',
        'file_name': '模型文件',
        'predict_name': '模型名',
        'predict_value': '预测值',
        'predict_type_name': '预测名',
        'predict_image': '预测图像',
        'predict_record_name': '数据',
        'predict_record_file_name': '数据文件',
        'predict_record': '数据文件',
    }

    list_columns = ['predict_name', 'file_name', 'predict_record_file_name', 'predict_value', 'predict_type_name', 'predict_image']

    related_views = [PredictFileModelView, PredictTypeModelView]

    @action("predict", "执行预测", "确认执行预测?")
    def predict(self, items):
        for item in items:
            self.predict_one(item)
        self.update_redirect()
        return redirect(self.get_redirect())

    def predict_one(self, item):
        # 加载模型
        model_m = keras.models.load_model(self.appbuilder.app.config['UPLOAD_FOLDER']+item.file.file)
        # 读取测试数据
        x_test = np.loadtxt(self.appbuilder.app.config['UPLOAD_FOLDER']+item.predict_record.file)
        input_shape = 240
        predict = model_m.predict(x_test)
        test_record = x_test.reshape(1, input_shape)
        # 预测的活动类型，但是输出值为整数
        prediction = np.argmax(model_m.predict(test_record), axis=1)

        predict_type = db.session().query(PredictType).filter_by(source_name=str(prediction)).first()
        if predict_type:
            item.predict_type_id = predict_type.id
            item.predict_value = prediction
            self.datamodel.edit(item)


class PredictRecordModelView(ModelView):
    datamodel = SQLAInterface(PredictRecord)

    label_columns = {
        'name': '名称',
        'file': '文件',
    }

    add_columns = ['name', 'file']

    list_columns = ['name', 'file']



"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()

appbuilder.add_view(
    DataModelView,
    "原始数据",
    category = "数据"
)

appbuilder.add_view(
    TagModelView,
    "数据标签",
    category="数据"
)

appbuilder.add_view(
    DataChartView,
    "图表",
    href="/datachart",
    category = "数据",
)

appbuilder.add_view(
    FileModelView,
    "数据文件",
    category="数据"
)

appbuilder.add_view(
    PredictModelView,
    "预测结果",
    category="预测"
)

appbuilder.add_view(
    PredictFileModelView,
    "预测模型",
    category="预测"
)

appbuilder.add_view(
    PredictTypeModelView,
    "预测类型",
    category="预测"
)

appbuilder.add_view(
    PredictImageModelView,
    "预测图像",
    category="预测"
)

appbuilder.add_view(
    PredictRecordModelView,
    "数据",
    category="预测"
)