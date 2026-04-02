#!/usr/bin/env python3
"""
LaTeX Layout Fixer for IUG Documents - FIXED VERSION
Fixes margin overflow issues in IUG_NON_TRANSMISSIBILITY.tex and IUG_SUPPLEMENT.tex
"""

import re
import os
import shutil
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

MAIN_DOC = "IUG_NON_TRANSMISSIBILITY.tex"
SUPPLEMENT = "IUG_SUPPLEMENT.tex"
BACKUP_SUFFIX = ".backup"

# ============================================================================
# FIX FUNCTIONS
# ============================================================================

def fix_weight_vector_inline(content: str) -> str:
    """
    Fix inline weight vector that spills over margin.
    Adds \\allowbreak after commas to enable line breaking.
    """
    # Pattern for the weight vector in inline math - properly escaped
    pattern = r'\$\(w_D,\s*w_T,\s*w_R,\s*w_P,\s*w_F,\s*w_K,\s*w_G,\s*w_\{\\Gamma\},\s*w_\{\\Phi\},\s*w_H,\s*w_S,\s*w_\{\\Omega\}\)\s*=\s*\(1\.0'
    
    replacement = r'''\\begin{multline*}
(w_D,\ w_T,\ w_R,\ w_P,\ w_F,\ w_K,\ w_G,\ w_{\\Gamma},\ w_{\\Phi},\ w_H,\ w_S,\ w_{\\Omega}) \\\\
= (1.0'''
    
    content = re.sub(pattern, replacement, content)
    
    return content


def fix_weight_vector_multline(content: str) -> str:
    """
    Ensure weight vector uses multline environment with proper line break.
    """
    # Check if multline already exists with weight vector
    if 'multline*' in content and 'w_D' in content:
        # Ensure proper line break after the vector
        pattern = r'\(w_D,\\s*w_T,\\s*w_R,\\s*w_P,\\s*w_F,\\s*w_K,\\s*w_G,\\s*w_\{\\Gamma\},\\s*w_\{\\Phi\},\\s*w_H,\\s*w_S,\\s*w_\{\\Omega\}\)\s*\\\\\s*='
        
        replacement = r'(w_D,\ w_T,\ w_R,\ w_P,\ w_F,\ w_K,\ w_G,\ w_{\\Gamma},\ w_{\\Phi},\ w_H,\ w_S,\ w_{\\Omega}) \\\\\n='
        
        content = re.sub(pattern, replacement, content)
    
    return content


def fix_synthon_tuple(content: str) -> str:
    """
    Fix the synthon tuple that spills over margin.
    Wraps in synthonbox or adds manual breaks.
    """
    # Pattern for the long synthon tuple in math mode
    pattern = r'\\\$\\langle D_\\text\{holo\};\\s*T_\\text\{holo\};\\s*R_\\dagger;\\s*P_\\pm\^\\{\\text\{sym\}\};\\s*F_\\text\{eth\};\\s*K_\\text\{mod\};\\s*G_\\aleph;\\s*\\Gamma_\\text\{broad\};\\s*\\Phi_c;\\s*H_1;\\s*n\{:n;\\s*\\Omega_\{Z_2\}\\rangle\\\$'
    
    # Replace with synthonbox environment
    replacement = r'''\\begin{synthonbox}
\\langle D_\\text{holo};\\ T_\\text{holo};\\ R_\\dagger;\\ P_\\pm^\\text{sym};\\ F_\\text{eth};\\ K_\\text{mod};\\ G_\\aleph;\\ \\Gamma_\\text{broad};\\ \\Phi_c;\\ H_1;\\ n{:}n;\\ \\Omega_{Z_2}\\rangle
\\end{synthonbox}'''
    
    content = re.sub(pattern, replacement, content)
    
    # Also handle version without outer $ signs
    pattern2 = r'\\langle D_\\text\{holo\};\\s*T_\\text\{holo\};\\s*R_\\dagger;\\s*P_\\pm\^\\{\\text\{sym\}\};\\s*F_\\text\{eth\};\\s*K_\\text\{mod\};\\s*G_\\aleph;\\s*\\Gamma_\\text\{broad\};\\s*\\Phi_c;\\s*H_1;\\s*n\{:n;\\s*\\Omega_\{Z_2\}\\rangle'
    
    content = re.sub(pattern2, replacement, content)
    
    return content


