import yaml
import pytest
from collections import Counter


def test_unique_network_automation_folks():
    with open("bsky_users.yaml", "r") as file:
        data = yaml.safe_load(file)

    network_automation_folks = data["starterpacks"]["Network Automation Folks"]
    counter = Counter(network_automation_folks)
    duplicates = [item for item, count in counter.items() if count > 1]

    assert len(duplicates) == 0, f"Duplicate items found: {duplicates}"


if __name__ == "__main__":
    pytest.main()
