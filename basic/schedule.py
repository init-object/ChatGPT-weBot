# -*- coding: utf-8 -*-

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from basic.task import NormalTask, ScheduleTask
from multithread.threads import sche_que

scheduler_dict = dict()

def doSchedule(scheduleTask):
    sche_que.put(scheduleTask)

def addScheduleTask(scheduleTask=ScheduleTask):
    if scheduleTask.reply is None or scheduleTask.reply.isspace():
        scheduleTask.reply = "请设置定时任务发送内容"
        sche_que.put(scheduleTask)
        return
    if scheduleTask.cron is None or scheduleTask.cron.isspace():
        scheduleTask.reply = "请设置定时任务cron表达式"
        sche_que.put(scheduleTask)
        return
    job_id = scheduleTask.wx_id
    if scheduleTask.is_room:
        job_id += scheduleTask.room_id
        scheduler_dict[(scheduleTask.wx_id, scheduleTask.room_id)] = scheduleTask
    else:
        scheduler_dict[(scheduleTask.wx_id, "")] = scheduleTask

    job_tip = "定时任务新增成功"
    if scheduler.get_job(job_id=job_id):
        scheduler.remove_job(job_id=job_id)
        job_tip = "定时任务覆盖成功 旧定时任务被覆盖"
    scheduler.add_job(func=doSchedule, trigger=CronTrigger.from_crontab(scheduleTask.cron), args=[scheduleTask], id=job_id)
    return job_tip

def removeScheduleTask(is_room, wx_id, room_id):
    task: ScheduleTask
    job_id = wx_id
    if is_room:
        job_id += room_id
        if (wx_id, room_id) in scheduler_dict:
            task = scheduler_dict.pop((wx_id, room_id))
        else:
            return "任务不存在或已取消"
    else:
        if (wx_id, "") in scheduler_dict:
            task = scheduler_dict.pop((wx_id, ""))
        else:
            return "任务不存在或已取消"
    if scheduler.get_job(job_id=job_id):
        scheduler.remove_job(job_id=job_id)
    return task.content


scheduler = BackgroundScheduler()
scheduler.start()
