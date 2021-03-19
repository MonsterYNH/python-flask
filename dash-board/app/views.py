from flask import render_template, redirect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.actions import action
from flask_appbuilder import ModelView, BaseView, expose
from flask_appbuilder.api import ModelRestApi
from sqlalchemy.sql import func
import json
import pandas as pd

from . import appbuilder, db
from .models import Data, File, Tag

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
