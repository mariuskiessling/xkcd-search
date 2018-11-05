from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.hive_operator import HiveOperator
from airflow.operators.mysql_operator import MySqlOperator 
from airflow.operators.hive_to_mysql import HiveToMySqlTransfer
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

dag = DAG(
    'xkcd_search', default_args=default_args, schedule_interval=None)


downloadComics = BashOperator(
    task_id='stage1_download_comics',
    bash_command='python3 /home/hadoop/xkcd-search/crawler/crawler.py /home/hadoop/xkcd-search/raw',
    dag=dag)

createHdfsBase = BashOperator(
    task_id='stage1_create_hdfs_base',
    bash_command='hadoop fs -mkdir -p /user/hadoop/xkcd-search/; hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw',
    dag=dag)

createRunDateDirCmd = """
hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw/\
{{ execution_date.year }}
hadoop fs -mkdir -p /user/hadoop/xkcd-search/raw/\
{{ execution_date.year }}/\
{{ execution_date.day }}
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
    dag=dag)

dropHiveDatabase = HiveOperator(
    task_id='stage2_drop_hive_db',
    hql='DROP TABLE IF EXISTS xkcd_search;',
    hive_cli_conn_id='beeline_default',
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
    hive_cli_conn_id='beeline_default',
    dag=dag)

dropMysqlDatabase = MySqlOperator(
    task_id='stage3_drop_mysql_schema',
    mysql_conn_id='mysql_default',
    sql='DROP TABLE IF EXISTS comics',
    database='xkcd_search',
    dag=dag)

createMysqlSchema = MySqlOperator(
    task_id='stage3_create_mysql_schema',
    mysql_conn_id='mysql_default',
    sql="""
        CREATE TABLE comics (
        month int(11) DEFAULT NULL,
        num int(11) NOT NULL,
        link varchar(256) DEFAULT '',
        year int(11) NOT NULL,
        news text,
        save_title text,
        transcript text,
        alt text,
        img varchar(256) DEFAULT NULL,
        title text,
        day int(11) DEFAULT NULL,
        PRIMARY KEY (num),
        FULLTEXT KEY title (title,save_title,alt,transcript)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """,
    database='xkcd_search',
    dag=dag)

migrateToEndUserDB = HiveToMySqlTransfer(
    task_id='stage3_migrate_to_end_user_db',
    sql='SELECT * FROM xkcd_search',
    mysql_table='xkcd_search.comics',
    mysql_conn_id='mysql_default',
    hiveserver2_conn_id='hiveserver2_default',
    dag=dag)


createHdfsBase.set_upstream(downloadComics)
createRunDateDir.set_upstream(createHdfsBase)
placeComicFile.set_upstream(createRunDateDir)
dropHiveDatabase.set_upstream(placeComicFile)
createHiveSchema.set_upstream(dropHiveDatabase)
dropMysqlDatabase.set_upstream(createHiveSchema)
createMysqlSchema.set_upstream(dropMysqlDatabase)
migrateToEndUserDB.set_upstream(createMysqlSchema)
