from datetime import datetime

from crontab import CronTab
from django.conf import settings
from .script import MongoDatabases


class CronJobs:
    PROJECT_PATH = settings.BASE_DIR

    def list_cronjob(self):
        try:
            cron = CronTab()
            cron_list = []
            for obj in cron.crons:
                cron_obj = {}
                cron_name = obj.comment.split(' ')
                cron_obj['cron_type'] = cron_name[0]
                cron_obj['cron_function'] = cron_name[1]
                cron_obj['cron_time'] = cron_name[3]
                cron_list.append(cron_obj)
            return cron_list
        except Exception as ex:
            print(f'Error in Cronjob Listing: {ex}')
            return []

    def create_cronjob(self, _time, cron_type, script_name):
        """
        Each asterisk represents a time parameter:
         a. Minute (0-59)
         b. Hour (0-23)
         c. Day of the month (1-31)
         d. Month (1-12)
         e. Day of the week (0-7, where both 0 and 7 represent Sunday)
        """

        hours, minutes = _time.split(':')

        cron_type_dict = {
            'daily': f'{minutes} {hours} * * *',
            'weekly': f'{minutes} {hours} * * 0',  # runs every Sunday
            'monthly': f'{minutes} {hours} 1 * *',  # runs at 1st of every month
            'yearly': f'{minutes} {hours} 1 1 *'  # runs at 1st day of 1st month
        }

        # assign values
        interval = cron_type.title()
        schedule_time = f'{script_name.title()} at {_time}'
        created_at = datetime.now()

        # Create a new cron tab object
        cron = CronTab()

        # Create a new cron job with a shell script command and unique comment
        job = cron.new(command=f'cd {self.PROJECT_PATH}  && ./{script_name}.sh',
                       comment=f'{interval} {schedule_time} => initiated at {created_at}')

        # Set the desired schedule for the cron job
        job.setall(cron_type_dict.get(cron_type))  # Example: Runs according to schedule

        # Add the cron job to the cron tab
        cron.write()

        # insert nto db
        db_script = MongoDatabases()
        db_script.insert_cronjob_in_db(job.comment, created_at, _time, interval)
