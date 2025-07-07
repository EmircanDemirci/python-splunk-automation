#!/usr/bin/env python3

from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
import yaml

def test_conversion():
    # Test rule from your original code
    test_rule = """
title: Suspicious PowerShell Command
id: 12345678-1234-1234-1234-123456789012
status: test
description: Detects suspicious PowerShell commands
references:
    - https://example.com
author: Security Team
date: 2024/01/01
tags:
    - attack.execution
    - attack.t1059.001
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\\powershell.exe'
        CommandLine|contains:
            - 'Invoke-Expression'
            - 'DownloadString'
            - 'IEX'
    condition: selection
falsepositives:
    - Unknown
level: high
"""

    try:
        print("🔄 Testing Sigma to Splunk conversion...")
        
        # Parse YAML
        sigma_dict = yaml.safe_load(test_rule)
        print("✅ YAML parsed successfully")
        
        # Create SigmaRule object
        sigma_rule = SigmaRule.from_dict(sigma_dict)
        print("✅ SigmaRule created successfully")
        
        # Create SigmaCollection
        collection = SigmaCollection([sigma_rule])
        print("✅ SigmaCollection created successfully")
        
        # Create Splunk backend
        backend = SplunkBackend()
        print("✅ SplunkBackend created successfully")
        
        # Convert to Splunk queries
        queries = backend.convert(collection)
        print("✅ Conversion successful!")
        
        print(f"\n📊 Generated {len(queries)} Splunk quer{'y' if len(queries) == 1 else 'ies'}:")
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Query {i}:")
            print("-" * 50)
            print(query)
            print("-" * 50)
            
        print("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_conversion()