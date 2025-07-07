import streamlit as st
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
import yaml

st.set_page_config(page_title="Sigma to Splunk", layout="wide")
st.title("🛡️ Sigma → Splunk Query Converter")

st.markdown("""
Bu uygulama Sigma kurallarını Splunk sorgularına dönüştürür. 
Sigma kuralınızı aşağıdaki metin alanına yapıştırın ve "Splunk Query Oluştur" butonuna tıklayın.
""")

sigma_input = st.text_area("Sigma Kuralını Yapıştır", height=300, help="YAML formatında Sigma kuralını buraya yapıştırın")

if st.button("🚀 Splunk Query Oluştur"):
    if not sigma_input.strip():
        st.warning("Lütfen bir Sigma kuralı girin.")
    else:
        try:
            # Parse the YAML input
            sigma_dict = yaml.safe_load(sigma_input)
            
            # Create SigmaRule object
            sigma_rule = SigmaRule.from_dict(sigma_dict)
            
            # Create SigmaCollection with the rule
            collection = SigmaCollection([sigma_rule])
            
            # Create Splunk backend
            backend = SplunkBackend()
            
            # Convert collection to Splunk queries
            queries = backend.convert(collection)
            
            # Display results
            st.success("✅ Sigma kuralı başarıyla Splunk sorgusuna dönüştürüldi!")
            
            for i, query in enumerate(queries, 1):
                st.subheader(f"Splunk Query {i}:")
                st.code(query, language='splunk')
                
                # Add copy to clipboard functionality using st.text_area (readonly)
                st.text_area(f"Query {i} (kopyalamak için seçin):", value=str(query), height=100, key=f"copy_area_{i}")

        except yaml.YAMLError as e:
            st.error(f"YAML parse hatası: {str(e)}")
        except Exception as e:
            st.error(f"Hata oluştu: {str(e)}")
            st.error("Lütfen Sigma kuralının doğru YAML formatında olduğundan emin olun.")
            
# Add sidebar with example
with st.sidebar:
    st.header("📖 Örnek Sigma Kuralı")
    st.markdown("Aşağıda örnek bir Sigma kuralı bulabilirsiniz:")
    
    example_rule = """title: Suspicious PowerShell Command
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
level: high"""
    
    st.code(example_rule, language='yaml')
    
    if st.button("📝 Örneği Kullan"):
        st.session_state.example_used = True
        
    # Add instructions
    st.header("📋 Kullanım Talimatları")
    st.markdown("""
    1. Sigma kuralınızı YAML formatında sol taraftaki metin alanına yapıştırın
    2. "Splunk Query Oluştur" butonuna tıklayın
    3. Oluşturulan Splunk sorgusunu kopyalayın
    4. Splunk'ta kullanın!
    """)
    
    st.header("ℹ️ Hakkında")
    st.markdown("""
    Bu uygulama [pySigma](https://github.com/SigmaHQ/pySigma) kütüphanesini kullanarak 
    Sigma kurallarını Splunk sorgularına dönüştürür.
    """)