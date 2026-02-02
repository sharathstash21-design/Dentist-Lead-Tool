import requests
import json

def search_google_social(industry, city, platform):
    url = "https://google.serper.dev/search"
    
    # This query finds specific social profiles with phone numbers
    payload = json.dumps({
      "q": f'site:{platform} "{industry}" "{city}" "+91"'
    })
    
    headers = {
      'X-API-KEY': '7ab11ec8c0050913c11a96062dc1e295af9743f0', # Put your key here
      'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        results = response.json()
        
        leads = []
        # Serper gives us clean data that Google won't block
        for result in results.get('organic', []):
            snippet = result.get('snippet', '')
            phone = re.search(r'[6-9]\d{9}', snippet)
            if phone:
                leads.append({
                    "Name": result.get('title', 'Dentist'),
                    "Phone": phone.group(),
                    "Platform": platform,
                    "Link": f"https://wa.me/91{phone.group()}"
                })
        return leads
    except:
        return []
