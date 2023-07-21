import pandas as pd
import requests as re

# URL for PubChem API
API_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Function to normalize drug names by getting synonyms from PubChem
def normalize_drug_name(drug_name):
    # Make an API request to retrieve drug synonyms
    response = re.get(API_BASE_URL + "/compound/name/{}/synonyms/JSON".format(drug_name))
    if response.status_code == 200:
        data = response.json()
        if "InformationList" in data and "Information" in data["InformationList"]:
            synonyms = data["InformationList"]["Information"][0]["Synonym"]
            if isinstance(synonyms, list):
                normalized_name = synonyms[0]
                return normalized_name
    return None

# Function to get compound properties and save them to an Excel file
def drug_properties_excel_save(original_set, output_file):
    # Normalize drug names using the provided function
    normalized_set = [normalize_drug_name(drug_name) for drug_name in original_set]

    # Create a DataFrame with original and normalized drug names
    df = pd.DataFrame({'original_names': original_set, 'normalized_set': normalized_set})

    # Drop duplicates based on the 'normalized_set' column
    df = df.drop_duplicates(subset='normalized_set')

    # Initialize lists to store compound properties
    molecular_weight_set = []
    canonical_smiles_set = []
    xlogp_set = []
    LogP_class = []

    # Loop through the normalized drug names and retrieve compound properties from PubChem
    for normalized_name in df['normalized_set']:
        if normalized_name:
            # Make an API request to retrieve compound properties
            response = re.get(API_BASE_URL + "/compound/name/{}/property/MolecularWeight,CanonicalSMILES,XLogP/JSON".format(normalized_name))
            if response.status_code == 200:
                data = response.json()
                if "PropertyTable" in data and "Properties" in data["PropertyTable"]:
                    compound = data["PropertyTable"]["Properties"][0]
                    molecular_weight_set.append(compound.get("MolecularWeight"))
                    canonical_smiles_set.append(compound.get("CanonicalSMILES"))
                    xlogp = compound.get("XLogP")
                    xlogp_set.append(xlogp)
                    LogP_class.append(1 if xlogp > 0 else 0)
                else:
                    molecular_weight_set.append(None)
                    canonical_smiles_set.append(None)
                    xlogp_set.append(None)
                    LogP_class.append(None)

    # Add the compound properties to the DataFrame
    df['MolecularWeight'] = molecular_weight_set
    df['CanonicalSMILES'] = canonical_smiles_set
    df['XLogP'] = xlogp_set
    df['LogP_class'] = LogP_class

    # Convert "MolecularWeight" column to numeric type
    df['MolecularWeight'] = pd.to_numeric(df['MolecularWeight'])

    # Convert the 'normalized_set' column to uppercase
    df['normalized_set'] = df['normalized_set'].str.upper()

    # Add new columns ranking MolecularWeight and XLogP in ascending order
    df['MolecularWeightRank'] = df['MolecularWeight'].rank(ascending=True).astype(int)
    df['XLogPRank'] = df['XLogP'].rank(ascending=True).astype(int)

    # Save the DataFrame to an Excel file with two sheets
    with pd.ExcelWriter(output_file) as writer:
        df.to_excel(writer, sheet_name='Data', index=False)

        # Add a new sheet for calculating the rank
        rank_data = pd.DataFrame({
            'normalized_set': df['normalized_set'],
            'MolecularWeight': df['MolecularWeight'],
            'XLogP': df['XLogP']
        })
        rank_data.to_excel(writer, sheet_name='Features_rank', index=False)

    return df

# Example usage:
original_set = ["Adenosine", "Adenocard", "BG8967", "Bivalirudin", "BAYT006267", "diflucan", "ibrutinib", "PC-32765"]
output_file = 'Data_drug.xlsx'
df_with_properties = drug_properties_excel_save(original_set, output_file)