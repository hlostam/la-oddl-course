import logging
import logging.config

import shutil
import urllib.request
from pathlib import Path
from genericpath import isfile
import zipfile
# import click
import hashlib
import pickle

import numpy as np
import pandas as pd
from dotenv import find_dotenv, load_dotenv

# from log_config import LOGGING
# logging.config.dictConfig(LOGGING)
# logger = logging.getLogger(__name__)

OULAD_URL = 'https://analyse.kmi.open.ac.uk/open_dataset/download'
OULAD_MD5_URL = 'https://analyse.kmi.open.ac.uk/open_dataset/downloadCheckSum'
DS_ASSESSMENTS = 'assessments'
DS_COURSES = 'courses'
DS_STUD_ASSESSMENTS = 'studentAssessment'
DS_STUD_INFO = 'studentInfo'
DS_STUD_REG = 'studentRegistration'
DS_STUD_VLE = 'studentVle'
DS_VLE = 'vle'
DS_ARRAY = [DS_ASSESSMENTS, DS_COURSES, DS_STUD_ASSESSMENTS, DS_STUD_INFO,
            DS_STUD_REG, DS_STUD_VLE, DS_VLE]


def check_oulad_md5(filepath: str):
    with urllib.request.urlopen(OULAD_MD5_URL) as response:
        data = response.read()
        md5_zip_desired = data.decode('UTF-8')
        logging.debug("Desired MD4: %s", md5_zip_desired)
    md5_zip_real = ""
    if isfile(filepath):
        hasher = hashlib.md5()
        with open(filepath, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)
        md5_zip_real = hasher.hexdigest()
        logging.debug("Real MD5: %s", md5_zip_real)
    return md5_zip_desired == md5_zip_real


