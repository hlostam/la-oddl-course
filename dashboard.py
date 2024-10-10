import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

import plotly.express as px

mod_pres_list = ['CCC_2014B','CCC_2014J','DDD_2013B','DDD_2013J','DDD_2014B','DDD_2014J']
mod_pres_list_task2 = ['CCC_2014B', 'DDD_2013B', 'DDD_2014B' ]

col_dict = {'Gender':'gender',
            'Disability':'disability',
            'Previous education':'educ_band',
            'Age':'age_band',
            'Is repeating':'is_repeating',
            'Other credits':'credits_other_band',
            'IMD': 'imd_2',
            'Overall': None
            }


def plot_per_group(df, att = None, outcome="score", density=True):
    fig, ax = plt.subplots(figsize=(8, 6))
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
                bw_method=0.3,
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
    
    ax.set_title('Histogram - ' + att)
    ax.set_xlabel("Exam score")
    ax.set_ylabel(y_legend)
    ax.grid(True, linestyle='--', alpha=0.8)
    return fig


def show_correlations_tma(df, assessment_types = 'both', precision=4):
    st.header('TMA Correlations')
    if assessment_types == 'TMA':
        asssessments = ['TMA 1','TMA 2','TMA 3','TMA 4','TMA 5','TMA 6', 'exam']
    elif assessment_types == 'CMA':
        asssessments = ['CMA 1','CMA 2','CMA 3','CMA 4','CMA 5','CMA 6','CMA 7', 'exam']
    elif assessment_types == 'both':
        asssessments = ['TMA 1','TMA 2','TMA 3','TMA 4','TMA 5','TMA 6',
                    'CMA 1','CMA 2','CMA 3','CMA 4','CMA 5','CMA 6','CMA 7', 
                    'exam']

    df_corr = (df
        
        [asssessments]
        .corr()
        .round(precision)
        .dropna(axis='index',how='all')
        .dropna(axis='columns',how='all')
        .style
            .format(precision=precision)
            .background_gradient(axis=None, vmin=0, vmax=1, 
                                 cmap="YlGnBu"
                                 )
    )
    st.write(df_corr)
    st.write("Each value in the table is a Person correlation coefficient between the two variables.")
    st.write("- exam = Exam Score")
    st.write("- TMA 1-6 = The score in the Tutor Marked Assignment")
    st.write("- CMA 1-7 = The score in the Computer Marked Assignment (Quiz)")

def show_registrations(df_reg):
    st.header('Registrations')
    max_reg = df_reg.num_students_registered.max()

    df_reg = df_reg.set_index('week').assign(pct_registered_student = lambda df_: ((df_.num_students_registered/max_reg)* 100) )
    density_inner = st.selectbox("Normalise the counts", ['YES','NO'])
    if density_inner == "YES":
        col = 'pct_registered_student'
    else:
        col = 'num_students_registered'
    
    df_to_plot = df_reg[col].reset_index()
    fig = px.line(df_to_plot.reset_index(), x='week', 
                  y=df_to_plot.columns,
                  labels={'value': '% students registered in a given week.'})  # Replace with your column names
    fig.update_yaxes(range=[0, 100])

    st.plotly_chart(fig, key="regisration", on_select="rerun")
    

def show_engagement(df_vle, df_vle_demog, df_reg):
    st.header("VLE Engagement")
    mod_pres = st.sidebar.selectbox("Select Course", mod_pres_list_task2) 
    df_vle_filt = (df_vle
                   .loc[lambda df_: df_.mod_pres == mod_pres]
                   .drop(columns=['mod_pres'])
    )
    df_reg_filt = (df_reg
                   .loc[lambda df_: df_.mod_pres == mod_pres]
    )
    
    # fig, ax = plt.subplots(figsize=(8, 6))
    df_to_plot = (df_vle_filt
                .set_index(['week'])
                .dropna(axis='columns',how='all')
                # .drop(columns=drop_cols)
                .rename(columns={'oucollaborate':'Webinar',
                                 'ouelluminate':'Webinar',
                                 'resource':'PDF Download',
                                 'forumng':'Forum',
                                 'oucontent':'HTML content',
                                 'url':'External link',
                                 'homepage':'Homepage',
                                 'quiz':'Quiz','externalquiz':'Quiz',
                                 'ouwiki':'Wiki',
                                 'glossary':'Glossary'
                                 })
                .fillna(0)
                )
    drop_cols = ['dataplus','page','sharedsubpage','dualpane','folder','subpage']
    for col in drop_cols:
        if col in df_to_plot:
            df_to_plot = df_to_plot.drop(columns=[col])
    
    fig = px.line(df_to_plot.reset_index(), 
                  x='week', 
                  y=df_to_plot.columns,
                  labels={'value': '% students with the activity, out of all registered in that week. ',
                          'variable':'Activity Type'}
                  )  
    fig.update_yaxes(range=[0, 1])
    st.plotly_chart(fig, key="vle_at", on_select="rerun", theme=None,)

    st.write("Overall percentage of students in VLE per demographic group.")
    selected_column_name = get_selected_column()
    col = col_dict[selected_column_name]
    if selected_column_name != 'Overall':
        df_vle_demog_filt = (df_vle_demog
                    .loc[lambda df_: df_.mod_pres == mod_pres]
            .loc[lambda df_: df_.col == col]
            .drop(columns=['mod_pres','col'])
            .set_index(['week','val'])
            .unstack()
            ['pct_students']
        )

        fig2 = px.line(df_vle_demog_filt.reset_index(), x='week',
                       y=df_vle_demog_filt.columns,
                        labels={
                            'value': '% students with the activity, out of all registered in that week. ',
                           'variable':'Attribute Value'
                           }
                  )  
        fig2.update_yaxes(range=[0, 1])
        st.plotly_chart(fig2, theme=None, key="vle_grp", on_select="rerun")

    # show_student_counts(df_vle_demog_filt, col)
    show_registrations(df_reg_filt)


