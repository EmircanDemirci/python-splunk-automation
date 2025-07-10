import streamlit as st
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
import yaml

st.set_page_config(page_title="Sigma to Splunk", layout="wide")
st.title("Sigma → Splunk Query Converter")
st.text("by venoox")

sigma_input = st.text_area("Sigma Kuralını Yapıştır", height=300, help="YAML formatında Sigma kuralını buraya yapıştırın")

if st.button("Splunk Query Oluştur"):
    if not sigma_input.strip():
        st.warning("Lütfen bir Sigma kuralı girin.")
    else:
        try:
            # Parse the YAML input
            sigma_dict = yaml.safe_load(sigma_input) #converts to dict like {"logsource":...,"detection":....}
            
            # Create SigmaRule object
            sigma_rule = SigmaRule.from_dict(sigma_dict)

            # Create SigmaCollection with the rule
            collection = SigmaCollection([sigma_rule])
            
            # Create Splunk backend
            backend = SplunkBackend() #this is a class for convert
            
            # Convert collection to Splunk queries
            queries = backend.convert(collection) #converting sigma to spl
            
            # Display results
            st.success("✅ Sigma kuralı başarıyla Splunk sorgusuna dönüştürüldü!")
            
            for i, query in enumerate(queries, 1): #getting query with index like this -> 1 query \n 2 query
                st.subheader(f"Splunk Query {i}:")
                st.code(query, language='splunk')
                
                # Add copy to clipboard functionality using st.text_area (readonly)
                st.text_area(f"Query {i}:", value=str(query), height=100, key=f"copy_area_{i}")

        except yaml.YAMLError as e:
            st.error(f"YAML parse hatası: {str(e)}")
        except Exception as e:
            st.error(f"Hata oluştu: {str(e)}")
            st.error("Lütfen Sigma kuralının doğru YAML formatında olduğundan emin olun.")
            