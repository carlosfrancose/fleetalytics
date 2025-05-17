import os
import json
from pathlib import Path
import argparse
import re

def preview_large_json(file_path, max_bytes=10000):
    """
    Reads the first max_bytes of a JSON file and tries to analyze its structure.
    """
    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Read the first chunk of the file for preview
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            preview_data = f.read(max_bytes)
        
        # Try to understand the structure using our custom analyzer
        structure_info = analyze_json_structure(file_path)
        
        return {
            'preview': preview_data,
            'structure': structure_info,
            'file_size': file_size
        }
    except Exception as e:
        return {
            'preview': f"Error reading file: {str(e)}",
            'structure': "Error",
            'file_size': 0
        }

def analyze_json_structure(file_path, max_items=5):
    """
    Analyzes a JSON file structure using manual parsing to handle non-standard JSON values like NaN.
    Returns a description of the structure.
    """
    try:
        # First attempt: basic structure detection without detailed parsing
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first few bytes to determine the basic structure
            start_content = f.read(1024)
            
            # Clean content by replacing NaN with null
            clean_content = start_content.replace('NaN', 'null')
            
            # Try to determine root structure
            if clean_content.strip().startswith('{'):
                structure_type = "JSON object"
                
                # Try to extract some top-level keys
                import re
                # Find patterns like "key": at the beginning of the JSON object
                keys = re.findall(r'"([^"]+)"(?=\s*:)', clean_content[:1000])
                
                if keys:
                    # Get just the first few unique keys
                    unique_keys = []
                    for key in keys:
                        if key not in unique_keys and len(unique_keys) < max_items:
                            unique_keys.append(key)
                    
                    return f"JSON object with keys including: {', '.join(unique_keys)}"
                else:
                    return "JSON object (dictionary)"
                    
            elif clean_content.strip().startswith('['):
                return "JSON array (list)"
            else:
                return "Unknown JSON structure"
    
    except Exception as e:
        # If the basic approach fails, try a more robust method
        try:
            # Read a larger chunk and replace NaN with null to make it valid JSON
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10240)  # Read first 10KB
                clean_content = content.replace('NaN', 'null')
                
                # Try to parse a small portion of the cleaned content
                if clean_content.strip().startswith('{'):
                    # Find the first complete JSON object
                    bracket_count = 0
                    end_pos = 0
                    
                    for i, char in enumerate(clean_content):
                        if char == '{':
                            bracket_count += 1
                        elif char == '}':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_pos = i + 1
                                break
                    
                    if end_pos > 0:
                        # Try to parse the first complete object
                        first_obj = json.loads(clean_content[:end_pos])
                        keys = list(first_obj.keys())[:max_items]
                        return f"JSON object with keys including: {', '.join(keys)}"
                
                return "JSON structure detected, but details could not be parsed"
                
        except Exception as nested_e:
            # If all else fails, return a simplified structure analysis
            try:
                with open(file_path, 'rb') as f:
                    first_char = f.read(1).decode('utf-8', errors='ignore')
                    if first_char == '{':
                        return "JSON object (dictionary) with NaN values"
                    elif first_char == '[':
                        return "JSON array (list) with NaN values"
                    else:
                        return "Unknown JSON structure with possible NaN values"
            except:
                return f"Could not analyze structure: {str(e)}"

def find_json_files(base_dir):
    """
    Recursively finds all JSON files in the given directory.
    """
    json_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files

def format_file_size(size_in_bytes):
    """Format file size in a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024 or unit == 'GB':
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Preview JSON files in a directory structure')
    parser.add_argument('--dir', type=str, default="almrrc2021", 
                        help='Base directory containing the JSON files')
    parser.add_argument('--output', type=str, default="json_previews.txt",
                        help='Output file to write previews to')
    parser.add_argument('--size', type=int, default=10240,
                        help='Number of bytes to preview from each file')
    args = parser.parse_args()
    
    # Find all JSON files
    json_files = find_json_files(args.dir)
    print(f"Found {len(json_files)} JSON files")
    
    # Create the preview file
    with open(args.output, 'w', encoding='utf-8') as out_f:
        out_f.write(f"JSON FILE PREVIEWS\n")
        out_f.write(f"Generated preview of {len(json_files)} JSON files\n\n")
        
        for file_path in json_files:
            # Get relative path for cleaner output
            rel_path = os.path.relpath(file_path, start=os.path.dirname(args.dir))
            
            # Get preview info
            preview_info = preview_large_json(file_path, args.size)
            
            # Write file header
            out_f.write(f"\n{'=' * 80}\n")
            out_f.write(f"FILE: {rel_path}\n")
            out_f.write(f"SIZE: {format_file_size(preview_info['file_size'])}\n")
            out_f.write(f"{'=' * 80}\n\n")
            
            # Write structure info
            out_f.write(f"STRUCTURE: {preview_info['structure']}\n\n")
            
            # Write preview
            out_f.write("PREVIEW:\n")
            out_f.write(preview_info['preview'])
            out_f.write("\n\n")
            
            print(f"Processed: {rel_path} ({format_file_size(preview_info['file_size'])})")
    
    print(f"Preview file created: {args.output}")

if __name__ == "__main__":
    main()