import os
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.parent
RELEASES_DIR = BASE_DIR / 'data' / 'releases'
SUMMARIES_DIR = BASE_DIR / 'data' / 'summaries'

def parse_release_file(file_path):
    """
    Parses a release markdown file and returns a list of release dictionaries.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract repo name from filename (e.g., owner_repo_1.md -> owner/repo)
    filename = file_path.name
    match = re.match(r'(.+?)_(.+?)_\d+\.md', filename)
    if match:
        owner, repo_part = match.groups()
        repo_name = f"{owner}/{repo_part}"
    else:
        repo_name = filename.replace('.md', '')

    releases = []
    
    # Split by the separator
    parts = content.split('\n---\n')
    
    for part in parts:
        # Regex to extract details
        tag_match = re.search(r'- \*\*Tag\*\*: (.*)', part)
        date_match = re.search(r'- \*\*Published At\*\*: (\d{4}-\d{2}-\d{2})', part)
        
        if tag_match and date_match:
            tag = tag_match.group(1).strip()
            date_str = date_match.group(1).strip()
            
            # Extract notes: content after ### Notes
            notes_parts = part.split('### Notes')
            notes = notes_parts[1].strip() if len(notes_parts) > 1 else ""
            
            releases.append({
                'repo_name': repo_name,
                'tag': tag,
                'date': date_str,
                'notes': notes
            })
            
    return releases

def generate_monthly_summaries():
    """
    Aggregates releases by month and writes summary files.
    """
    if not RELEASES_DIR.exists():
        print(f"Directory not found: {RELEASES_DIR}")
        return

    os.makedirs(SUMMARIES_DIR, exist_ok=True)
    
    monthly_data = defaultdict(lambda: defaultdict(list))
    
    files = list(RELEASES_DIR.glob('*.md'))
    print(f"Found {len(files)} files to process.")

    for file_path in files:
        try:
            releases = parse_release_file(file_path)
            for release in releases:
                date_obj = datetime.strptime(release['date'], '%Y-%m-%d')
                month_key = date_obj.strftime('%Y-%m')
                monthly_data[month_key][release['repo_name']].append(release)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    # Generate summary files
    for month, repos in monthly_data.items():
        summary_content = f"# {month} AI SDK Updates Summary\n\n"
        
        sorted_repos = sorted(repos.keys())
        for repo in sorted_repos:
            repo_releases = repos[repo]
            # Sort releases by date descending
            repo_releases.sort(key=lambda x: x['date'], reverse=True)
            
            summary_content += f"## {repo}\n\n"
            for rel in repo_releases:
                summary_content += f"### {rel['tag']} ({rel['date']})\n\n"
                summary_content += f"{rel['notes']}\n\n"
            summary_content += "---\n\n"
        
        output_file = SUMMARIES_DIR / f"summary_{month}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"Generated summary for {month}: {output_file}")

if __name__ == "__main__":
    generate_monthly_summaries()

