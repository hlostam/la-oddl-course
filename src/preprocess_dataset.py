import numpy as np
import pandas as pd

# ###############################################################################################
DS_ASSESSMENTS = 'assessments'
DS_COURSES = 'courses'
DS_STUD_ASSESSMENTS = 'studentAssessment'
DS_STUD_INFO = 'studentInfo'
DS_STUD_REG = 'studentRegistration'
DS_STUD_VLE = 'studentVle'
DS_VLE = 'vle'

DS_ARRAY = [DS_ASSESSMENTS, DS_COURSES, DS_STUD_ASSESSMENTS, DS_STUD_INFO,
            DS_STUD_REG, DS_STUD_VLE, DS_VLE]

# ###############################################################################################
# Generalisable
# ###############################################################################################
# 1. Filtering

# Filtering by modpres


# def filter_modpres(dfs_all,module, presentation):
#     df_assessments = dfs_all[DS_ASSESSMENTS].sort_index()
#     dfs = {
#             DS_COURSES: dfs_all[DS_COURSES].loc[module, presentation],
#             DS_ASSESSMENTS: df_assessments.loc[module, presentation],
#             DS_VLE: dfs_all[DS_VLE].loc[module, presentation],
#             DS_STUD_INFO: dfs_all[DS_STUD_INFO].loc[module, presentation],
#             DS_STUD_ASSESSMENTS: dfs_all[DS_STUD_ASSESSMENTS].loc[module, presentation],
#             DS_STUD_REG: dfs_all[DS_STUD_REG].loc[module, presentation],
#             DS_STUD_VLE: dfs_all[DS_STUD_VLE].loc[module, presentation]
#         }
#     return dfs


def remove_wrong_registrations(df, max_registration_day=10, min_unregistration_day=0):
    # if NA -> exclude
    df = df[~df.date_registration.isna()]

    # exclude early dropout: if not NA but UNregistered before start of the course
    df = df[~(df.date_unregistration < min_unregistration_day)]

    # Exclude LATE registered: if not NA but registered after day10
    df = df[~(df.date_registration > max_registration_day)]

    return df


def no_weighted_assessment_as_withdrawn(df):
    # removing = df.loc[lambda df_: ((df_.ocas == 0) & (df_.final_result != 'Withdrawn'))]
    len_bef = len(df)
    df = df.loc[lambda df_: ~((df_.num_submitted < 1) & (df_.final_result == 'Pass'))]
    print(f"Removed: {len_bef} -> {len(df)}")
    # df.loc[lambda df_: ((df_.sum_score == 0) & (df_.final_result != 'Withdrawn')), 'final_result_2'] = 'Withdrawn'
    # df.loc[lambda df_: ((df_.sum_score == 0) & (df_.final_result != 'Withdrawn')), 'final_result'] = 'Withdrawn'
    # print(f"Removing OCAS=0 & not Withdrawn: {len(removing)}")
    # print(f"{removing.groupby('code_module').size()}")
    return df


def filter_student_no_weighted_assessment(df):
    ''' Removes students that have no weighted assessment graded and are still not withdrawn.
    How could these students achieved a grade?

    Requires a dataframe with the ocas column (Overall Continuing Assessment Score)
    '''
    removing = df.loc[lambda df_: ((df_.ocas == 0) & (df_.final_result != 'Withdrawn'))]
    print(f"Removing OCAS=0 & not Withdrawn: {len(removing)}")
    print(f"{removing.groupby('code_module').size()}")
    return df.loc[lambda df_: ~((df_.ocas == 0) & (df_.final_result != 'Withdrawn'))]


def get_first_assessment(df_assessments):
    mindate = (df_assessments.groupby(['code_module', 'code_presentation'])
               ['date']
               .min())
    return (df_assessments
            .reset_index()
            .merge(mindate, on=['code_module', 'code_presentation', 'date'])
            .set_index(['code_module', 'code_presentation'])['assessment_name']
            .rename('first_assessment')
            # .reset_index()
            )

# ###############################################################################################
# 2. Extending data
# ###############################################################################################