def show_assessment_difficulty(df, df_ass, df_ass_stats, precision=2):
    st.header('TMA difficulty')
    asssessments = ['TMA 1','TMA 2','TMA 3','TMA 4','TMA 5','TMA 6',
                    'CMA 1','CMA 2','CMA 3','CMA 4','CMA 5','CMA 6','CMA 7', 
                    'exam']
    
    df_res_all = (df[asssessments].mean().dropna().round(precision).rename('Average Score')
            .reset_index()
        .merge(df_ass, left_on=['index'], right_index=True)
        .merge(df_ass_stats
               .drop(columns=['week','num_students_registered','num_submitted',
                              'avg_score','score_std']).round(precision)
               .assign(pct_late = lambda df_: df_.pct_late * 100,
                       pct_submitted = lambda df_: df_.pct_submitted * 100), 
               left_on=['index'], right_index=True)
        .set_index(['index'])
        .sort_values(by=['date'])
        [['date','week','weight','pct_submitted','pct_late','Average Score']]
    )
    st.write(df_res_all)

    st.write("Columns explanation")
    st.write("- date = deadline of the assignment as the numbet of days from the course start")
    st.write("- week = week of the assignment deadline")
    st.write("- weight [0-100] = how much the score contributes to the overall course assessmnet score (OCAS)")
    st.write("- pct_submitted [0-100] = percentage of students that submitted the assignment, out of number of students that were registered at the date of the deadline")
    st.write("- pct_late [0-100] =  percentage of students that submitted the assignment after the deadline, out of students that submitted.")
    st.write("- Average score [0-100] = mean score achieved by students, out of students that submitted. Not-submitted are not counted in the average.")


    st.header('-- Average Score per student factor')
    selected_column_name = get_selected_column()
    col = col_dict[selected_column_name]
    
    
    if selected_column_name != 'Overall':
        df_res = (df.groupby(col)[asssessments].mean().transpose().dropna(axis='index',how='all')
                  .add_prefix('Average Score '))
        df_res = (df_res.style
            .format(precision=precision)
            .background_gradient(axis=None, vmin=0, vmax=100, 
                                 cmap="YlGnBu"
                                 )
                                 )
        st.write(df_res)

    show_student_counts(df, col)


def show_assessment_correlations(df, df_ass, df_ass_stats):
    st.header('Assessment Correlations')
    mod_pres = st.sidebar.selectbox("Select Course", mod_pres_list_task2)   
    
    df_filt = df.loc[lambda df_: df_.mod_pres == mod_pres]
    df_ass_filt = (df_ass
                   .loc[lambda df_: df_.mod_pres == mod_pres]
        .drop(columns=['code_module','code_presentation', 'mod_pres'])
        .set_index(['assessment_name'])
    )
    df_ass_stats_filt = (df_ass_stats
                         .loc[lambda df_: df_.mod_pres == mod_pres]
        .drop(columns=['mod_pres'])
        .set_index(['assessment_name'])
    )
    

    show_correlations_tma(df_filt)
    show_assessment_difficulty(df_filt, df_ass_filt, df_ass_stats_filt)
    

