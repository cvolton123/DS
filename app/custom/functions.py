import re

def position_group(x):
    if x is None:
        return x
    elif (x.find('менедж') >= 0) or (x.find('менеж') >= 0):
        return 'менеджер'
    elif (x.find('директор') >= 0) or (x.find('діректор') >= 0):
        return 'директор'
    elif x.find('продав') >= 0:
        return 'продавець'
    elif (x.find('керівник') >= 0) or (x.find('руков') >= 0) or (x.find('начал') >= 0):
        return 'керівник'
    elif (x.find('воді') >= 0) or (x.find('такс') >= 0) or (x == 'водитель'):
        return 'водій'
    elif (x.find('власник') >= 0) or (x == 'собственник'):
        return 'власник'
    elif (x.find('оператор') >= 0):
        return 'оператор'
    elif (x.find('спеці') >= 0) or (x.find('специ') >= 0):
        return 'спеціаліст'
    elif (x.find('охорон') >= 0) or (x.find('охран') >= 0) or (x.find('комірник') >= 0):
        return 'охоронець/комірник'
    elif (x.find('каси') >= 0) or (x.find('касі') >= 0) or (x.find('касс') >= 0):
        return 'касир'
    elif (x.find('бухгал') >= 0) or (x.find('бугал') >= 0):
        return 'бухгалтер'
    elif (x.find('майстер') >= 0) or (x.find('мастер') >= 0) or (x.find('робочий') >= 0) or (x.find('робітник') >= 0):
        return 'майстер/робітник'
    elif (x.find('вчител') >= 0) or (x.find('учител') >= 0):
        return 'вчитель'
    else:
        return 'інше'

def get_domain_zone(x):
    dz = re.findall(r'[a-z]{2,}$', x)
    return dz[0] if len(dz) else 'None'