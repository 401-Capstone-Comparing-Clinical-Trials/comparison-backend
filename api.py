import flask
from flask import request, jsonify
import requests

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return '''
    <h1>Comparison Backend</h1>
    '''

# _______________________ API START _______________________ #
# request body:
# {
#     "keyword": "fulvestrant",
#     "numResults": "10",
#     "sortingCriteria": "age",
#     "order": "ascending"
# }
# _______________________ API END _______________________ #


def get_trials(keyword, num_results): #(fullStudies):
    
    # Use keyword and numResults to query the API
    key = keyword.split()
    search = ""
    last_ind = len(key) - 1

    for i in range(0, len(key)):
        search = search + key[i]
        if i != last_ind:
            search += "+"

    query_string = "https://clinicaltrials.gov/api/query/full_studies?expr=" + search + "&min_rnk=1&max_rnk=" + num_results + "&fmt=json"

    print(query_string)

    response = requests.get(query_string)

    full_studies_response =response.json()['FullStudiesResponse']
    full_studies = full_studies_response['FullStudies']
    # Frontend should pass fullStudies to backend, here I just call directly from API
    
    return full_studies
    
def apply_sorting_criteria(trial_data):
    print(" not done ")

# Sort Trials By Criteria Route
@app.route('/api/sortTrialsByCriteria', methods=['GET'])
def api_sort_trials_by_criteria():

    keyword = request.form['keyword']
    num_results = request.form['numResults']

    print(keyword + ", " + num_results)
    # get trial data based on keyword and numResults from front end request
    trial_data = get_trials(keyword, num_results)

    apply_sorting_criteria(trial_data)

    return jsonify(
        status=True,
        message="Successfully sorted trials",
        data=trial_data
    )

# sort trials from highest score to lowest (if there is no score, put this trial to tail)
def sort_trials(full_studies):
    def score(full_studies):
        try:
            return int(full_studies['score'])
        except KeyError:
            return float('-inf')
    full_studies.sort(key=score, reverse=True)

# Assign score to all trials
def set_up_score(trial_data, age, condition, inclusion, exclusion, ongoing, completed, include_drug, exclude_drug):
    for study in trial_data:
        try:
            protocol_section=study['Study']['ProtocolSection']
        except KeyError:
            print("No Protocol Section")
            continue
            
        score=0
        if protocol_section['EligibilityModule']:
            eligibility_module=protocol_section['EligibilityModule']
            # Check if age is in range
            try:
                min_age = eligibility_module['MinimumAge']
                int_min_age = int(min_age.split(' ')[0])
                if not age == '':
                    if int(age)>int_min_age:
                        score+=1
            except KeyError:
                print("No minimumAge Section")
            
            # Check eligibilityCriteria
            try:
                eligibility_criteria=eligibility_module['EligibilityCriteria']
                
                in_criteria=False
                ex_criteria=False
                in_str=eligibility_criteria
                ex_str=eligibility_criteria
                
                # Check inclusion
                if 'Inclusion Criteria:' in eligibility_criteria:
                    in_criteria=True
                    
                # Check exclusion
                if 'Exclusion Criteria:' in eligibility_criteria:
                    ex_criteria=True
                    if in_criteria:
                        in_str, ex_str = eligibility_criteria.split('Exclusion Criteria:')
                        
                if in_criteria:
                    if not inclusion == '':
                        if inclusion in in_str:
                            score+=1
                    
                if ex_criteria:
                    if not exclusion == '':
                        if exclusion in ex_str:
                            score+=1
            except KeyError:
                print("No EligibilityCriteria Section")
            
            
        # Check if this condition exists
        try:
            con_list=protocol_section['ConditionsModule']['ConditionList']['Condition']
            if not condition == '':
                if condition in con_list:
                    score+=1
        except KeyError:
            print("No condition Section")
        
        
        try:
            completed_date=protocol_section['StatusModule']['CompletionDateStruct']['CompletionDateType']
            # Check completed
            if completed:
                if completed_date=='Actual':
                    score+=1
                    
            # Check ongoing
            if ongoing:
                if completed_date=='Anticipated':
                    score+=1
        except KeyError:
            print("No completion date Section")
            
        
        try:
            # Check includeDrug and excludeDrug
            arm_group=protocol_section['ArmsInterventionsModule']['ArmGroupList']['ArmGroup']
            for arm in arm_group:
                drug_list=arm['ArmGroupInterventionList']['ArmGroupInterventionName']
                for drug in drug_list:
                    if not include_drug == '':
                        if include_drug.lower() in drug.lower(): # Make drug string to lower case 
                            score+=1 # includeDrug
                    if not exclude_drug == '':
                        if exclude_drug.lower() in drug.lower():
                            score-=1 # excludeDrug
        except KeyError:
            print("No includeDrug and excludeDrug Section")
            
        study.update({'score':score})
    

app.run()