def fix_table2_supplement(content: str) -> str:
    """
    Fix Table 2 in supplement that spills over margin.
    Converts adjustbox+tabular to tabularx with dynamic column widths.
    """
    # Check if table uses adjustbox
    if 'adjustbox' in content and 'tab:full_tuples' in content:
        # Replace adjustbox wrapper with tabularx
        old_start = r'\\begin\{adjustbox\}\{max width=\\textwidth\}\s*\\begin\{tabular\}'
        new_start = r'\\setlength{\\tabcolsep}{2pt}\n\\begin{tabularx}{\\textwidth}'
        
        content = re.sub(old_start, new_start, content, flags=re.DOTALL)
        
        # Replace end tags
        old_end = r'\\end\{tabular\}\s*\\end\{adjustbox\}'
        new_end = r'\\end{tabularx}'
        
        content = re.sub(old_end, new_end, content, flags=re.DOTALL)
        
        # Update column specification - replace fixed p{} with X columns
        # Find the column spec line and update it
        col_pattern = r'(\\begin\{tabularx\}\{\\textwidth\}\{)([^}]+)(\})'
        
        def replace_cols(match):
            # Keep first column as fixed width, rest as X
            return match.group(1) + '>{\\bfseries\\raggedright\\arraybackslash}p{2.2cm}' + '*{12}{>{\\centering\\arraybackslash}X}' + '>{\\centering\\arraybackslash}p{1.0cm}' + match.group(3)
        
        content = re.sub(col_pattern, replace_cols, content, flags=re.DOTALL)
        
        # Reduce tabcolsep if it exists
        content = re.sub(r'\\setlength\{\\tabcolsep\}\{4pt\}', r'\\setlength{\\tabcolsep}{2pt}', content)
    
    return content


def add_necessary_packages(content: str) -> str:
    """
    Ensure all necessary packages are loaded.
    """
    packages_needed = []
    
    # Check for multline
    if 'multline' in content and 'amsmath' not in content:
        packages_needed.append('amsmath')
    
    # Check for tabularx
    if 'tabularx' in content and 'usepackage{tabularx}' not in content:
        packages_needed.append('tabularx')
    
    # Add missing packages after documentclass
    if packages_needed:
        for pkg in packages_needed:
            if f'\\usepackage{{{pkg}}}' not in content:
                content = re.sub(
                    r'(\\documentclass.*?\n)',
                    rf'\1\\usepackage{{{pkg}}}\n',
                    content
                )
    
    return content


def fix_geometry_margins(content: str) -> str:
    """
    Adjust page margins to give more space.
    """
    # Reduce side margins from 1in to 0.75in
    pattern = r'\\usepackage\[top=1in,\s*bottom=1in,\s*left=1in,\s*right=1in\]\{geometry\}'
    
    if re.search(pattern, content):
        content = re.sub(
            pattern,
            r'\\usepackage[top=1in, bottom=1in, left=0.75in, right=0.75in]{geometry}',
            content
        )
    
    return content


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_file(filepath: str, fixes: list) -> tuple:
    """
    Apply all fixes to a file and return modified content + change log.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    content = original_content
    changes = []
    
    for fix_func, fix_name in fixes:
        try:
            before = content
            content = fix_func(content)
            if content != before:
                changes.append(f"✓ Applied: {fix_name}")
            else:
                changes.append(f"○ Skipped: {fix_name} (no match)")
        except Exception as e:
            changes.append(f"✗ Error: {fix_name} - {str(e)}")
    
    return content, changes


def create_backup(filepath: str) -> str:
    """
    Create a backup of the original file.
    """
    backup_path = filepath + BACKUP_SUFFIX
    shutil.copy2(filepath, backup_path)
    return backup_path


def save_file(filepath: str, content: str) -> None:
    """
    Save modified content to file.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


# ============================================================================
# EXECUTION
# ============================================================================

def main():
    print("=" * 70)
    print("LaTeX Layout Fixer for IUG Documents (FIXED)")
    print("=" * 70)
    print()
    
    files_to_process = [
        (MAIN_DOC, "Main Document"),
        (SUPPLEMENT, "Supplement")
    ]
    
    for filepath, description in files_to_process:
        if not os.path.exists(filepath):
            print(f"⚠ File not found: {filepath}")
            print()
            continue
        
        print(f"Processing: {filepath} ({description})")
        print("-" * 70)
        
        # Create backup
        backup_path = create_backup(filepath)
        print(f"  ✓ Backup created: {backup_path}")
        
        # Define fixes based on file
        if "SUPPLEMENT" in filepath:
            fixes = [
                (fix_weight_vector_inline, "Weight vector line breaks"),
                (fix_weight_vector_multline, "Weight vector multline environment"),
                (fix_table2_supplement, "Table 2 tabularx conversion"),
                (add_necessary_packages, "Package dependencies"),
                (fix_geometry_margins, "Page margin adjustment"),
            ]
        else:
            fixes = [
                (fix_weight_vector_inline, "Weight vector line breaks"),
                (fix_weight_vector_multline, "Weight vector multline environment"),
                (fix_synthon_tuple, "Synthon tuple overflow"),
                (add_necessary_packages, "Package dependencies"),
                (fix_geometry_margins, "Page margin adjustment"),
            ]
        
        # Process file
        modified_content, changes = process_file(filepath, fixes)
        
        # Report changes
        print()
        for change in changes:
            print(f"  {change}")
        
        # Save if modified
        if modified_content != open(filepath, 'r', encoding='utf-8').read():
            save_file(filepath, modified_content)
            print()
            print(f"  ✓ File updated: {filepath}")
        else:
            print()
            print(f"  ○ No changes needed: {filepath}")
        
        print()
    
    print("=" * 70)
    print("Processing complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Compile both documents with pdflatex or latexmk")
    print("  2. Check for any remaining overflow warnings in the log")
    print("  3. If issues persist, manually adjust tabcolsep or font size")
    print()
    print("To restore originals, rename .backup files back to original names.")
    print()


if __name__ == "__main__":
    main()