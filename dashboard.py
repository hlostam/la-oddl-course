import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


mod_pres_list = ['CCC_2014B','CCC_2014J','DDD_2013B','DDD_2013J','DDD_2014B','DDD_2014J']
col_dict = {'Gender':'gender',
            'Disability':'disability',
            'Previous education':'educ_band',
            'Age':'age_band',
            'Is repeating':'is_repeating',
            'Other credits':'credits_other_band',
            'Overall':None}


def plot_per_group(df, att = None, outcome="score", density=True):
    # outcome = 'pct_weeks_active_before_exam'
    # groups = (df
    #     # .loc[lambda df_: df_.assessment_name == 'Exam']
    #     .groupby(['code_module','code_presentation','assessment_name'])
    # )
    
    # if outcome == 'exam':
    #     bins = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 101)
    # else:
    #     bins = (.1,.2,.3,.4,.5,.6,.7,.8,.9,1.01)
    fig, ax = plt.subplots(figsize=(8, 6))
    # for (g, grp), ax in zip(groups, axes.flatten()):
    if att is not None:
        df = df.groupby(att)
    else:
        att = 'Overall'
    type_of_graph = st.selectbox("Type of graph", ['Histogram','Cumulative histogram','Density plot'])   
    if type_of_graph == 'Histogram':
        cumulative=0
        bins = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 101)
    elif type_of_graph == 'Cumulative histogram':
        cumulative=1
        bins = range(0,101)

    ind = range(0,101)
    if type_of_graph == 'Density plot':
        y_legend = "Density"
        df[outcome].plot.kde(
                # density=density_inner_flag,
                # bins=bins, 
                # alpha=0.5,
                ax=ax, 
                legend=True,
                ind=ind,
                bw_method=0.5,
                # histtype=fill_type,
                # cumulative=cumulative,
                # lw=3
                )
    else:
        fill = st.selectbox("Type of fil", ['Outline only','Filled'])
        density_inner = st.selectbox("Normalise the counts", ['YES','NO'])   

        if fill == 'Filled':
            fill_type = 'stepfilled'
        else:
            fill_type = 'step' 

        if density_inner == 'YES':
            density_inner_flag = 1
            y_legend = "Proportion of students for a given exam band."
        else:
            density_inner_flag = 0
            y_legend = "Frequency - number of students for a given exam band"
        df[outcome].hist(
            density=density_inner_flag,
                bins=bins, 
                alpha=0.5,
                ax=ax, 
                legend=True,
                histtype=fill_type,
                cumulative=cumulative,
                lw=3
                )
    
    # ax.hist(df[outcome],
    #         density=density,
    #         bins=bins, 
    #         # bins=(10, 20, 30, 40, 50, 60, 70, 80, 90, 101),
    #         alpha=0.5,
    #         # ax=ax, 
    #         # legend=True
    #         )
    ax.set_title('Histogram - ' + att)
    ax.set_xlabel("Exam score")
    ax.set_ylabel(y_legend)
    ax.grid(True, linestyle='--', alpha=0.8)
    return fig


def show_correlations_tma(df):
    st.header('Correlations')
    mod_pres = st.sidebar.selectbox("Select Course",mod_pres_list)   
    
    df_corr = (df
        .loc[lambda df_: df_.mod_pres == mod_pres]
        [['pct_weeks_online',
          'exam','TMA 1','TMA 2','TMA 3','TMA 4','TMA 5','TMA 6']]
        .corr()
        #  ['pct_weeks_active_before_exam']
        #  .unstack()['score']
        # .reset_index()
        .round(2)
        .dropna(axis='index',how='all')
        .dropna(axis='columns',how='all')
        .style
            .format(precision=4)
            .background_gradient(axis=None, vmin=0, vmax=1, 
                                 cmap="YlGnBu"
                                 )
    )
    st.write(df_corr)
    st.write("Each value in the table is a Person correlation coefficient between the two variables.")
    st.write("- pct_weeks_online = Percentage of weeks in the course that a student logged in Moodle (at least once)")
    st.write("- exam = Exam Score")
    st.write("- TMA 1-6 = The score in the Tutor Marked Assignment")


