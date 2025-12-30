import requests
import json
import logging
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraService:
    def __init__(self):
        self.base_url = settings.JIRA_URL
        self.email = settings.JIRA_EMAIL
        self.token = settings.JIRA_API_TOKEN
        # Requests handles Basic Auth automatically with this tuple
        self.auth = (self.email, self.token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def create_test_case(self, project_key: str, summary: str, description: str, parent_key: str = None):
        # 1. Clean Inputs
        if parent_key:
            parent_key = parent_key.strip()
        
        logger.info(f"Initiating Jira export. Project: {project_key}, Parent: {parent_key}")

        url = f"{self.base_url}/rest/api/3/issue"
        
        # 2. Construct ADF Description (Required for Jira Cloud)
        description_adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description or "No description provided."
                        }
                    ]
                }
            ]
        }

        # 3. Build Payload
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description_adf,
                "issuetype": {"name": "Task"} # Default
            }
        }

        # 4. Handle Subtask Logic
        if parent_key:
            payload["fields"]["parent"] = {"key": parent_key}
            payload["fields"]["issuetype"]["name"] = "Subtask"
            logger.info(f"Linking issue as Subtask to parent: {parent_key}")
        else:
            logger.info("No parent key provided. Creating as independent Task.")

        try:
            response = requests.post(
                url,
                json=payload,
                auth=self.auth,
                headers=self.headers
            )

            if response.status_code == 201:
                data = response.json()
                key = data.get("key")
                logger.info(f"Successfully created Jira ticket: {key}")
                return {"key": key, "url": f"{self.base_url}/browse/{key}"}
            else:
                logger.error(f"Jira API Failed ({response.status_code}): {response.text}")
                return {"error": f"Jira Error {response.status_code}: {response.text}"}

        except Exception as e:
            logger.exception("Exception occurred during Jira export")
            return {"error": str(e)}
