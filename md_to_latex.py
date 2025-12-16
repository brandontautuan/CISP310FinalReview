#!/usr/bin/env python3
"""
Convert Markdown files to LaTeX format.
"""

import re
import sys
import os
from pathlib import Path


def escape_latex(text):
    """Escape special LaTeX characters."""
    special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    for char, escaped in special_chars.items():
        text = text.replace(char, escaped)
    return text


def convert_header(line):
    """Convert markdown headers to LaTeX sections."""
    match = re.match(r'^(#{1,6})\s+(.+)$', line)
    if not match:
        return None
    
    level = len(match.group(1))
    text = escape_latex(match.group(2))
    
    commands = {
        1: r'\section',
        2: r'\subsection',
        3: r'\subsubsection',
        4: r'\paragraph',
        5: r'\subparagraph',
        6: r'\subparagraph',
    }
    
    return f"{commands[level]}{{{text}}}"


def convert_code_block(lines, start_idx):
    """Convert a code block to LaTeX verbatim environment."""
    # Find the closing ```
    end_idx = start_idx + 1
    while end_idx < len(lines) and not lines[end_idx].strip().startswith('```'):
        end_idx += 1
    
    code_lines = lines[start_idx+1:end_idx]
    
    # Check if there's a language specified
    first_line = lines[start_idx].strip()
    language = first_line[3:].strip() if len(first_line) > 3 else ''
    
    # Use different environments based on language
    if language.lower() in ['assembly', 'asm', 'c', 'cpp', 'java', 'python', 'javascript']:
        env = 'lstlisting'
        lang_map = {
            'assembly': '[language={[x86masm]Assembler}, commentstyle=\\color{gray}\\itshape]',
            'asm': '[language={[x86masm]Assembler}, commentstyle=\\color{gray}\\itshape]',
            'c': '[language=C, commentstyle=\\color{gray}\\itshape]',
            'cpp': '[language=C++, commentstyle=\\color{gray}\\itshape]',
            'java': '[language=Java, commentstyle=\\color{gray}\\itshape]',
            'python': '[language=Python, commentstyle=\\color{gray}\\itshape]',
            'javascript': '[language=JavaScript, commentstyle=\\color{gray}\\itshape]',
        }
        options = lang_map.get(language.lower(), '[commentstyle=\\color{gray}\\itshape]')
        result = [f'\\begin{{lstlisting}}{options}']
        result.extend(code_lines)
        result.append('\\end{lstlisting}')
        return result, end_idx + 1
    else:
        # Use verbatim for other languages or no language specified - preserves ALL content including comments
        result = ['\\begin{verbatim}']
        result.extend(code_lines)
        result.append('\\end{verbatim}')
        return result, end_idx + 1


def convert_inline_code(text):
    """Convert inline code to LaTeX."""
    return re.sub(r'`([^`]+)`', r'\\texttt{\1}', text)


def convert_bold(text):
    """Convert bold text to LaTeX."""
    return re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', text)


def convert_italic(text):
    """Convert italic text to LaTeX."""
    # Handle *text* but not **text**
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\\textit{\1}', text)
    # Handle _text_ but not __text__
    text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'\\textit{\1}', text)
    return text


def convert_list_item(line):
    """Convert markdown list items to LaTeX."""
    # Ordered list
    match = re.match(r'^(\d+)\.\s+(.+)$', line)
    if match:
        text = convert_inline_formatting(match.group(2))
        return f"\\item {text}"
    
    # Unordered list
    match = re.match(r'^[-*+]\s+(.+)$', line)
    if match:
        text = convert_inline_formatting(match.group(1))
        return f"\\item {text}"
    
    return None


def convert_inline_formatting(text):
    """Apply all inline formatting conversions."""
    text = convert_inline_code(text)
    text = convert_bold(text)
    text = convert_italic(text)
    return text


