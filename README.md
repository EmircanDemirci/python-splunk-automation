# 🛡️ Sigma to Splunk Query Converter

A Streamlit web application that converts Sigma rules to Splunk queries using the pySigma library.

## ✨ Features

- **Easy-to-use web interface** built with Streamlit
- **Real-time conversion** from Sigma YAML rules to Splunk queries
- **Built-in example** Sigma rule for testing
- **Turkish language support** for user interface
- **Copy-friendly output** with text areas for easy copying
- **Error handling** with helpful error messages

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the Streamlit application:
   ```bash
   streamlit run sigma_to_splunk_app.py
   ```

3. Open your web browser and go to `http://localhost:8501`

## 📖 Usage

1. **Paste your Sigma rule** in YAML format into the text area
2. **Click "🚀 Splunk Query Oluştur"** to convert
3. **Copy the generated Splunk query** from the output area
4. **Use the query in Splunk**

### Example Sigma Rule

```yaml
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
        Image|endswith: '\powershell.exe'
        CommandLine|contains:
            - 'Invoke-Expression'
            - 'DownloadString'
            - 'IEX'
    condition: selection
falsepositives:
    - Unknown
level: high
```

### Generated Splunk Query

```splunk
Image="*\\powershell.exe" CommandLine IN ("*Invoke-Expression*", "*DownloadString*", "*IEX*")
```

## 🔧 Testing

You can test the conversion logic without the web interface by running:

```bash
python test_conversion.py
```

This will test the conversion with the example Sigma rule and display the results.

## 📋 Dependencies

- **streamlit**: Web application framework
- **pysigma**: Core Sigma rule processing library
- **pysigma-backend-splunk**: Splunk backend for pySigma
- **pyyaml**: YAML parsing library

## 🗂️ Files

- `sigma_to_splunk_app.py` - Main Streamlit application
- `test_conversion.py` - Test script to verify conversion logic
- `requirements.txt` - Python dependencies
- `README.md` - This documentation file
- `splunkautomation.py` - Original automation script (legacy)

## 🛠️ Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure you've activated the virtual environment and installed all dependencies
2. **YAML parse errors**: Ensure your Sigma rule is in valid YAML format
3. **Conversion errors**: Check that your Sigma rule follows the proper Sigma rule specification

### Error Messages

- **"YAML parse hatası"**: Your input is not valid YAML format
- **"Hata oluştu"**: General error - check your Sigma rule structure

## 🔄 Original Problem Solution

The original error `ModuleNotFoundError: No module named 'sigma.parser'` was resolved by:

1. **Installing the correct packages**: Using `pysigma` and `pysigma-backend-splunk` instead of the old API
2. **Using the correct imports**: 
   ```python
   from sigma.rule import SigmaRule
   from sigma.collection import SigmaCollection
   from sigma.backends.splunk import SplunkBackend
   ```
3. **Using SigmaCollection**: The backend expects a SigmaCollection, not a direct SigmaRule
4. **Setting up virtual environment**: Avoiding system package conflicts

## 📚 References

- [pySigma Documentation](https://github.com/SigmaHQ/pySigma)
- [Sigma Rule Specification](https://github.com/SigmaHQ/sigma/wiki/Specification)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 📄 License

This project is provided as-is for educational and security research purposes.