def show_correlations(df):
    st.header('Correlations')
    # mod_pres = st.sidebar.selectbox("Select Course",mod_pres_list)   

    st.markdown("""Each value in the two tables below is a [Pearson correlation coefficient](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient) between the semester score that the student gained and the exam score.
- **semester_score** = Weighted average of assignments accumulated during the semester.
- **exam** = Exam Score
    """)
    

    df_corr = (df
        # .loc[lambda df_: df_.mod_pres == mod_pres]
        .groupby(['mod_pres'])
        [[
          'ocas','exam'
          ]]
        .corr()
        #  ['exam']
        #  .unstack()['score']
        # .reset_index()
        .round(4)
        .dropna(axis='index',how='all')
        .dropna(axis='columns',how='all')
        .reset_index()
        .drop(columns=['ocas'])
        .set_index('mod_pres')
        [['exam']]
        .loc[lambda df_: df_.exam < 1.0]
        .style
            .format(precision=4)
            .background_gradient(axis=None, vmin=0, vmax=1, 
                                 cmap="YlGnBu"
                                 )
    )
    st.write('Overall correlation between the semester score and the exam score.')
    st.write(df_corr)


    st.write("**Correlations per student factors**")
    selected_column_name = st.selectbox("Select a grouping column", [
        # 'Overall',
        'Gender',
                                                            'Is repeating',
                                                            'Disability',
                                                            'Previous education',
                                                            'Age',
                                                            'Other credits'])
    col = col_dict[selected_column_name]
    df_corr_col = (df
        # .loc[lambda df_: df_.mod_pres == mod_pres]
        .groupby(['mod_pres',col])
        [[
          'ocas','exam'
          ]]
        .corr()
        .round(4)
        # .dropna(axis='index',how='all')
        # .dropna(axis='columns',how='all')
        ['exam']
        .loc[lambda df_: df_ < 1.0]
        .unstack().unstack()['ocas']
        .style
            .format(precision=4)
            .background_gradient(axis=None, vmin=0, vmax=1, 
                                 cmap="YlGnBu"
                                 )
    )
    
    st.write(df_corr_col)
    
    st.write("**Student Counts**")
    counts = df.groupby(['mod_pres',col]).size().unstack()   
    
    st.write(counts)
    
    

def show_histograms(df):
    st.header('Histograms')
    mod_pres = st.sidebar.selectbox("Select Course",mod_pres_list)
    selected_column_name = st.selectbox("Select a column", [
        'Overall','Gender',
                                                            'Is repeating',
                                                            'Disability',
                                                            'Previous education',
                                                            'Age',
                                                            'Other credits'])
    col = col_dict[selected_column_name]
    df_filt = df.loc[lambda df_: df_.mod_pres == mod_pres]
    st.pyplot(
        plot_per_group(df_filt, att = col, outcome="exam", density=True)
    )

    st.header("Count of students")
    counts_all = "Overall Number of students: " + str(len(df_filt))
    st.write(counts_all)

    if selected_column_name != 'Overall':
        counts = df_filt.groupby(col).size().rename('Number of students')   
        st.write(counts)


def show_data_overview(df):
    st.header('Data Overview')
    # mod_pres = st.sidebar.selectbox("Select Course",mod_pres_list)
    st.markdown("""
**Data description**

The data describes two course CCC and DDD from OULAD dataset, in 4 different presntations (runs). For CCC it is 2014B and 2014J. For DDD it is 2013B, 2013J, 2014B and 2014J.
- **B** - the course starts in February
- **J** - the course starts in October

Both courses are from the STEM area, and they have a duration more than 30 weeks. Students need to gain enough points during the semester and then pass the exam to pass the whole course.
                 
**Attributes**
- **Is repeating** - New=New student, Repeating=student already tried to take this module in the past but did not finish it (it might be early or late withdrawal, failing the exam)           
- **Disability** - Flag whether the student has declared any disability (Y/N)
- **Gender** - Male or Female
- **Previous education** - Highest education level achieved before the start of the course banded into three categories, based on A-level (similar to maturita exam)                
- **Age** - Age of the student at the start of the course banded into two categories (older or younger than 35 years)
- **Other credits** - Total number of enrolled credits in other than the studied course, banded into three categories - [0-1] = no other credits, [1-60) - less than 60, [60,600) - more than 60 
               
                
    """)

    st.write("**Student Counts**")
    counts = df.groupby(['mod_pres']).size().rename('Total number')   
    counts_gender = df.groupby(['mod_pres','gender']).size().unstack().add_prefix('gender_')
    counts_age = df.groupby(['mod_pres','age_band']).size().unstack().add_prefix('age_')
    counts_rep = df.groupby(['mod_pres','is_repeating']).size().unstack().add_prefix('repeat_')
    counts_dis = df.groupby(['mod_pres','disability']).size().unstack().add_prefix('disability_')
    counts_educ = df.groupby(['mod_pres','educ_band']).size().unstack().add_prefix('educ_')
    counts_cred = df.groupby(['mod_pres','credits_other_band']).size().unstack().add_prefix('credits_')
    
    counts  = (pd.DataFrame(counts)
               .merge(counts_gender, on=['mod_pres'])
               .merge(counts_age, on=['mod_pres'])
               .merge(counts_rep, on=['mod_pres'])

               .merge(counts_dis, on=['mod_pres'])
               .merge(counts_educ, on=['mod_pres'])
               .merge(counts_cred, on=['mod_pres'])
    )
    st.write(counts)
    


def main():
    df = pd.read_csv('./data/stud_course_all.csv')
    # st.set_option("deprecation.showPyplotGlobalUse", False)
    # st.sidebar.image('./smartlearning_logo.jpg', use_column_width=True)
    st.sidebar.title("OULAD Visualisation")
    option = st.sidebar.selectbox("Select View", ["Data Overview",
                                                  "Histograms", 
                                                  "Correlations"])
    if option == "Data Overview":
        show_data_overview(df)
    if option == "Correlations":
        show_correlations(df)
    if option == "Histograms":
        show_histograms(df)
    # elif option == "Data Dictionary & Raw":


if __name__ == "__main__":
    main()