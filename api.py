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


def getTrials(keyword, numResults): #(fullStudies):
    
    # Use keyword and numResults to query the API
    key = keyword.split()
    search = ""
    lastInd = len(key) - 1

    for i in range(0, len(key)):
        search = search + key[i]
        if i != lastInd:
            search += "+"

    queryString = "https://clinicaltrials.gov/api/query/full_studies?expr=" + search + "&min_rnk=1&max_rnk=" + numResults + "&fmt=json"

    print(queryString)

    response = requests.get(queryString)

    fullStudiesResponse=response.json()['FullStudiesResponse']
    fullStudies=fullStudiesResponse['FullStudies']
    # Frontend should pass fullStudies to backend, here I just call directly from API
    
    return fullStudies
    
def applySortingCriteria(trialdata):
    #setUpScore(trialdata, '19', 'Breast Cancer', 'breast cancer', 'CNS', True, False, 'Palbociclib', 'Placebo')
    #sortTrials(trialdata)
    a = "hello"

# Sort Trials By Criteria Route
@app.route('/api/sortTrialsByCriteria', methods=['GET'])
def api_sortTrialsByCriteria():

    keyword = request.form['keyword']
    numresults = request.form['numResults']

    print(keyword + ", " + numresults)
    # get trial data based on keyword and numResults from front end request
    trialdata = getTrials(keyword, numresults)

    applySortingCriteria(trialdata)

    return jsonify(
        status=True,
        message="Successfully sorted trials",
        data=trialdata
    )

# sort trials from highest score to lowest (if there is no score, put this trial to tail)
def sortTrials(fullStudies):
    def score(fullStudies):
        try:
            return int(fullStudies['score'])
        except KeyError:
            return float('-inf')
    fullStudies.sort(key=score, reverse=True)

# Assign score to all trials
def setUpScore(fullStudies, age, condition, inclusion, exclusion, ongoing, completed, includeDrug, excludeDrug):
    for study in fullStudies:
        try:
            protocolSection=study['Study']['ProtocolSection']
        except KeyError:
            print("No Protocol Section")
            continue
            
        score=0
        if protocolSection['EligibilityModule']:
            eligibilityModule=protocolSection['EligibilityModule']
            # Check if age is in range
            try:
                minAge = eligibilityModule['MinimumAge']
                intMinAge = int(minAge.split(' ')[0])
                if not age == '':
                    if int(age)>intMinAge:
                        score+=1
            except KeyError:
                print("No minimumAge Section")
            
            # Check eligibilityCriteria
            try:
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
            except KeyError:
                print("No EligibilityCriteria Section")
            
            
        # Check if this condition exists
        try:
            conList=protocolSection['ConditionsModule']['ConditionList']['Condition']
            if not condtion == '':
                if condtion in conList:
                    score+=1
        except KeyError:
            print("No condition Section")
        
        
        try:
            completedDate=protocolSection['StatusModule']['CompletionDateStruct']['CompletionDateType']
            # Check completed
            if completed:
                if completedDate=='Actual':
                    score+=1
                    
            # Check ongoing
            if ongoing:
                if completedDate=='Anticipated':
                    score+=1
        except KeyError:
            print("No completion date Section")
            
        
        try:
            # Check includeDrug and excludeDrug
            armGroup=protocolSection['ArmsInterventionsModule']['ArmGroupList']['ArmGroup']
            for arm in armGroup:
                drugList=arm['ArmGroupInterventionList']['ArmGroupInterventionName']
                for drug in drugList:
                    if not includeDrug == '':
                        if includeDrug.lower() in drug.lower(): # Make drug string to lower case 
                            score+=1 # includeDrug
                    if not excludeDrug == '':
                        if excludeDrug.lower() in drug.lower():
                            score-=1 # excludeDrug
        except KeyError:
            print("No includeDrug and excludeDrug Section")
            
        study.update({'score':score})
    

app.run()

