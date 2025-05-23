#!/usr/bin/python3
import yaml
import splunklib.client as client
import splunklib.results as results

# === [1] Sigma YAML -> Splunk Search convert === #
yaml_path = "Enter YAML file path"
output_path = "Enter output file path."

# Read Sigma YAML and parse
with open(yaml_path, "r") as f:
    sigma_rule = yaml.safe_load(f)

# detection -> selection -> Message|contains
conditions = sigma_rule.get("detection", {}).get("selection", {})
field = "Message"
terms = conditions.get("Message|contains", [])

# Create Splunk Query
source = 'source="WinEventLog:Microsoft-Windows-PowerShell/Operational"'
index = 'index=*'
splunk_conditions = " OR ".join([f'{field}="*{term}*"' for term in terms])
query = f"{index} {source} AND (({splunk_conditions})) | table {field}"

# Write to the file
with open(output_path, "w") as f:
    f.write(query)

# === [2] Write splunk search results === #
# Connection information
HOST = "localhost"
PORT = 8089
USERNAME = "Enter splunk admin username"
PASSWORD = "Enter splunk admin password"

# Connect Splunk
service = client.connect(
    host=HOST,
    port=PORT,
    username=USERNAME,
    password=PASSWORD
)

# Read from file and output
with open(output_path, "r") as f:
    search_query = "search " + f.read().strip()

search_options = {"earliest_time": "@d"}
results_stream = service.jobs.oneshot(search_query, **search_options)
reader = results.ResultsReader(results_stream)

# Results
print("\n--- Splunk Results ---")
for result in reader:
    if isinstance(result, dict):
        print(f"{field}: {result.get(field)}")
