
import requests
import jwt
from datetime import *
import pytz
import time
import notify2
import os
import pause
import yaml
import sys

os.environ['DISPLAY'] = ':0'




def pay(token, headers, id_parking):
    r = requests.get("https://consumer.paybyphoneapis.com/payment/accounts",
            headers=headers)
    paymentAccountId = r.json()[0]["id"]
    r = requests.get(f"https://consumer.paybyphoneapis.com/parking/locations/{code_postal}/rateOptions?parkingAccountId={id_parking}&licensePlate={licenseplate}",
            headers=headers)
    id_rate = r.json()[0]["rateOptionId"]
    r = requests.get(f"https://consumer.paybyphoneapis.com/parking/accounts/{id_parking}/quote?licensePlate={licenseplate}&locationId={code_postal}&rateOptionId={id_rate}&durationTimeUnit=Days&durationQuantity={renew_day}&isParkUntil=false",
            headers=headers)
    start_time = datetime.strptime(r.json()["parkingStartTime"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    #start_time += timedelta(hours=1)
    start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    headers["X-Pbp-ClientType"] = "WebApp"

    r = requests.post(f"https://consumer.paybyphoneapis.com/parking/accounts/{id_parking}/sessions/",
            data = {"licensePlate" : licenseplate,
                    "locationId"   : code_postal,
                    "stall"        : "",
                    "rateOptionId" : id_rate,
                    "startTime"    : start_time,
                    "quoteId"      : r.json()["quoteId"],
                    "duration"     : {"timeUnit":"days","quantity":renew_day},
                    "paymentMethod": {"paymentMethodType":"PaymentAccount",
                        "payload":
                            {"paymentAccountId": paymentAccountId,"cvv":""}}},
                    headers=headers)
    n.set_urgency(notify2.URGENCY_NORMAL)

def check_pay():
    # Connection
    r = requests.post('https://consumer.paybyphoneapis.com/identity/token',
            data = {'grant_type':'password',
                    'username': USERNAME,
                    'password': PASSWORD,
                    'client_id': 'paybyphone_webapp'})


    # Connection data
    token = r.json()["access_token"]
    jwt_decoded = jwt.decode(token, verify=False)
    headers = {'Authorization': f"Bearer {token}",
               'x-pbp-version': '2',
               'Content-Type' : 'application/json'}

    # Check in how many time the program should payo
    r = requests.get("https://consumer.paybyphoneapis.com/parking/accounts",
        headers=headers)

    id_parking = r.json()[0]["id"]

    r = \
        requests.get(f"https://consumer.paybyphoneapis.com/parking/accounts/{id_parking}/sessions?periodType=Current",
                     headers=headers)

    # if no data is answer parking is free
    if r.json() == []:
        print("you should pay")
        pay(token, headers, id_parking)

    # else continue to check
    deadline = r.json()[0]['expireTime']

    deadline = datetime.strptime(deadline, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)

    wait = deadline - datetime.now(timezone.utc)
    wait = wait - timedelta(microseconds=wait.microseconds)
    n.update("PayByphone", str(wait))

    n.show()

    # print a message in function of time the program should wait
    if wait > timedelta(days=1):
        pause.until(datetime.now() + timedelta(days=1))
    elif wait > timedelta(hours=1):
        pause.until(datetime.now() + timedelta(hours=1))
    else:
        n.set_urgency(notify2.URGENCY_CRITICAL)
        waiting = wait
        while waiting.total_seconds() > 0:
            n.update("PayByphone", str(waiting))
            n.show()
            time.sleep(60)
            waiting -= timedelta(seconds=60)



if __name__ == "__main__":
    with open("/var/lib/paybyphones/config.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            USERNAME = config["USERNAME"]
            PASSWORD = config["PASSWORD"]
            code_postal = config["code_postal"]
            licenseplate = config["licenseplate"]
            renew_day = config["renew_day"]
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

    notify2.init("Paybyphones autopay")
    n = notify2.Notification(None) 
    n.set_urgency(notify2.URGENCY_NORMAL)

    while True:
        check_pay()
