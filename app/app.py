from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import time
import joblib
import re
from custom.functions import position_group, get_domain_zone

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

# load model
clf = joblib.load('models/logistic_regression.joblib')
woe_encoder = joblib.load('preprocessing/woe_encoder.joblib')
std_scaler = joblib.load('preprocessing/std_scaler.joblib')

@app.route('/json', methods=['POST'])
def calc_score():
    try:
        # record start time of the routine
        begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        # receive input data in JSON format
        data = request.get_json()['app']

        # fill missing fields from application
        if data['faculty'] is None:
            data['faculty'] = 'MISSING'

        if data['emp_region'] is None:
            data['emp_region'] = 'MISSING'

        if data['emp_field'] is None:
            data['emp_field'] = 'MISSING'

        if data['exp_all'] is None:
            data['exp_all'] = 0

        if data['exp_loans'] is None:
            data['exp_loans'] = 0

        if data['emp_position'] is None:
            data['emp_position'] = 'інше'

        if data['income_period'] is None:
            data['income_period'] = 'MISSING'

        if data['cp_relation'] is None:
            data['cp_relation'] = 'MISSING'

        if data['emp_phone'] is None:
            data['emp_phone_code'] = 'MISSING'
        else:
            data['emp_phone_code'] = data['emp_phone'][2:5]

        if data['cp_phone'] is None:
            data['cp_phone_code'] = 'MISSING'
        else:
            data['cp_phone_code'] = data['cp_phone'][2:5]

        # transform fields
        data['emp_region_equal'] = (data['emp_region'] == data['reg_region'])
        data['mphone_code'] = data['mphone'][2:5]
        data['age'] = (pd.Timestamp.today() - pd.to_datetime(data['birthday'])).days
        data['passport_age'] = (pd.Timestamp.today() - pd.to_datetime(data['passport_date'])).days
        data['reg_addr_age'] = (pd.Timestamp.today() - pd.to_datetime(data['reg_addr_date'])).days
        data['days_to_income'] = (pd.to_datetime(data['income_next']) - pd.to_datetime(data['start_time'])).days
        data['start_month'] = pd.to_datetime(data['start_time']).month
        data['start_day'] = pd.to_datetime(data['start_time']).day
        data['start_day_of_week'] = pd.to_datetime(data['start_time']).weekday()
        data['start_hour'] = pd.to_datetime(data['start_time']).hour
        data['duration'] = (pd.to_datetime(data['end_time']) - pd.to_datetime(data['start_time'])).seconds
        data['email'] = data['email'].lower()
        data['prefix'], data['domain'] = data['email'].split('@')
        data['email_prefix_length'] = len(data['prefix'])
        data['email_prefix_digits'] = sum([c.isdigit() for c in data['prefix']])
        data['email_prefix_letters'] = sum([c.isalpha() for c in data['prefix']])
        data['email_prefix_symbols'] = data['email_prefix_length'] - data['email_prefix_digits'] - data['email_prefix_letters']
        data['domain_zone'] = get_domain_zone(data['domain'])
        data['emp_position'] = position_group(data['emp_position'])
        data['exp_all_to_income'] = data['exp_all'] / data['income']
        data['exp_loans_to_income'] = data['exp_loans'] / data['income']

        if data['emp_type'] != 'UNEMPLOYED':
            data['income_source'] = data['emp_type']

        data['has_emp_edrpou'] = False if (data['emp_edrpou'] is None) or (data['emp_edrpou'] == '') else True
        data['has_emp_flat'] = False
        data['has_emp_pcode'] = False if (data['emp_pcode'] is None) or (data['emp_pcode'] == '') else True
        data['has_reg_pcode'] = False if (data['reg_pcode'] is None) or (data['reg_pcode'] == '') else True
        data['has_liv_pcode'] = False if (data['liv_pcode'] is None) or (data['liv_pcode'] == '') else True
        data['has_reg_flat'] = False
        data['has_liv_flat'] = False
        data['has_promo_code'] = False if (data['promo_code'] is None) or (data['promo_code'] == '') else True


        # drop unused fields
        fields = ['emp_region', 'emp_phone', 'cp_phone', 'mphone', 'birthday', 'reg_addr_date', 'income_next',
                  'passport_date', 'start_time', 'end_time', 'email', 'prefix', 'emp_type', 'emp_edrpou',
                  'emp_pcode', 'reg_pcode', 'liv_pcode', 'promo_code']
        for field in fields:
            del data[field]

        # create DataFrame
        X = pd.Series(data).to_frame().T

        # fake fields for encoder and transformer !!! TEMPORARILY SOLUTION !!!
        X['liv_region'] = 'MISSING'
        X['emp_region'] = 'MISSING'
        X['has_liv_pcode'] = False
        X['has_liv_flat'] = False
        X['liv_addr_age'] = 0
        X['exp_loans_to_income'] = 0
        X['email_prefix_letters'] = 0

        # encode data
        X = woe_encoder.transform(X)

        # scale data
        cols_order = ['credit_term', 'credit_amount', 'know_source', 'loan_purpose',
           'social_status', 'family_status', 'children16', 'education', 'faculty',
           'gender', 'passport_type', 'reg_region', 'reg_status', 'liv_equal',
           'liv_region', 'liv_status', 'emp_region', 'emp_field', 'emp_position',
           'exp_loans', 'exp_all', 'income', 'income_period', 'income_source',
           'cp_relation', 'mphone_code', 'emp_phone_code', 'cp_phone_code',
           'has_reg_pcode', 'has_liv_pcode', 'has_emp_pcode', 'has_reg_flat',
           'has_liv_flat', 'has_emp_flat', 'has_emp_edrpou', 'has_promo_code',
           'app_rank', 'app_count', 'emp_region_equal', 'age', 'passport_age',
           'reg_addr_age', 'liv_addr_age', 'days_to_income', 'start_month',
           'start_day', 'start_day_of_week', 'start_hour', 'duration', 'domain',
           'email_prefix_length', 'email_prefix_digits', 'email_prefix_letters',
           'email_prefix_symbols', 'domain_zone', 'exp_all_to_income',
           'exp_loans_to_income']
        X = pd.DataFrame(
            std_scaler.transform(X[cols_order]), # reorder columns for scaling
            columns=cols_order
        )

        # drop unused fields
        X.drop(['liv_region', 'emp_region', 'has_liv_pcode', 'has_liv_flat', 'liv_addr_age',
                 'exp_loans_to_income','email_prefix_letters'],
                 axis='columns', inplace=True)

        # make predictions
        decision = 'reject' if clf.predict(X)[0] else 'accept'
        score = (1 - clf.predict_proba(X)[0,0])*1000

        # record end time of the routine
        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        # generate response
        response = {
            'routine': 'calc_score',
            'version': '1.1.0',
            'startedAt': begin_time,
            'finishedAt': end_time,
            'response': {
                'decision': decision,
                'score': score
            }
        }

    except Exception as e:
        # record end time of the routine
        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        # generate response
        response = {
            'routine': 'calc_score',
            'version': '1.1.0',
            'startedAt': begin_time,
            'finishedAt': end_time,
            'response': {
                'error': repr(e)
            }
        }

    return jsonify(response)

@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
