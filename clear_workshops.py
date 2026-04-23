import requests

# Clear workshop 1 (Филе) and 2 (Котлеты)
workshops_to_clear = [1, 2]

for workshop_id in workshops_to_clear:
    try:
        response = requests.post(f"http://localhost:8000/clear-workshop/{workshop_id}")
        print(f"Workshop {workshop_id}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error clearing workshop {workshop_id}: {e}")
