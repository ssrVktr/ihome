from ihome.tasks.main import celery_app
from ihome.libs.yuntongxun.sms import CCP


# 发送注册短信
@celery_app.task
def send_sms(mobile, dates, temp_id):
    ccp = CCP()
    try:
        result = ccp.send_template_sms(mobile, dates, temp_id)
    except Exception:
        result = -2
    return result