def convert_table(lines, start_idx):
    """Convert markdown table to LaTeX table."""
    # Read table lines
    table_lines = []
    idx = start_idx
    while idx < len(lines) and '|' in lines[idx]:
        table_lines.append(lines[idx])
        idx += 1
    
    if len(table_lines) < 2:
        return None, start_idx
    
    # Parse header
    header = table_lines[0]
    separator = table_lines[1]  # |---|---|
    
    # Extract columns
    header_cols = [col.strip() for col in header.split('|')[1:-1]]
    num_cols = len(header_cols)
    
    # Build LaTeX table
    result = ['\\begin{table}[h]', '\\centering', '\\begin{tabular}{' + '|' + 'l' * num_cols + '|}', '\\hline']
    
    # Header row
    header_latex = ' & '.join(escape_latex(col) for col in header_cols)
    result.append(header_latex + ' \\\\')
    result.append('\\hline')
    
    # Data rows
    for row_line in table_lines[2:]:
        row_cols = [col.strip() for col in row_line.split('|')[1:-1]]
        row_latex = ' & '.join(escape_latex(col) for col in row_cols[:num_cols])
        result.append(row_latex + ' \\\\')
        result.append('\\hline')
    
    result.append('\\end{tabular}')
    result.append('\\end{table}')
    
    return result, idx


def convert_horizontal_rule(line):
    """Convert horizontal rule to LaTeX."""
    if re.match(r'^---+\s*$', line) or re.match(r'^\*\*\*+\s*$', line):
        return '\\hrule'
    return None


def convert_link(text):
    """Convert markdown links to LaTeX."""
    # [text](url)
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        return f'\\href{{{url}}}{{{escape_latex(link_text)}}}'
    
    return re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', replace_link, text)


def markdown_to_latex(md_content):
    """Convert markdown content to LaTeX."""
    lines = md_content.split('\n')
    latex_lines = []
    i = 0
    
    in_list = False
    list_type = None  # 'ordered' or 'unordered'
    
    while i < len(lines):
        line = lines[i]
        original_line = line
        
        # Check for code block
        if line.strip().startswith('```'):
            if in_list:
                if list_type == 'ordered':
                    latex_lines.append('\\end{enumerate}')
                else:
                    latex_lines.append('\\end{itemize}')
                in_list = False
            
            code_block, i = convert_code_block(lines, i)
            latex_lines.extend(code_block)
            continue
        
        # Check for horizontal rule
        hr = convert_horizontal_rule(line)
        if hr:
            if in_list:
                if list_type == 'ordered':
                    latex_lines.append('\\end{enumerate}')
                else:
                    latex_lines.append('\\end{itemize}')
                in_list = False
            latex_lines.append(hr)
            i += 1
            continue
        
        # Check for table
        if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1] and '---' in lines[i + 1]:
            if in_list:
                if list_type == 'ordered':
                    latex_lines.append('\\end{enumerate}')
                else:
                    latex_lines.append('\\end{itemize}')
                in_list = False
            
            table_lines, i = convert_table(lines, i)
            if table_lines:
                latex_lines.extend(table_lines)
            continue
        
        # Check for header
        header = convert_header(line)
        if header:
            if in_list:
                if list_type == 'ordered':
                    latex_lines.append('\\end{enumerate}')
                else:
                    latex_lines.append('\\end{itemize}')
                in_list = False
            latex_lines.append(header)
            i += 1
            continue
        
        # Check for list item
        list_item = convert_list_item(line)
        if list_item:
            # Determine list type
            is_ordered = bool(re.match(r'^\d+\.\s+', line))
            current_list_type = 'ordered' if is_ordered else 'unordered'
            
            if not in_list:
                if is_ordered:
                    latex_lines.append('\\begin{enumerate}')
                else:
                    latex_lines.append('\\begin{itemize}')
                in_list = True
                list_type = current_list_type
            elif list_type != current_list_type:
                # Close previous list and start new one
                if list_type == 'ordered':
                    latex_lines.append('\\end{enumerate}')
                else:
                    latex_lines.append('\\end{itemize}')
                if is_ordered:
                    latex_lines.append('\\begin{enumerate}')
                else:
                    latex_lines.append('\\begin{itemize}')
                list_type = current_list_type
            
            latex_lines.append(list_item)
            i += 1
            continue
        else:
            # Not a list item, close list if open
            if in_list:
                if list_type == 'ordered':
                    latex_lines.append('\\end{enumerate}')
                else:
                    latex_lines.append('\\end{itemize}')
                in_list = False
        
        # Regular paragraph line
        if line.strip():
            formatted = convert_inline_formatting(line)
            formatted = convert_link(formatted)
            latex_lines.append(formatted)
        else:
            # Empty line
            latex_lines.append('')
        
        i += 1
    
    # Close any open list
    if in_list:
        if list_type == 'ordered':
            latex_lines.append('\\end{enumerate}')
        else:
            latex_lines.append('\\end{itemize}')
    
    return '\n'.join(latex_lines)


