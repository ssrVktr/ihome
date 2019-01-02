from ihome.tasks import config
from celery import Celery


celery_app = Celery('ihome')
celery_app.config_from_object(config)
# 自动搜寻异步任务
celery_app.autodiscover_tasks(['ihome.tasks.sms'])
