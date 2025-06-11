import re
import pandas as pd
from bs4 import BeautifulSoup

FinalData = []

def extract_funnel_data(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        funnel_cards = soup.find_all('div', {'class': 'card-inner-container'})
        print(f"Found {len(funnel_cards)} funnel cards")
        
        all_funnels = {}
        for i, card in enumerate(funnel_cards):
            ScrappedData = {}
            try:
                # Get funnel title
                title_elem = card.find('div', {'class': 't-16'})
                date_subtitle = card.find('div', {'class': 'card-subtitle'})
                
                if not title_elem:
                    print(f"Warning: No title found for card {i+1}")
                    continue
                    
                title = title_elem.text.strip()
                print(f"\nProcessing funnel: {title}")
                ScrappedData["title"] = title
                
                if date_subtitle:
                    ScrappedData["date_range"] = date_subtitle.text.strip()
                
                # Extract all text elements that might contain data
                data_labels = card.find_all(['text', 'tspan'])
                step_labels = card.find_all('span', style=lambda value: value and 'position: absolute' in value)
                
                steps = [label.text.strip() for label in step_labels]
                conversion_data = []
                seen_texts = set()
                step_counter = 0
                
                # Process data labels
                for label in data_labels:
                    try:
                        text = label.text.strip()
                        if not text or text in seen_texts:
                            continue
                            
                        seen_texts.add(text)
                        ScrappedData[str(step_counter)] = text
                        step_counter += 1
                        
                        if '%' in text:
                            match = re.search(r'([\d.]+)%\s*\((\d+(?:,\d+)?)\)', text)
                            if match:
                                percentage = float(match.group(1))
                                users = int(match.group(2).replace(',', ''))
                                conversion_data.append({
                                    'conversion_rate': percentage,
                                    'users': users
                                })
                    except Exception as e:
                        print(f"Warning: Failed to parse data label '{label.text}': {str(e)}")
                        continue
                
                # Align steps with conversion data
                if conversion_data:
                    # If steps are fewer than conversion data, pad with generic labels
                    if len(steps) < len(conversion_data):
                        steps.extend([f"Step {j+1}" for j in range(len(steps), len(conversion_data))])
                    # If steps are more, truncate to match conversion data
                    steps = steps[:len(conversion_data)]
                    
                    df = pd.DataFrame({
                        'step': steps,
                        'users': [d['users'] for d in conversion_data],
                        'conversion_rate': [d['conversion_rate'] for d in conversion_data]
                    })
                    all_funnels[title] = df
                else:
                    print(f"Warning: No conversion data found for funnel {title}")
                
                FinalData.append(ScrappedData)
                
            except Exception as e:
                print(f"Error processing card {i+1}: {str(e)}")
                continue
        
        return all_funnels
        
    except Exception as e:
        print(f"Error in extract_funnel_data: {str(e)}")
        return {}

def analyze_funnels(html_content):
    try:
        funnels = extract_funnel_data(html_content)
        if not funnels:
            print("No funnel data was extracted")
            return {}
            
        for title, df in funnels.items():
            try:
                print(f"\nAnalyzing {title}")
                print("-" * 50)
                print(f"Steps in funnel: {len(df)}")
                print(f"Initial Users: {df['users'].iloc[0]:,}")
                print(f"Final Users: {df['users'].iloc[-1]:,}")
                
                df['dropoff'] = df['users'].shift(-1).fillna(df['users'].iloc[-1])
                df['dropoff_rate'] = (df['users'] - df['dropoff']) / df['users'] * 100
                
                for idx, row in df.iterrows():
                    print(f"\nStep {idx + 1}: {row['step']}")
                    print(f"Users: {row['users']:,}")
                    print(f"Conversion rate: {row['conversion_rate']:.2f}%")
                    if idx < len(df) - 1:
                        print(f"Drop-off: {row['users'] - df['users'].iloc[idx + 1]:,} users ({row['dropoff_rate']:.2f}%)")
            except Exception as e:
                print(f"Error analyzing funnel {title}: {str(e)}")
                continue
        
        return funnels
        
    except Exception as e:
        print(f"Error in analyze_funnels: {str(e)}")
        return {}

def process_data_and_create_excel(data, output_filename="output.xlsx"):
    print("Entering process_data_and_create_excel function...")
    excel_data = []
    
    for item in data:
        try:
            print(f"\nProcessing item: {item}")
            title = item.get('title', 'Unknown Title')
            
            row = [title]  # Use original title directly
            for step in ['0', '1', '2', '3']:
                if step in item:
                    text = item[step]
                    match = re.search(r'([\d.]+)%\s*\((\d+(?:,\d+)?)\)', text)
                    if match:
                        percentage = f"{match.group(1)}%"  # Add % symbol
                        value = format_number_with_commas(int(match.group(2).replace(',', '')))
                        row.extend([value, percentage])
                    else:
                        row.extend(['-', '-'])  # Handle non-percentage data
                else:
                    row.extend(['-', '-'])
            
            excel_data.append(row)
        except Exception as e:
            print(f"Error processing item {item.get('title', 'unknown')}: {str(e)}")
            continue
    
    columns = ['Title']
    for step in range(4):
        columns.extend([f'Value {step}', f'Percentage {step}'])
    
    df = pd.DataFrame(excel_data, columns=columns)
    df.to_excel(output_filename, index=False)
    print(f"Excel file '{output_filename}' created successfully.")

def format_number_with_commas(number):
    if isinstance(number, str):
        number = int(number)
    return "{:,}".format(number)

if __name__ == "__main__":
    filename = 'x.html'
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            html_content = f.read()
            print(f"Successfully read {len(html_content)} characters from file")
            
            if not html_content:
                print("Warning: File is empty")
            else:
                funnels = analyze_funnels(html_content)
                process_data_and_create_excel(FinalData, "my_output.xlsx")  # Removed title_mapping
                if funnels:
                    print("\nRaw funnel data:")
                    for title, df in funnels.items():
                        print(f"\n{title}")
                        print(df)
                else:
                    print("No funnel data to display")
                
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
    except Exception as e:
        print(f"Error: An error occurred while reading or parsing the file: {str(e)}")