def download_oulad_dataset(output_filepath: str):
    with urllib.request.urlopen(OULAD_URL) as response, open(output_filepath, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    if not check_oulad_md5(output_filepath):
        raise Exception('MD5 checksum of %s after download doesnt match the desired one',
                        output_filepath)


def download_and_extract(output_path):
    zip_filepath = output_path/'oulad.zip'
    if not isfile(zip_filepath):
        logging.info('Downloading %s ...', zip_filepath)
        download_oulad_dataset(zip_filepath)
    else:
        logging.info('Already downloaded %s', zip_filepath)
    if not isfile(output_path / 'studentAssessment.csv'):
        archive = zipfile.ZipFile(zip_filepath, 'r')
        logging.debug("Extracting zip")
        archive.extractall(output_path)


def read_all_csv_to_feather(csv_path):
    logging.debug("Reading all csvs..")
    REQUIRED_OULAD_CSV_NUM = 7
    successfully_read = 0
    df_all = dict()
    for ds in DS_ARRAY:
        df = read_csv_and_store_to_feather(csv_path, ds)
        if df is not None:
            successfully_read += 1
            df_all[ds] = df
    logging.debug("Read: %s/%s", successfully_read, REQUIRED_OULAD_CSV_NUM)
    if successfully_read != REQUIRED_OULAD_CSV_NUM:
        logging.error("Some files CSV were not loaded.")
        raise IOError("Some files CSV were not loaded.")
    with open(csv_path / 'oulad.pickle', 'wb') as handle:
        pickle.dump(df_all, handle, protocol=pickle.HIGHEST_PROTOCOL)


def read_csv_and_store_to_feather(csv_path, ds):
    f = ".".join([ds, 'csv'])
    logging.debug("Reading: %s ", str(f))
    abs_path = csv_path / f
    if isfile(abs_path):
        df = pd.read_csv(abs_path)
        df = preprocess(df, ds)
        return df
    else:
        return None


def preprocess(df, ds):
    if ds == DS_ASSESSMENTS:
        df = df.set_index(['code_module', 'code_presentation'])
        df = df.sort_values(by='date')
        df_agg = df.groupby(['code_module', 'code_presentation', 'assessment_type'])
        # Assign each row the order within the group MOD-PRES-TYPE
        df['assessment_name'] = df['assessment_type'] + " " + (df_agg.cumcount() + 1).map(str)
        df.loc[df['assessment_name'] == 'Exam 1', 'assessment_name'] = 'Exam'
    elif ds == DS_COURSES:
        df = df.set_index(['code_module', 'code_presentation'])
    elif ds == DS_VLE:
        df = df.set_index(['code_module', 'code_presentation'])
    elif ds == DS_STUD_INFO:
        df = df.set_index(['code_module', 'code_presentation'])
    elif ds == DS_STUD_REG:
        df = df.set_index(['code_module', 'code_presentation'])
    elif ds == DS_STUD_ASSESSMENTS:
        df = df.set_index(['id_assessment'])
    elif ds == DS_STUD_VLE:
        df = df.set_index(['code_module', 'code_presentation'])
    else:
        df = df
    return df


# Load from preprocessed pickle - when it is already downloaded
def load_oulad(verbose=True, pickle_path='../data/raw'):
    # oulad_pickle = r'C:\Users\martin.hlosta\code\srl-features\data\raw\oulad.pickle'
    # oulad_pickle = get_basepath()/'code'/'srl-features'/'data'/'raw'/'oulad.pickle'
    # print(oulad_pickle)
    pickle_file_name = 'oulad.pickle'
    # pickle_path = '../data/raw'
    oulad_pickle = f'{pickle_path}/{pickle_file_name}'
    with open(oulad_pickle, 'rb') as handle:
        dfs_all = pickle.load(handle)
    if verbose:
        keys = [k for k, v in dfs_all.items()]
        print(keys)
    return dfs_all


def imd_to_continuous(series):
    imd_mapping = {
      '0-10%': 0.05,
      '10-20': 0.15,
      '20-30%': 0.25,
      '30-40%': 0.35,
      '40-50%': 0.45,
      '50-60%': 0.55,
      '60-70%': 0.65,
      '70-80%': 0.75,
      '80-90%': 0.85,
      '90-100%': 0.95,
      #   None: np.nan
      }
    return series.map(imd_mapping).fillna(np.nan)


def band_imd_quintiles(series):
    imd_mapping = {
        '0-10%': 'Q1',
        '10-20': 'Q1',
        '20-30%': 'Q2',
        '30-40%': 'Q2',
        '40-50%': 'Q3',
        '50-60%': 'Q3',
        '60-70%': 'Q4',
        '70-80%': 'Q4',
        '80-90%': 'Q5',
        '90-100%': 'Q5',
        # None: 'INT'
        }
    return series.map(imd_mapping).fillna('INT')


def band_imd_quintiles_2(series):
    imd_mapping = {
        '0-10%': 'Q1_Q2',
        '10-20': 'Q1_Q2',
        '20-30%': 'Q1_Q2',
        '30-40%': 'Q1_Q2',
        '40-50%': 'Q3',
        '50-60%': 'Q3',
        '60-70%': 'Q4_Q5',
        '70-80%': 'Q4_Q5',
        '80-90%': 'Q4_Q5',
        '90-100%': 'Q4_Q5',
        # None: 'INT'
        }
    return series.map(imd_mapping).fillna('INT')


def band_imd_terciles(series):
    imd_mapping = {
        '0-10%': 'T1',
        '10-20': 'T1',
        '20-30%': 'T1',
        '30-40%': 'T2',
        '40-50%': 'T2',
        '50-60%': 'T2',
        '60-70%': 'T2',
        '70-80%': 'T3',
        '80-90%': 'T3',
        '90-100%': 'T3',
        # None: 'INT'
        }
    return series.map(imd_mapping).fillna('INT')


def preprocess_oulad(dfs_all, verbose=True):
    dfs_all[DS_STUD_ASSESSMENTS] = (
        dfs_all[DS_STUD_ASSESSMENTS]
        .reset_index()
        .merge(dfs_all[DS_ASSESSMENTS][['id_assessment']].reset_index(),
               on=['id_assessment'])
        .set_index(['code_module', 'code_presentation', 'id_assessment'])
        )
    dfs_all[DS_ASSESSMENTS]['week'] = np.floor(dfs_all[DS_ASSESSMENTS]['date'] / 7)

    dfs_all[DS_STUD_INFO]['imd'] = band_imd_quintiles(dfs_all[DS_STUD_INFO].imd_band)
    dfs_all[DS_STUD_INFO]['imd_2'] = band_imd_quintiles_2(dfs_all[DS_STUD_INFO].imd_band)
    dfs_all[DS_STUD_INFO]['imd_3'] = band_imd_terciles(dfs_all[DS_STUD_INFO].imd_band)
    dfs_all[DS_STUD_VLE]['week'] = np.floor(dfs_all[DS_STUD_VLE]['date'] / 7)
    dfs_all[DS_STUD_VLE]['weekday'] = np.mod(dfs_all[DS_STUD_VLE]['date'], 7)

    return dfs_all


# @click.command()
# @click.argument('input_filepath', type=click.Path(exists=True))
# @click.argument('output_filepath', type=click.Path())
def main():
    project_dir = Path(__file__).resolve().parents[2]

    output_path = project_dir / 'data' / 'raw'
    download_and_extract(output_path)
    read_all_csv_to_feather(output_path)


if __name__ == '__main__':
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    # load_dotenv(find_dotenv())

    main()
