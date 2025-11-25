import pdfplumber
import pandas as pd

# --- CONFIGURATION ---
pdf_file = "../data/ndrrmc/_Breakdown__Final_Report_for_Taal_Volcano_Eruption_2020.pdf" 
HEADER_SEARCH_DISTANCE = 80 
ALIGNMENT_TOLERANCE = 5  # Pixels of tolerance for centering checks

def get_text_alignment_and_case(page, cell_bbox):
    """
    Analyzes text within a cell bbox to determine:
    1. Alignment (Left, Center, Right)
    2. Casing (UPPER, Title, Mixed)
    3. The actual text content
    """
    if not cell_bbox:
        return None, None, ""

    # Crop the page to the specific cell
    try:
        cell_crop = page.crop(cell_bbox)
        words = cell_crop.extract_words()
    except ValueError:
        return None, None, "" # Handle edge cases where crop is invalid

    if not words:
        return None, None, ""

    # Reconstruct the text line
    text = " ".join([w['text'] for w in words]).strip()
    
    # --- GEOMETRY CALCULATIONS ---
    # Get bounds of the cell
    cell_x0, _, cell_x1, _ = cell_bbox
    cell_width = cell_x1 - cell_x0
    
    # Get bounds of the text content inside
    text_x0 = min([w['x0'] for w in words])
    text_x1 = max([w['x1'] for w in words])
    
    # Calculate margins
    left_margin = text_x0 - cell_x0
    right_margin = cell_x1 - text_x1
    
    # --- ALIGNMENT LOGIC ---
    alignment = "UNKNOWN"
    
    # Check Center: Left and Right margins are roughly equal
    if abs(left_margin - right_margin) < ALIGNMENT_TOLERANCE:
        alignment = "CENTER"
    # Check Left: Left margin is small
    elif left_margin < ALIGNMENT_TOLERANCE * 2: # *2 to be a bit lenient
        alignment = "LEFT"
    # Check Right: Right margin is small
    elif right_margin < ALIGNMENT_TOLERANCE * 2:
        alignment = "RIGHT"
        
    # --- CASING LOGIC ---
    case_type = "MIXED"
    if text.isupper():
        case_type = "UPPER"
    elif text.istitle():
        case_type = "TITLE" # Sentence case often looks like Title Case in lists
        
    return alignment, case_type, text

print(f"Processing {pdf_file}...")
all_rows_data = []

# State variables for the "Fill Down" logic
current_region = None
current_province = None
current_muni = None
current_barangay = None
current_title = "Unknown_Section"

with pdfplumber.open(pdf_file) as pdf:
    for i, page in enumerate(pdf.pages):
        # 1. Find tables based on lines
        tables_found = page.find_tables(
            table_settings={
                "vertical_strategy": "lines", 
                "horizontal_strategy": "lines",
                "snap_tolerance": 5,
            }
        )
        
        if tables_found:
            print(f"Page {i+1}: Found {len(tables_found)} table(s)")
        
        for table_obj in tables_found:
            # --- HEADER DETECTION  ---
            x0, top, x1, bottom = table_obj.bbox
            search_top = max(0, top - HEADER_SEARCH_DISTANCE)
            try:
                header_text = page.crop((0, search_top, page.width, top)).extract_text() or ""
                lines = [line.strip() for line in header_text.split('\n') if line.strip()]
                if lines:
                    potential_title = lines[-1]
                    if potential_title.isupper() or len(potential_title) < 100:
                        current_title = potential_title
            except Exception:
                pass 

            # --- ADVANCED ROW PROCESSING ---
            # table_obj.rows contains the geometry (bboxes) of the cells
            # table_obj.extract() contains the simple text
            
            # We assume the first column (index 0) is the Location column
            row_geometries = table_obj.rows
            extracted_text_rows = table_obj.extract()

            # Iterate through rows
            for row_obj, text_data in zip(row_geometries, extracted_text_rows):
                if not row_obj.cells: continue
                
                # Get the geometry of the first cell (Location Column)
                loc_cell_bbox = row_obj.cells[0]

                # Analyze the visual properties of the first column
                align, casing, text = get_text_alignment_and_case(page, loc_cell_bbox)
                
                # Skip header rows inside the table (e.g. "REGION | PROVINCE...")
                if text and "REGION" in text and "PROVINCE" in text:
                    continue
                
                if not text:
                    # If text is empty, it might be a breakdown row for the previous location
                    # We keep the current state variables as they are
                    pass
                else:
                    # --- CLASSIFICATION LOGIC  ---
                    # 1. Region: Centered + All Caps
                    if align == "CENTER" and casing == "UPPER":
                        current_region = text
                        current_province = None
                        current_muni = None
                        current_barangay = None
                        
                    # 2. Province: Left-Aligned + All Caps
                    elif align == "LEFT" and casing == "UPPER":
                        current_province = text
                        current_muni = None
                        current_barangay = None
                        
                    # 3. Municipality/City: Centered + Sentence/Title Case
                    # (Adding 'UPPER' check skip because specific cities might be caps, 
                    # but strictly following rule: Centered + !Upper)
                    elif align == "CENTER" and casing != "UPPER":
                        current_muni = text
                        current_barangay = None
                        
                    # 4. Barangay: Right-Aligned
                    elif align == "RIGHT":
                        current_barangay = text

                    # Fallback/Heuristics if alignment detection is fuzzy:
                
                # Create the structured row
                row_dict = {
                    "Page_Num": i + 1,
                    "Detected_Title": current_title,
                    "Region": current_region,
                    "Province": current_province,
                    "City_Municipality": current_muni,
                    "Barangay": current_barangay,
                }
                
                # Add the rest of the columns dynamically
                # We start from index 1 because index 0 was the specific location column we parsed
                for col_idx, cell_text in enumerate(text_data):
                    if col_idx == 0: continue # We handled column 0 manually
                    clean_text = cell_text.replace('\n', ' ').strip() if cell_text else ""
                    row_dict[f"Column_{col_idx}"] = clean_text
                
                all_rows_data.append(row_dict)

# --- SAVE RESULTS ---
if all_rows_data:
    final_df = pd.DataFrame(all_rows_data)
    
    # Remove rows that are completely empty (optional)
    final_df = final_df.dropna(subset=[col for col in final_df.columns if "Column" in col], how='all')

    output_filename = "hierarchical_parsed.csv"
    final_df.to_csv(output_filename, index=False)
    print(f"\n🎉 SUCCESS! Processed {len(pdf.pages)} pages.")
    print(f"Extracted {len(final_df)} structured rows.")
    print(f"Data saved to: {output_filename}")
    
    # Preview
    print(final_df[['Region', 'Province', 'City_Municipality', 'Barangay']].head(10))
else:
    print("No data extracted.")