import pandas as pd

COLUMN_MAPPING = {
    "Main Event Disaster Type": "hasType",
    "Disaster Name": "eventName",
    "Date/Period": "startDate",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Main Area/s Affected / Location": "hasLocation",  
    "Additional Perils/Disaster Sub-Type Occurences (Compound Disaster, e.g. Typhoon Haiyan = rain + wind + storm surge)": "hasSubtype",
    "PREPAREDNESS_Announcements_Warnings Released / Status Alert or Alert/ State of Calamity": "declarationOfCalamity",
    "PREPAREDNESS_Evacuation_No. of Evacuation Centers": "evacuationCenters",
    "IMPACT_Number of Affected Areas_Barangays": "affectedBarangays",
    "IMPACT_Casualties_Dead_Total": "dead",
    "IMPACT_Casualties_Injured_Total": "injured",
    "IMPACT_Casualties_Missing_Total": "missing",
    "IMPACT_Affected_Families": "affectedFamilies",
    "IMPACT_Affected_Persons": "affectedPersons",
    "IMPACT_Evacuated_Families": "displacedFamilies",
    "IMPACT_Evacuated_Persons": "displacedPersons",
    "IMPACT_Damages to Properties_Houses_Fully": "totallyDamagedHouses",
    "IMPACT_Damages to Properties_Houses_Partially": "partiallyDamagedHouses",
    "IMPACT_Damages to Properties_Infrastructure (in Millions)": "infraDamageAmount",
    "IMPACT_Damages to Properties_Agriculture (in Millions)": "agricultureDamageAmount",
    "IMPACT_Damages to Properties_Private/Commercial (in Millions)": "commercialDamageAmount",
    "IMPACT_Status of Lifelines_Electricity or Power Supply": "powerAffected",
    "IMPACT_Status of Lifelines_Communication Lines": "communicationAffected",
    "IMPACT_Status of Lifelines_Transportation_Roads and Bridges": "roadAndBridgesAffected",
    "IMPACT_Status of Lifelines_Transportation_Seaports": "seaportsAffected",
    "IMPACT_Status of Lifelines_Transportation_Airports": "airportsAffected",
    "IMPACT_Status of Lifelines_Water_Dams and other Reservoirs": "areDamsAffected",
    "IMPACT_Status of Lifelines_Water_Tap": "isTapAffected",
    "RESPONSE AND RECOVERY_Allocated Funds for the Affected Area/s": "allocatedFunds",
    "RESPONSE AND RECOVERY_NGO-LGU Support Units Present": "agencyLGUsPresent",
    "RESPONSE AND RECOVERY_International Organizations Present": "internationalOrgsPresent",
    "RESPONSE AND RECOVERY_Amount of Donation from International Organizations (including local NGOs)": "amoungNGOs",
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Canned Goods, Rice, etc._Cost": "itemCostGoods",    # itemTypeOrNeeds: Canned Goods, Rice
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Canned Goods, Rice, etc._Quantity": "itemQtyGoods", # itemTypeOrNeeds: Canned Goods, Rice
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Water_Cost": "itemCostWater",    # itemTypeOrNeeds: Water
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Water_Quantity": "itemQtyWater", # itemTypeOrNeeds: Water
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Clothing_Cost": "itemCostClothing",    # itemTypeOrNeeds: Clothing
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Clothing_Quantity": "itemQtyClothing", # itemTypeOrNeeds: Clothing
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Medicine_Cost": "itemCostMedicine",    # itemTypeOrNeeds: Medicine
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Medicine_Quantity": "itemQtyMedicine", # itemTypeOrNeeds: Medicine
    "RESPONSE AND RECOVERY_Supply of Relief Goods_Items Not Specified (Cost)": "itemCostOthers", # itemTypeTypeOrNeeds: Others
    "REFERENCES (Authors. Year. Title. Journal/Book/Newspaper. Publisher, Place published. Pages. Website, Date Accessed)": "reference",
    "Detailed Description of Disaster Event": "OTHER [magnitude, remarks]"

}

COLUMNS_TO_CLEAN = {
    "date": "normalize_date",
    "location": "resolve_location",
}

def load_with_tiered_headers(path):
    """
    Load XLSX with 3–4 tier headers.
    Automatically stops merging deeper levels when columns become 'Unnamed'.
    """
    df = pd.read_excel(path, header=[3,4,5,6], nrows=50)

    new_cols = []
    for col_tuple in df.columns:

        cleaned = []
        for level in col_tuple:
            s = str(level).strip()

            if s.lower().startswith("unnamed") or s == "" or s == "nan":
                break  

            cleaned.append(s)

        merged = "_".join(cleaned)

        new_cols.append(merged)

    df.columns = new_cols
    return df

df = load_with_tiered_headers("../../data/geog-archive.xlsx")
df = df.rename(columns=COLUMN_MAPPING)

# print("\n=== XLSX column names ===")
# for col in df.columns:
#     print(col)

df = df[list(COLUMN_MAPPING.values())]
df = df.dropna(how='all')
df.to_csv('gda.csv', index=True)
