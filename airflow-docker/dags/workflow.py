# pylint: disable=missing-function-docstring

# [START import_module]
import json
import pandas as pd
import os
import pyarrow
import requests
from google.cloud import bigquery


from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator

# [END import_module]

# [START default_args]
# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args = {
    'owner': 'airflow',
}
# [END default_args]


# [START instantiate_dag]
@dag(dag_id="data_ops",
    description="ETL orchestration",
    default_args=default_args, 
    schedule_interval='@daily', 
    start_date=days_ago(2),
     tags=['example'])

def _api_etl():
    """
    ### ETL
    This is a simple ETL data pipeline using three simple tasks for Extract, Transform, and Load.
    It extracts the data from an API (request), Transforms the data into a Pandas dataframe,
    and then loads the data to Google Big Query 
    """
    # [END instantiate_dag]

    # [START extract]
    @task()
    def extract():
        """
        #### Extract task
        A simple Extract task to get data ready for the rest of the data
        pipeline. In this case, we get the data from the citybik API.
        """
        base_url = 'https://api.citybik.es/v2/networks/bicing'
        response = requests.get(base_url)

        if response.status_code == 200:
            bike_data_json = response.json() 
            return bike_data_json  # returns the response in JSON format
        else:
            return f"Error: {response.status_code}"

    # [END extract]

    # [START transform]
    @task(multiple_outputs=False)
    def transform(bike_data_json: json) -> pd.DataFrame:
        """
        #### Transform task
        A simple Transform task which takes in the collection of bicing station data and
        mostly cleans the data.
        """
        df = pd.json_normalize(bike_data_json['network']['stations'])
        df['id'] = df['id'].apply(lambda row: str(row))
        df['name'] = df['name'].apply(lambda row: str(row))
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        df.rename(columns=lambda x: x.replace("extra.", ""), inplace=True)

        return df

    # [END transform]

    # [START load]
    @task()
    def load(df: pd.DataFrame):
        """
        #### Load task
        A simple Load task which takes in the result of the Transform task and
        we load it to Google Big Query using our service account.
        """
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/opt/airflow/bicing_Gcloud_service.json'

        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bicing_Gcloud_service.json'
        client = bigquery.Client()
        table_id = "bicingml.bicing.descriptors"
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,  # or WRITE_TRUNCATE to overwrite
            autodetect=True  # Autodetects schema if set to True
        )
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)

        print("Success")

    # [END load]

    # [START main_flow]
    bicing_data = extract()
    df_transformed = transform(bicing_data)
    load(df_transformed)
    # [END main_flow]


# [START dag_invocation]
etl_dag = _api_etl()
# [END dag_invocation]

# [END airflow task]