def create_full_latex_document(latex_body, title="Document"):
    """Create a complete LaTeX document with preamble."""
    preamble = f"""\\documentclass[9pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{geometry}}
\\geometry{{a4paper, margin=0.4in, top=0.3in, bottom=0.3in}}
\\usepackage{{listings}}
\\usepackage{{xcolor}}
\\usepackage{{hyperref}}
\\usepackage{{booktabs}}
\\usepackage{{longtable}}
\\usepackage{{enumitem}}
\\usepackage{{titlesec}}
\\usepackage{{parskip}}
\\usepackage{{fancyhdr}}

% Remove header/footer spacing
\\pagestyle{{plain}}
\\setlength{{\\headheight}}{{0pt}}
\\setlength{{\\headsep}}{{0pt}}
\\setlength{{\\footskip}}{{10pt}}

% Compact spacing for sections
\\titlespacing*{{\\section}}{{0pt}}{{3pt}}{{1pt}}
\\titlespacing*{{\\subsection}}{{0pt}}{{2pt}}{{0.5pt}}
\\titlespacing*{{\\subsubsection}}{{0pt}}{{1.5pt}}{{0pt}}
\\titlespacing*{{\\paragraph}}{{0pt}}{{0.5pt}}{{0pt}}

% Compact lists
\\setlist{{nosep, leftmargin=12pt, itemsep=0pt, parsep=0pt, topsep=1pt, partopsep=0pt}}
\\setenumerate{{nosep, leftmargin=12pt, itemsep=0pt, parsep=0pt, topsep=1pt}}
\\setitemize{{nosep, leftmargin=12pt, itemsep=0pt, parsep=0pt, topsep=1pt}}

% Reduce paragraph spacing
\\setlength{{\\parskip}}{{1pt}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\baselineskip}}{{10pt}}

% Compact code listings - preserves ALL comments
\\lstset{{
    basicstyle=\\ttfamily\\scriptsize,
    breaklines=true,
    frame=single,
    framesep=2pt,
    numbers=left,
    numbersep=3pt,
    numberstyle=\\tiny\\color{{gray}},
    xleftmargin=5pt,
    xrightmargin=5pt,
    aboveskip=2pt,
    belowskip=2pt,
    showstringspaces=false,
    keepspaces=true,
    tabsize=2,
    commentstyle=\\color{{gray!70}}\\itshape,
    keywordstyle=\\color{{blue}}\\bfseries,
    stringstyle=\\color{{red!70}},
    escapeinside={{@*}}{{*@}},
}}

\\title{{{escape_latex(title)}}}
\\author{{}}
\\date{{}}

\\begin{{document}}

\\maketitle
\\vspace{{-10pt}}

"""
    
    ending = """
\\end{document}
"""
    
    return preamble + latex_body + ending


def convert_file(md_file, output_dir=None, standalone=True):
    """Convert a markdown file to LaTeX."""
    md_path = Path(md_file)
    
    if not md_path.exists():
        print(f"Error: File {md_file} not found.")
        return
    
    print(f"Converting {md_file}...")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    latex_body = markdown_to_latex(md_content)
    
    if standalone:
        title = md_path.stem.replace('_', ' ').title()
        latex_content = create_full_latex_document(latex_body, title)
    else:
        latex_content = latex_body
    
    if output_dir:
        output_path = Path(output_dir) / f"{md_path.stem}.tex"
    else:
        output_path = md_path.parent / f"{md_path.stem}.tex"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    print(f"  -> {output_path}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        # Convert all .md files in current directory
        md_files = list(Path('.').glob('*.md'))
        if not md_files:
            print("No markdown files found in current directory.")
            print("\nUsage:")
            print("  python md_to_latex.py <file1.md> [file2.md ...]")
            print("  python md_to_latex.py  # converts all .md files in current directory")
            return
        
        print(f"Found {len(md_files)} markdown file(s) to convert.")
        for md_file in md_files:
            convert_file(md_file)
    else:
        # Convert specified files
        for md_file in sys.argv[1:]:
            convert_file(md_file)
    
    print("\nConversion complete!")
    print("\nNote: You may need to compile the .tex files with pdflatex or xelatex.")
    print("For code listings, you may need to adjust the language settings in the preamble.")


if __name__ == '__main__':
    main()

