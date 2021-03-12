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
#     "data": [json array of trials],
#     "sortingCriteria": "age",
#     "order": "ascending"
# }
API_ENDPOINT = "https://clinicaltrials.gov/api/query/full_studies?expr=paloma+3%0D%0A&min_rnk=1&max_rnk=2&fmt=json"
response = requests.get(API_ENDPOINT)

def jsonArrayFromFrontend(): #(fullStudies):
    
    fullStudiesResponse=response.json()['FullStudiesResponse']
    fullStudies=fullStudiesResponse['FullStudies']
    # Frontend should pass fullStudies to backend, here I just call directly from API
    
    setUpScore(fullStudies, '19', 'Breast Cancer', 'breast cancer', 'CNS', True, False, 'Palbociclib', 'Placebo')
    sortTrials(fullStudies)
    
    return fullStudies
    
# _______________________ API END _______________________ #


# Sort Trials By Criteria Route
@app.route('/api/sortTrialsByCriteria', methods=['GET'])
def api_sortTrialsByCriteria():
    return jsonify(
        status=True,
        message="Successfully sorted trials",
        data=jsonArrayFromFrontend()
    )

# sort trials from highest score to lowest (if there is no score, put this trial to tail)
def sortTrials(fullStudies):
    def score(fullStudies):
        try:
            return int(fullStudies['score'])
        except KeyError:
            return 0
    fullStudies.sort(key=score, reverse=True)

# Assign score to all trials
def setUpScore(fullStudies, age, condtion, inclusion, exclusion, ongoing, completed, includeDrug, excludeDrug):
    for study in fullStudies:
        score=0
        if study['Study']['ProtocolSection']['EligibilityModule']['MinimumAge']:
            eligibilityModule=study['Study']['ProtocolSection']['EligibilityModule']
            # Check if age is in range
            if eligibilityModule['MinimumAge']:
                minAge = eligibilityModule['MinimumAge']
                intMinAge = int(minAge.split(' ')[0])
                if not age == '':
                    if int(age)>intMinAge:
                        score+=1
            
            # Check eligibilityCriteria
            if eligibilityModule['EligibilityCriteria']:
                eligibilityCriteria=eligibilityModule['EligibilityCriteria']
                
                inCriteria=False
                exCriteria=False
                inStr=eligibilityCriteria
                exStr=eligibilityCriteria
                
                # Check inclusion
                if 'Inclusion Criteria:' in eligibilityCriteria:
                    inCriteria=True
                    
                # Check exclusion
                if 'Exclusion Criteria:' in eligibilityCriteria:
                    exCriteria=True
                    if inCriteria:
                        inStr, exStr = eligibilityCriteria.split('Exclusion Criteria:')
                        
                if inCriteria:
                    if not inclusion == '':
                        if inclusion in inStr:
                            score+=1
                    
                if exCriteria:
                    if not exclusion == '':
                        if exclusion in exStr:
                            score+=1
                
        # Check if this condition exists
        if study['Study']['ProtocolSection']['ConditionsModule']['ConditionList']['Condition']:
            conList=study['Study']['ProtocolSection']['ConditionsModule']['ConditionList']['Condition']
            if not condtion == '':
                if condtion in conList:
                    score+=1
        
        
        if study['Study']['ProtocolSection']['StatusModule']['CompletionDateStruct']['CompletionDateType']:
            completedDate=study['Study']['ProtocolSection']['StatusModule']['CompletionDateStruct']['CompletionDateType']
            # Check completed
            if completed:
                if completedDate=='Actual':
                    score+=1
                    
            # Check ongoing
            if ongoing:
                if completedDate=='Anticipated':
                    score+=1
        
        
        # Check includeDrug and excludeDrug
        if study['Study']['ProtocolSection']['ArmsInterventionsModule']['ArmGroupList']['ArmGroup']:
            armGroup=study['Study']['ProtocolSection']['ArmsInterventionsModule']['ArmGroupList']['ArmGroup']
            for arm in armGroup:
                if arm['ArmGroupInterventionList']['ArmGroupInterventionName']:
                    drugList=arm['ArmGroupInterventionList']['ArmGroupInterventionName']
                    for drug in drugList:
                        if not includeDrug == '':
                            if includeDrug.lower() in drug.lower(): # Make drug string to lower case 
                                score+=1 # includeDrug
                        if not excludeDrug == '':
                            if excludeDrug.lower() in drug.lower():
                                score-=1 # excludeDrug

        study.update({'score':score})
    

app.run()

