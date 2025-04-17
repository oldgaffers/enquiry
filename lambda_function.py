import json
import smtplib
import boto3
from datetime import datetime, timedelta
from email.message import EmailMessage

ssm = boto3.client('ssm')
s3 = boto3.client('s3')

fishermen = ['joger7536@gmail.com','amira.awwab18@gmail.com','j.leonhardx@gmail.com','asmawatilenggi75@gmail.com','soverson@aol.com']
 
def json_from_object(bucket, key):
    r = s3.get_object(Bucket=bucket, Key=key)
    text = r["Body"].read().decode('utf-8')
    return json.loads(text)
    
def gold():
    d = datetime.now()
    prev = (d - timedelta(days=1)).date().isoformat()
    return json_from_object('boatregister', f'gold/{prev}.json')

def sendmail(mail):
    # print('sendmail', mail)
    r = ssm.get_parameter(Name='MAIL_HOST')
    host = r['Parameter']['Value']
    r = ssm.get_parameter(Name='MAIL_PORT')
    port = int(r['Parameter']['Value'])
    r = ssm.get_parameter(Name='MAIL_USER')
    user = r['Parameter']['Value']
    r = ssm.get_parameter(Name='MAIL_PASSWORD', WithDecryption=True)
    password = r['Parameter']['Value']
    server = smtplib.SMTP_SSL(host, port)
    server.login(user, password)
    fromaddr = user
    toaddrs  = []
    msg = EmailMessage()
    msg['From'] = fromaddr
    if 'to' in mail:
        msg['To'] = ', '.join(mail['to'])
        toaddrs.extend(mail['to'])
    if 'cc' in mail:
        msg['Cc'] = ', '.join(mail['cc'])
        toaddrs.extend(mail['cc'])
    if 'bcc' in mail:
        toaddrs.extend(mail['bcc'])
    toaddrs.append(user) # make sure boatregister is included
    msg['Subject'] = mail['boat_name']
    msg.set_content(mail['message'])
    server.sendmail(fromaddr, toaddrs, msg.as_string())
    server.quit()
    # print('mail sent', json.dumps(headers))
    return {
        'statusCode': 200,
        'body': json.dumps('your mail has been sent')
    }
    
def getOwners(owners):
    l = [n['id'] for n in owners]
    g = gold()
    n = [m for m in g if m['ID'] in l]
    return n
    
def getDear(owners):
    n = [o['Firstname'] for o in owners]
    if len(n) > 0:
        return ' and '.join(n)
    return "folks"

def handle(event):
    if 'owners' in event:
        owners = getOwners(event['owners'])
        dear = getDear(owners)
        your = 'your '
    else:
        dear = 'boat register editors'
        your = ''
    if 'member' in event and event['member']:
        name = 'an OGA member'
    else:
        name = 'someone'
    if 'name' in event and len(event['name'].strip()) > 0:
        name = event['name']
    text = [
        f"Dear {dear},",
        f"{name} would like to contact you about {your}boat {event['boat_name']}, OGA No {event['oga_no']} regarding:",
        f"{event['text']}."
    ]
    text.append(f"They can be contacted at {event['email']}.")
    text.append("If our records are out of date and this email is not appropriate, please accept our apologies.")
    text.append("You can contact us by replying to this email or via our website oga.org.uk.")
    mail = { 'boat_name': event['boat_name']}
    mail['message'] = "\n".join(text)
    mail['to'] = [o['Email'] for o in owners]
    sendmail(mail)

def lambda_handler(event, context):
    # print(json.dumps(event))
    if 'Records' in event:
        for record in event['Records']:
            handle(json.loads(record['Sns']['Message']))
    else:
        if event['email'] not in fishermen:
            handle(event)