def show_correlations(df, precision=4):
    st.header('Correlations')

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
        .round(precision)
        .dropna(axis='index',how='all')
        .dropna(axis='columns',how='all')
        .reset_index()
        .drop(columns=['ocas'])
        .set_index('mod_pres')
        [['exam']]
        .loc[lambda df_: df_.exam < 1.0]
        .style
            .format(precision=precision)
            .background_gradient(axis=None, vmin=0, vmax=1, 
                                 cmap="YlGnBu"
                                 )
    )
    st.write('Overall correlation between the semester score and the exam score.')
    st.write(df_corr)


    st.write("**Correlations per student factors**")
    selected_column_name = get_selected_column()

    col = col_dict[selected_column_name]
    df_corr_col = (df
        .groupby(['mod_pres',col])
        [[
          'ocas','exam'
          ]]
        .corr()
        .round(4)
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
    
    show_student_counts(df, col)

def show_student_counts(df, col):
    st.write("**Student Counts per selected characteristic**")
    counts_all = "Overall Number of students: " + str(len(df))
    st.write(counts_all)

    if col != None:
        if 'mod_pres' in df.columns:
            counts = df.groupby(['mod_pres',col]).size().unstack()   
        else:
                counts = df.groupby([col]).size().unstack()   
        st.write(counts)

def get_selected_column():
    return st.selectbox("Select a column", [
        'Overall',
        'Gender',
        'Is repeating',
        'Disability',
        'Previous education',
        'Age',
        'Other credits',
        'IMD'])


def show_histograms(df):
    st.header('Histograms')
    mod_pres = st.sidebar.selectbox("Select Course",mod_pres_list)
    selected_column_name = get_selected_column()
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
- **IMD** - Index of multiple deprivation, banded into three categories - Q1_Q2 = 0\%-40, indicating the highest poverty areas, Q3 = 40\%-60\%, indicating medium quality of the neighbourhood, Q4_Q5 = 60\%-100\%, indicating the most affluent areas and INT = missing IMD, indicating international students  

**VLE activity types***
- **Homepage** - visiting a homepage of the course, usually any other activity happens after the homepage visit                       
- **Forum** - students discussing in an online forum, can be both reading or contribution                      
- **Webinar** - synchronous meeting using an online platform (such as Teams, Adobe connect, etc.)                        
- **Quiz** - computer graded quiz, can result in a score in CMA or if it is formattive, then it is just an indication for a student without any grading implication.                        
- **External link** - indicates click leading outside Moodle VLE (can be news, video platform, or some external learning system, ...)                      
- **PDF Download** - downloading of a PDF resource that can be then viewed offline and such activity cannot be tracked anymore                       
- **HTML content** - usually the main content of the course is presented in this way, includes structuring into sections and can contain images 
- **Glossary** -  can serve as a collaborative dictionary where students and teachers add new entries, could be viewing a Glossary, adding or editing a Glossary entry (word, term, or definition), or approving entries.
- **Wiki** - collaborative tool allowing multiple students to create, edit, and manage a collection of web pages. Could be group work, or building a knowledge base collectively. The activity can be viewing the Wiki page or creating or editing a Wiki entry.                           
                 
                
    """)

    st.write("**Student Counts**")
    counts = df.groupby(['mod_pres']).size().rename('Total number')   
    counts_gender = df.groupby(['mod_pres','gender']).size().unstack().add_prefix('gender_')
    counts_age = df.groupby(['mod_pres','age_band']).size().unstack().add_prefix('age_')
    counts_rep = df.groupby(['mod_pres','is_repeating']).size().unstack().add_prefix('repeat_')
    counts_dis = df.groupby(['mod_pres','disability']).size().unstack().add_prefix('disability_')
    counts_educ = df.groupby(['mod_pres','educ_band']).size().unstack().add_prefix('educ_')
    counts_cred = df.groupby(['mod_pres','credits_other_band']).size().unstack().add_prefix('credits_')
    counts_cred = df.groupby(['mod_pres','imd_2']).size().unstack().add_prefix('IMD_')
    
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
    df_ass = pd.read_csv('./data/assessments.csv')
    df_ass_stats = pd.read_csv('./data/stud_ass_stats.csv')
    df_reg = pd.read_csv('./data/reg_stat_weekly_all.csv')
    df_vle = pd.read_csv('./data/vle_by_act_all.csv')
    df_vle_demog = pd.read_csv('./data/vle_weekly_demog_all.csv')

    st.sidebar.title("OULAD Visualisation")
    option = st.sidebar.selectbox("Select View", ["_Data Overview",
                                                  "Task1_Histograms", 
                                                #   "Correlations",
                                                  "Task2_Assessments",
                                                  "Task2_Engagement"
                                                  ])
    if option == "_Data Overview":
        show_data_overview(df)
    if option == "Correlations":
        show_correlations(df)
    if option == "Task1_Histograms":
        show_histograms(df)
    if option == "Task2_Assessments":
        show_assessment_correlations(df, df_ass, df_ass_stats)
    if option == "Task2_Engagement":
        show_engagement(df_vle, df_vle_demog, df_reg)


if __name__ == "__main__":
    main()