def extend_by_final_result_ext(df: pd.DataFrame):
    df = (df
          .assign(final_result_2=lambda df_: df_.final_result)
          # .assign(final_result_2 = lambda df_: pd.Series(dtype='object')
          #     .where((df_['final_result'] != 'Withdrawn') | (df_['date_unregistration'].isna()), 'Withdrawn')
          #     .where((df_['final_result'] == 'Withdrawn') & (df_['date_unregistration'] > df_['date']), 'Withdrawn_Before')
          #     .where((df_['final_result'] == 'Withdrawn') & (df_['date_unregistration'] <= df_['date']), 'Withdrawn')
          # )
          )

    df.loc[lambda df_: (df_.final_result == 'Withdrawn')
           & (df_.date_unregistration > df_.date), 'final_result_2'] = 'Withdrawn'

    # Withdrawn_Before = before TMA cutoff
    df.loc[lambda df_: (df_.final_result == 'Withdrawn') &
                       (df_.date_unregistration <= df_.date) &
           # if submit ahead and then unregister -> considered after TMA
           # ((df_.date_unregistration <= df_.date_submitted) | (df_.date_submitted.isna()))
           # only if not submitted its withdrawn, if submitted cannot be withdrawn_before
                       ((df_.date_submitted.isna())),
           'final_result_2'] = 'Withdrawn_Before'

    # stud_tma1.loc[lambda df_: (df_.final_result == 'Withdrawn')
    # & (df_.date_unregistration.isna()),'final_result_2'] = 'Withdrawn_NA'
    df.loc[lambda df_: (df_.final_result == 'Withdrawn') & (df_.date_unregistration.isna()),
           'final_result_2'] = 'Withdrawn'
    return df


def special_ns_withdrawn_before_deadline(df: pd.DataFrame):
    return (df
            .assign(score_banded_ns_f_p=lambda df_: np.where(
                df_.final_result_2 == 'Withdrawn_Before',
                df_.score_banded_ns_f_p + '_Withdrawn_Before',
                df_.score_banded_ns_f_p))
            )


def compute_ocas(stud_ass, ass):
    stud_ass = (stud_ass.reset_index().merge(ass, on=['id_assessment'])
                )

    ass_sums = (ass
                .loc[lambda df_: df_.assessment_type != 'Exam']
                .groupby(['code_module', 'code_presentation']).weight.sum()
                )
    # print(ass_sums)
    ocas = (stud_ass
            .loc[lambda df_: df_.assessment_type != 'Exam']
            .assign(weighted_score=lambda df_: df_.score * df_.weight)
            .groupby(['id_student', 'code_module', 'code_presentation'])
            .agg(
                ocas=pd.NamedAgg(column='weighted_score', aggfunc="sum"),
                sum_score=pd.NamedAgg(column='score', aggfunc="sum"),
                num_submitted=pd.NamedAgg(column='weighted_score', aggfunc='size'),
                num_banked=pd.NamedAgg(column='is_banked', aggfunc='sum')
            )
            .assign(ocas_rel=lambda df_: df_.ocas.div(ass_sums))
            .reset_index()
            )
    return ocas


def compute_pass_rate(df):
    '''needs to have registration AND final results information'''
    return (df
            .pipe(extend_by_final_result_ext)
            .loc[lambda df_: df_.final_result_2 != 'NS_Withdrawn_Before', ]
            .assign(is_pass=lambda df_: df_.final_result_2.isin(['Pass', 'Distinction']))
            .groupby(['code_module'])['is_pass']
            .mean()
            .rename('pass_rate')
            )


# Banding
# Assessments  / TMAs


def band_assessment_score(series, fail_band=50):
    if series < fail_band:
        return 'Fail'
    elif pd.isna(series):
        return 'NS'
    else:
        return 'Pass'


def band_assessment_scores(series, fail_band=50):
    condition = (series < fail_band)
    result = np.where(condition, 'Fail', np.where(series.isna(), 'NS', 'Pass'))
    return pd.Series(result, index=series.index)


def band_assessment_scores2(series, fail_band=50):
    condition = (series < fail_band)
    result = np.where(condition, 'NS_Fail', np.where(series.isna(), 'NS_Fail', 'Pass'))
    return pd.Series(result, index=series.index)


def band_tma_score_2(series):
    band_score_2 = {
            "Pass": "Pass",
            "Fail": "Fail_NS",
            "NS": "Fail_NS",
    }
    return series.map(band_score_2)


def band_tma_score_submssion(series):
    band_score_submit = {
            "Pass": "Submit",
            "Fail": "Submit",
            "NS": "NS",
    }
    return series.map(band_score_submit)


