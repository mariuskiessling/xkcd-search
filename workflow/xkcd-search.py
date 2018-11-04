from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.hive_operator import HiveOperator
import datetime

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['vcs@mariuskiessling.de'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
    'start_date': datetime.datetime.utcnow(),
}

runDate = datetime.datetime.now()

dag = DAG(
    'xkcd_search', default_args=default_args, schedule_interval=None)


#downloadComics = BashOperator(
#    task_id='stage1_download_comics',
#    bash_command='python3 /home/hadoop/xkcd-search/crawler/crawler.py /home/hadoop/xkcd-search/raw',
#    dag=dag)

createHdfsBase = BashOperator(
    task_id='stage1_create_hdfs_base',
    bash_command='hadoop fs -mkdir -p /user/hadoop/xkcd-search/; hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw',
    dag=dag)

createRunDateDirCmd = """
hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw/\
{{ execution_date.year }}
hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw/\
{{ execution_date.year }}/\
{{ params.runDate.day }}
hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw/\
{{ execution_date.year }}/\
{{ execution_date.day }}/\
{{ execution_date.month }}
hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw/\
{{ execution_date.year }}/\
{{ execution_date.day }}/\
{{ execution_date.month }}/\
{{ execution_date.hour }}-\
{{ execution_date.minute }}-\
{{ execution_date.second }}
"""

createRunDateDir = BashOperator(
    task_id='stage1_create_run_date_dir',
    bash_command=createRunDateDirCmd,
    params={'runDate': runDate},
    dag=dag)

placeComicFileCmd = """
hadoop fs -put /home/hadoop/xkcd-search/raw/xkcd.json \
/user/hadoop/xkcd-search/raw/\
{{ execution_date.year }}/\
{{ execution_date.day }}/\
{{ execution_date.month }}/\
{{ execution_date.hour }}-\
{{ execution_date.minute }}-\
{{ execution_date.second }}/
"""

placeComicFile = BashOperator(
    task_id='stage1_place_comic_file',
    bash_command=placeComicFileCmd,
    params={'runDate': runDate},
    dag=dag)

dropHiveDatabase = HiveOperator(
    task_id='stage2_drop_hive_db',
    hql='DROP TABLE IF EXISTS xkcd_search;',
    hive_cli_conn_id='hive_cli_default',
    dag=dag)

createHiveSchema = HiveOperator(
    task_id='stage2_create_hive_schema',
    hql="""
        CREATE EXTERNAL TABLE IF NOT EXISTS xkcd_search(
        month INT,
        num INT,
        link STRING,
        year INT,
        news STRING,
        safe_title STRING,
        transcript STRING,
        alt STRING,
        img STRING,
        title STRING,
        day int)
        COMMENT 'XKCD comics'
        ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
        STORED AS TEXTFILE LOCATION '/user/hadoop/xkcd-search/raw/{{ execution_date.year }}/{{ execution_date.day }}/{{ execution_date.month }}/{{ execution_date.hour }}-{{ execution_date.minute }}-{{ execution_date.second }}';
        """,
    hive_cli_conn_id='hive_cli_default',
    dag=dag)

createRunDateDir.set_upstream(createHdfsBase)
placeComicFile.set_upstream(createRunDateDir)
dropHiveDatabase.set_upstream(placeComicFile)
createHiveSchema.set_upstream(dropHiveDatabase)
