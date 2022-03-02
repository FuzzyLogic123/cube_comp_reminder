from datetime import datetime
from dateutil import parser
from datetime import timezone, datetime
import smtplib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from rich.console import Console
from rich.pretty import pprint

console = Console()

def scrape_wca():

    comp_info = []
    comp_links = []
    wca_url = "https://www.worldcubeassociation.org/competitions?utf8=✓&region=Australia&search=&state=present&year=all+years&from_date=&to_date=&delegate=&display=list"
    response = requests.get(wca_url)
    html = response.text

    soup = BeautifulSoup(html, 'html.parser')

    rows = soup.select('ul.list-group li.list-group-item')
    comp_location = None
    # print(rows[1])
    for row in rows:
        for comp_location_iter in row.select('div.location'):
            comp_location = comp_location_iter.get_text().strip()
            # print(comp_location)
        comp_details_links = row.select('div.competition-link a')
        for comp_details_link in comp_details_links:
            comp_link = urljoin(wca_url, comp_details_link.get('href'))
            # print(comp_link)
        if comp_location and "Melbourne" in comp_location:
            comp_links.append(comp_link)
        
    # print(comp_links)
    for link in comp_links:
        # print(link)
        response = requests.get(link)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        comp_due_dates = soup.select('span.wca-local-time[data-utc-time]')
        comp_dates = []
        for comp_date in comp_due_dates:
            comp_dates.append(comp_date['data-utc-time'])
        comp_name = soup.select('h3')[0].get_text().strip()
        comp_info.append({
            "name": comp_name,
            "dates": list(set(comp_dates))
        })
    # print(comp_info)
    return comp_info



def check_for_comp_reg(comp):
    comp_dates = comp["dates"]
    comp_name = comp["name"]
    comp_dates = [parser.isoparse(date) for date in comp_dates]
    registration_open = min(comp_dates)
    registration_close = max(comp_dates)
    now = datetime.now(timezone.utc)
    # now = datetime(2022, 2, 17)
    # now = now.replace(tzinfo=timezone.utc)

    # console.print(f'close: {registration_close}, open: {registration_open}, name:{comp_name}')
    if abs(now - registration_open).total_seconds() <= 24 * 60 * 60:
        print(comp_name)
        print(":smiley: [green3] The comp is open for registration")
        return {
            "name": comp_name,
            "register_open": registration_open,
            "register_close": registration_close
        }
    return False

def get_comps(comp_info):
    registers_available = []
    for comp in comp_info:
        is_register_required = check_for_comp_reg(comp)
        if is_register_required:
            registers_available.append(is_register_required)
    return registers_available


#if this returns a value then email said people with details
def send_email(registers_available):
    email_contents = ''
    if len(registers_available) == 1:
        email_contents += f"There is 1 comp cube comp available!"
    else:
        email_contents += f"There is {len(registers_available)} comps available"
        
    for comp in registers_available:
        email_contents += f'\nRegistration for {comp["name"]} opens {comp["register_open"].strftime("%b %d %Y %H:%M")} and closes {comp["register_close"].strftime("%b %d %Y %H:%M")}'
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login('cubecomp.reminder@gmail.com', '!CubeComp12')

    server.sendmail('cubecomp.reminder@gmail.com',['pat.e1@icloud.com', "hughjedwards@icloud.com"], email_contents)

def main():
    comp_info = scrape_wca()
    pprint(comp_info)
    registers_available = get_comps(comp_info)
    if len(registers_available) > 0:
        send_email(registers_available)

main()
