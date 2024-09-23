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
    
    if outcome == 'exam':
        bins = (10, 20, 30, 40, 50, 60, 70, 80, 90, 101)
    else:
        bins = (.1,.2,.3,.4,.5,.6,.7,.8,.9,1.01)
    fig, ax = plt.subplots(figsize=(8, 6))
    # for (g, grp), ax in zip(groups, axes.flatten()):
    if att is not None:
        df = df.groupby(att)
    else:
        att = 'Overall'
    df[outcome].hist(density=density,
            bins=bins, 
            alpha=0.5,
            ax=ax, 
            legend=True,
            histtype="step",
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
    ax.grid(True, linestyle='--', alpha=0.8)
    return fig

def show_correlations(df):
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
    st.write("pct_weeks_online = Percentage of weeks in the course that a student logged in Moodle (at least once)")
    st.write("exam = Exam Score")
    st.write("TMA 1-6 = The score in the Tutor Marked Assignment")


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
    st.pyplot(
        plot_per_group(df, att = col, outcome="exam", density=True)
    )

    st.header("Count of students")
    counts_all = "Overall Number of students: " + str(len(df))
    st.write(counts_all)

    if selected_column_name != 'Overall':
        counts = df.groupby(col).size().rename('Number of students')   
        st.write(counts)

def main():
    df = pd.read_csv('./data/stud_course_all.csv')
    # st.set_option("deprecation.showPyplotGlobalUse", False)
    # st.sidebar.image('./smartlearning_logo.jpg', use_column_width=True)
    st.sidebar.title("OULAD Visualisation")
    option = st.sidebar.selectbox("Select View", ["Correlations", "Histograms"])
    if option == "Correlations":
        show_correlations(df)
    if option == "Histograms":
        show_histograms(df)
    # elif option == "Data Dictionary & Raw":


if __name__ == "__main__":
    main()