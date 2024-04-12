    
![png](output_4_0.png)
    





    '\ncity=\'Mumbai\'\ndef oxford_age_stats():\n    with open("global_inputs.yml", \'r\') as f:\n        global_inputs = yaml.safe_load(f)\n\n    # Get city inputs\n    city_inputs = global_inputs.get(\'city_inputs\')\n    \n# Define the \'oxford_age_stats\' function\ndef oxford_age_stats(city):\n    with open("global_inputs.yml", \'r\') as f:\n        global_inputs = yaml.safe_load(f)\n\n    # Get city inputs\n    city_inputs = global_inputs.get(\'city_inputs\')\n\n    if \'oxford\' in menu and menu[\'oxford\']:  \n        oxford_data_path = os.path.join(multi_scan_folder, "Oxford Global Cities Data.csv")\n        if os.path.exists(oxford_data_path):  \n            oxford_data = pd.read_csv(oxford_data_path)\n            indicators = oxford_data[\'Indicator\'].drop_duplicates()\n            pop_dist_inds = [indicator for indicator in indicators if "Population" in indicator and indicator not in ["Population 0-14", "Population 15-64", "Population 65+"]]  \n\n            if city in oxford_data[\'Location\'].values:\n                print(f"{city} exists in the Oxford file.")\n                pop_dist_structure = oxford_data.loc[(oxford_data[\'Location\'] == city) & (oxford_data[\'Indicator\'].isin(pop_dist_inds))]\n                print(pop_dist_structure.head(3))\n                pop_dist_structure[\'Age_Bracket\'] = pop_dist_structure[\'Indicator\'].str[11:19]\n                # Convert to numeric, handling errors by setting them to NaN\n                pop_dist_structure[\'Age_Bracket\'] = pd.to_numeric(pop_dist_structure[\'Age_Bracket\'], errors=\'coerce\')\n                pop_dist_structure[\'Group\'] = pd.cut(\n                    pop_dist_structure[\'Age_Bracket\'],\n                    bins=[0, 4, 14, np.inf],  # Replace float(\'inf\') with np.inf\n                    labels=[\'Young\', \'Working\', \'65+\']\n                )\n                \n                pop_dist_structure = pop_dist_structure.groupby([\'Year\', \'Group\']).agg(Count=(\'Value\', \'sum\')).reset_index()\n                pop_dist_structure[\'Percent\'] = pop_dist_structure.groupby(\'Year\')[\'Count\'].transform(lambda x: x / x.sum())\n                pop_dist_structure[\'pct_sum\'] = pop_dist_structure.groupby(\'Year\')[\'Percent\'].cumsum()\n                return pop_dist_structure\n            else:\n                print(f"{city} does not exist in the Oxford file.")\n        else:\n            print("Oxford file does not exist.")\n    else:\n        print("Oxford is not selected in the menu.")\n\n# Example usage\noxford_age_stats(\'Mumbai\')\n'



    /Users/ipshitakarmakar/mambaforge/envs/geo/share/jupyter/nbconvert/templates/base/display_priority.j2:32: UserWarning:
    
    Your element with mimetype(s) dict_keys(['application/vnd.plotly.v1+json']) is not able to be represented.
    

