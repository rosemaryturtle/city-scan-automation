def demographics(local_data_dir, local_output_dir, data_bucket, cloud_bucket, city_name_l, country_iso3, features, output_dir):
    import raster_pro
    import requests
    import os
    import utils

    local_demo_folder = f'{local_data_dir}/demographics'
    os.makedirs(local_demo_folder, exist_ok=True)

    wp_file_json = requests.get(f"https://www.worldpop.org/rest/data/age_structures/ascic_2020?iso3={country_iso3}").json()
    wp_file_list = wp_file_json['data'][0]['files']

    raster_pro.download_raster(wp_file_list, local_demo_folder, data_bucket, data_bucket_dir='WorldPop age structures')

    sexes = ['f', 'm']

    with open(f'{local_output_dir}/{city_name_l}_demographics.csv', 'w') as f:
        f.write('age_group,sex,population\n')

        for i in [1] + list(range(0, 85, 5)):
            for s in sexes:
                out_image, out_meta = raster_pro.raster_mask_file(f'{local_demo_folder}/{country_iso3.lower()}_{s}_{i}_2020_constrained.tif', features)
                out_image[out_image == out_meta['nodata']] = 0

                if i == 0:
                    age_group_label = '0-1'
                elif i == 1:
                    age_group_label = '1-4'
                elif i == 80:
                    age_group_label = '80+'
                else:
                    age_group_label = f'{i}-{i+4}'
                
                f.write('%s,%s,%s\n' % (age_group_label, s, sum(sum(sum(out_image)))))
    
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_demographics.csv', f'{output_dir}/{city_name_l}_demographics.csv')

def demo_plot(city_name, city_name_l, render_dir, font_dict, local_output_dir, cloud_bucket, output_dir):
    import pandas as pd
    import matplotlib.pyplot as plt
    import plotly.express as px
    import yaml
    import utils

    pop_dist_group_wp = pd.read_csv(f'{local_output_dir}/{city_name_l}_demographics.csv')

    pop_dist_group_wp = pop_dist_group_wp.rename(columns={"age_group": "Age_Bracket", "sex": "Sex"})
    pop_dist_group_wp['Count'] = pd.to_numeric(pop_dist_group_wp['population'], errors='coerce')
    pop_dist_group_wp['Age_Bracket'] = pop_dist_group_wp['Age_Bracket'].replace({'0-1': '0-4', '1-4': '0-4'})

    # Define custom sorting for age brackets
    age_order = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79', '80+']
    pop_dist_group_wp['Age_Bracket'] = pd.Categorical(pop_dist_group_wp['Age_Bracket'], categories=age_order, ordered=True)
    pop_dist_group_wp = pop_dist_group_wp.groupby(['Age_Bracket', 'Sex']).agg(Count=('Count', 'sum')).reset_index()

    pop_dist_group_wp['Percentage'] = pop_dist_group_wp.groupby('Sex')['Count'].transform(lambda x: x / x.sum()) * 100
    pop_dist_group_wp['Sexed_Percent'] = pop_dist_group_wp.groupby('Sex')['Count'].transform(lambda x: x / x.sum()) * 100
    pop_dist_group_wp['Sexed_Percent_cum'] = pop_dist_group_wp.groupby('Sex')['Sexed_Percent'].cumsum()

    colors = {'f': 'red', 'm': 'blue'}
    plt.figure(figsize=(8, 6))

    plt.title(f"Population distribution in {city_name} by sex")
    plt.xlabel("Age Bracket")
    plt.ylabel("Percentage")
    legend_handles = []
    for sex, color in colors.items():
        legend_handles.append(plt.Line2D([0], [0], color=color, lw=4, label='Female' if sex == 'f' else 'Male'))
    plt.legend(handles=legend_handles, title="Sex", loc="upper right")
    plt.xticks(rotation=45)
    plt.tight_layout()

    render_path = f"{local_output_dir}/{city_name_l}_age_stats.png"
    plt.savefig(render_path)
    plt.close()

    pop_dist_group_wp_sorted = pop_dist_group_wp.sort_values(by='Age_Bracket')
    fig = px.bar(pop_dist_group_wp_sorted, x='Age_Bracket', y='Percentage', color='Sex', barmode='group',  
                labels={'Age_Bracket': 'Age Bracket', 'Percentage': 'Percentage', 'Sex': 'Sex'},color_discrete_map={'f': 'red', 'm': 'blue'})

    fig.update_layout(template='plotly_white', xaxis_title="", yaxis_title="Percentage of Age Distribution", legend_title="", legend=dict(
            orientation="h",  
            yanchor="top",
            y=-0.4,  
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
                linecolor='black'  
            ),
        yaxis=dict(
                linecolor='black'  
            ),
        autosize=True,
        font=font_dict,
        plot_bgcolor='white')
    fig.for_each_trace(lambda t: t.update(name='Female' if t.name == 'f' else 'Male'))
    fig.update_xaxes(tickangle=45)
    fig.show()
    fig.write_html(render_path.replace('.png', '.html'), full_html=False, include_plotlyjs='cdn')

    under5 = pop_dist_group_wp[pop_dist_group_wp['Age_Bracket'] == '0-4']['Percentage'].sum()
    youth = pop_dist_group_wp[pop_dist_group_wp['Age_Bracket'].isin(['15-19', '20-24'])]['Percentage'].sum()
    total_percent = pop_dist_group_wp['Percentage'].sum()
    working_age_rows = pop_dist_group_wp[pop_dist_group_wp['Age_Bracket'].isin(['15-19','20-24','25-29','30-34','35-39','40-44','45-49','50-54','55-59','60-64'])]
    working_age_percent = working_age_rows['Percentage'].sum()
    working_age = (working_age_percent / total_percent) 
    elderly = pop_dist_group_wp[pop_dist_group_wp['Age_Bracket'].isin(['60-64', '65-69', '70-74', '75-79', '80+'])]['Percentage'].sum()
    male_count = pop_dist_group_wp[pop_dist_group_wp['Sex'] == 'm']['Count'].sum()
    female_count = pop_dist_group_wp[pop_dist_group_wp['Sex'] == 'f']['Count'].sum()
    sex_ratio = male_count / female_count * 100
    reproductive_age = pop_dist_group_wp[(pop_dist_group_wp['Sex'] == 'f') & (pop_dist_group_wp['Age_Bracket'].isin(['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49']))]['Sexed_Percent'].sum()

    summary_data = {
        'under5': f"{under5:.2f}%",
        'youth (15-24)': f"{youth:.2f}%",
        'working_age (15-64)': f"{working_age:.2f}%",
        'elderly (60+)': f"{elderly:.2f}%",
        'reproductive_age, percent of women (15-49)': f"{reproductive_age:.2f}%",
        'sex_ratio': f"{round(sex_ratio, 2)} males to 100 females"
    }

    with open(f"{local_output_dir}/{city_name_l}_demographics_summary.yml", 'w') as summary_file:
        yaml.dump(summary_data, summary_file, default_flow_style=False)

    utils.upload_blob(cloud_bucket, render_path, f'{render_dir}/{city_name_l}_age_stats.png', type = 'render')
    utils.upload_blob(cloud_bucket, render_path.replace('.png', '.html'), f'{render_dir}/{city_name_l}_age_stats.html', type = 'render')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_demographics_summary.yml', f'{output_dir}/{city_name_l}_demographics_summary.yml')