def band_ocas_by_median(df, ocas_column='ocas_rel', filter_withdrawn=True):
    if filter_withdrawn:
        df_filter = (df
                     .loc[lambda df_: df_.final_result_2 != 'NS_Withdrawn_Before', ]
                     .loc[lambda df_: df_.final_result_2 != 'Withdrawn', ]
                     )
    else:
        df_filter = df
    med_score = (df_filter
                 [['code_module', 'code_presentation', ocas_column]]
                 .dropna()
                 .groupby(['code_module', 'code_presentation'])
                 [ocas_column]
                 .median()
                 .rename('modpres_median_score')
                 .reset_index()
                 )
    # med_score
    # print(med_score)
    return (df
            .merge(med_score, on=['code_module', 'code_presentation'])
            .assign(ocas_median=lambda df_:
                    np.where(df_[ocas_column] < df_.modpres_median_score, 'Low',
                             np.where(df_[ocas_column].isna(), '__NA__', 'High')))
            # .drop(columns=['median_score'])
            )


def band_assessment_by_median(df):
    med_score = (df
                 [['code_module', 'code_presentation', 'score']]
                 .dropna()
                 .groupby(['code_module', 'code_presentation'])
                 ['score']
                 .median()
                 .rename('median_score')
                 .reset_index()
                 )
    # med_score
    return (df
            .merge(med_score, on=['code_module', 'code_presentation'])
            .assign(score_banded_median=lambda df_:
                    np.where(df_.score < df_.median_score, 'Fail',
                             np.where(df_.score.isna(), 'NS', 'Pass')))
            .drop(columns=['median_score'])
            )


# Demographics

def band_region(series):
    region_band = {
        'Scotland': 'Scotland',
        'East Anglian Region': 'England',
        'South Region': 'England',
        'London Region': 'England',
        'North Western Region': 'England',
        'South West Region': 'England',
        'West Midlands Region': 'England',
        'East Midlands Region': 'England',
        'Wales': 'Wales',
        'South East Region': 'England',
        'Yorkshire Region': 'England',
        'North Region': 'England',
        'Ireland': 'Ireland'
    }
    return series.map(region_band)


def band_education(series):
    d = {
        "No Formal quals": "0_lower_ALevel",
        "Lower Than A Level": "0_lower_ALevel",
        "A Level or Equivalent": "1_ALevel",
        "HE Qualification": "2_higher_ALevel",
        "Post Graduate Qualification": "2_higher_ALevel",
    }
    return series.map(d)

# Missing Data imputation


def impute_ggg_weights(ass):
    ass = ass.reset_index()

    # HARDCODED
    ass.loc[lambda df_: (df_.code_module == 'GGG') & (df_.assessment_type == 'TMA'), 'weight'] = 33
    ass.loc[lambda df_: (df_.code_module == 'GGG') & (df_.assessment_type == 'CMA'), 'weight'] = 0.1666666
    ass = ass.set_index(['code_module', 'code_presentation']) 
    return ass

# ###############################################################################################
# Generalisable
# ###############################################################################################
# VLE preprocessing
# ###############################################################################################


def get_weekly_meanstd(df, max_day=None, min_day=0, max_week=None):
    if max_day is not None:
        df = df[df.date <= max_day]
    df = df[df.date >= min_day]
    if max_week is not None:
        df = df[df.week <= max_week]
    df_sum_click = (df.groupby(['id_student', 'week', 'weekday'])
                    ['sum_click']
                    .sum()
                    .unstack()
                    .fillna(0))
    for col in [0, 1, 2, 3, 4, 5, 6]:
        if col not in df_sum_click.columns:
            df_sum_click[col] = 0.
    df_sum_click = df_sum_click[sorted(df_sum_click.columns)]
    df_sum_click = df_sum_click.stack().rename('daysum').reset_index()
    df_sum_click['week'] = df_sum_click['week'].astype(int)

    x_sum = (df_sum_click.groupby(['id_student', 'week'])
             ['daysum']
             .sum().rename('weeksum')
             .reset_index())
    x_mer = df_sum_click.merge(x_sum, on=['id_student', 'week'])
    x_mer['daysum_norm'] = x_mer['daysum'] / x_mer['weeksum']
    grp = x_mer.groupby(['id_student', 'week'])
    norm_std = grp['daysum_norm'].agg(['std'])
    # daysum = grp['daysum'].agg(['mean'])
    return norm_std


def get_pct_weeks_active(df, max_day=None, min_day=0, max_week=None, max_weeks=None):
    if max_day is not None:
        df = df[df.date <= max_day]
    df = df[df.date >= min_day]
    if max_week is not None:
        df = df[df.week <= max_week]
    if max_weeks is None:
        max_weeks = df.groupby(['code_module', 'code_presentation'])['week'].max()

    df_res = (df
              .groupby(['code_module', 'code_presentation', 'id_student'])
              ['week']
              .nunique()
              .div(max_weeks)
              .fillna(0)
              )

    return df_res
